#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# from Crypto.Cipher import AES
"""

from threading import Thread
from django.contrib.auth.decorators import login_required
from django.contrib.auth import mixins
from django.views import View
from django.forms.models import model_to_dict
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from iabe.api.src import MixClient
from iabe.api.src.WebBase import Cache
from iabe.models import Log, User

pools = []
action_map = [
    ("cw1", MixClient.PARAM_CGW_1),
    ("cw4", MixClient.PARAM_CGW_4),
    ("mn1", MixClient.PARAM_MONI_1),
    ("mn4", MixClient.PARAM_MONI_4),
]


class Tasks(mixins.LoginRequiredMixin, View):
    @staticmethod
    def show_tasks(request):
        return JsonResponse(dict(msg=repr(pools)))

    def get(self, request, account):
        action = request.GET.get("action")

        if action.startswith("cw"):
            self.call_cgw(account, var=dict(action_map)[action])
        elif action.startswith("mn"):
            self.call_moni(account, var=dict(action_map)[action])
        else:
            return JsonResponse(dict(msg=501))

        return JsonResponse(dict(msg=account))

    @staticmethod
    def call_cgw(account, *args, **kwargs):
        o = Tasks._init_account(account)
        if o:
            p = Thread(target=o.call_cgw, args=args, kwargs=kwargs)
            pools.append(p)
            p.setDaemon(True)
            p.start()

    @staticmethod
    def call_moni(account, *args, **kwargs):
        o = Tasks._init_account(account)
        if o:
            p = Thread(target=o.call_moni, args=args, kwargs=kwargs)
            pools.append(p)
            p.setDaemon(True)
            p.start()

    @staticmethod
    def _init_account(account):
        query = User.objects.filter(username=account).first()
        if query:
            return MixClient.init_from_dict(model_to_dict(query))

        return None

    @staticmethod
    def create_account(request,
                       username,
                       password,
                       area,
                       beizhu):
        region_choices = dict(User.REGION_CHOICES)

        o = MixClient(username=username, password=password, zone=area)

        if password in [1234, "1234"]:
            if o._change_pwd_v1("123456"):
                password = "123456"
                Cache.pop(username)

        sn = o.get_hao

        user_obj = dict(
            sn=sn,
            username=username,
            password=password,
            region=region_choices[area.upper()],
            creator_id=request.user.id,
            note=beizhu,
            is_finish=False,
        )

        User.objects.create(**user_obj)


class UserManage(mixins.LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "UserManage.html")

    def post(self, request):
        area_prefix = request.POST.get("area-prefix")
        area = request.POST.get("area")
        username = request.POST.get("username")
        password = request.POST.get("password")
        beizhu = request.POST.get("beizhu")

        o_lst = []
        region_choices = dict(User.REGION_CHOICES)

        if isinstance(username, list):
            username = username[0]
        username = username.split(",")
        username = [i for i in username if i]
        for user in username:
            if area_prefix != "无":
                user = "{}{}".format(area_prefix, user.strip())

            q = User.objects.filter(username=user)
            if not q:
                p = Thread(name="create_account",
                           target=Tasks.create_account,
                           kwargs=dict(
                               request=request,
                               username=user,
                               password=password,
                               area=area,
                               beizhu=beizhu,
                           ))
                pools.append(p)
                p.start()

            else:
                user_obj = dict(
                    username=username,
                    password=password,
                    region=region_choices[area.upper()],
                    note=beizhu,
                    is_finish=False,
                )
                q.update(**user_obj)

            # o_lst.append(user_obj)
        # User.objects.bulk_create(o_lst)
        # User.objects.update_or_create(o_lst)

        return HttpResponseRedirect('/iabe/index/')


@login_required
def index(request):
    page_size = 30
    page = request.POST.get("page", 1)
    s1, s2 = (page - 1) * page_size, page * page_size

    query_user = User.objects.filter(is_finish=False).order_by('updated_at').all()[s1:s2]
    context = dict(accounts=query_user, page=page, current_user=request.user)
    return render(request, "index.html", context=context)


class Api(mixins.LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        action_map = [
            ("exchange", self.get_exchange),
            ("logs", self.get_log),
            ("note", self.get_note),
            ("progress", self.get_progress),
            ("pwd", self.get_pwd),
            ("xue", self.get_xue),
            ("finish", self.make_finish),
        ]

        action = kwargs.get("action")
        self.account = kwargs.get("account")
        self._init_account()

        if self.account.find(",") >= 0:
            self.account = [i.strip() for i in self.account.split(",")]

        if dict(action_map).get(action):
            resp = dict(action_map)[action](request=request)
            if resp:
                return resp

        return HttpResponseNotFound(403)

    def get_log(self, request, **kwargs):
        assert isinstance(self.account, (str, bytes))

        lv = 0
        if request.GET.get("lv"):
            lv = getattr(Log, "%s_%s" % ("LOG", request.GET["lv"].upper()))

        query = Log.objects.filter(name="log_" + self.account)
        if lv:
            query = query.filter(lv__gte=lv)

        query = query.order_by("-created_at").all()[:20][::-1]
        if query:
            return JsonResponse([model_to_dict(o, exclude=["id"]) for o in query], safe=False)

    def get_note(self, **kwargs):
        obj = getattr(self, "obj")
        query = obj.meta["note"]

        return JsonResponse({"msg": query})

    def get_progress(self, **kwargs):
        obj = getattr(self, "obj")
        obj.login()

        query = obj.get_total_stage()
        if query:
            return JsonResponse(query)

    def get_pwd(self, **kwargs):
        obj = getattr(self, "obj")
        query = obj.meta["password"]
        return JsonResponse({"msg": query})

    def get_xue(self, **kwargs):
        obj = getattr(self, "obj")
        obj.login()

        query = obj.get_today_learn()
        if query:
            return JsonResponse(query)

    def get_exchange(self, request, **kwargs):
        obj = getattr(self, "obj")
        action = request.GET.get("action")

        result = obj.call_exchange(dict(action_map)[action])
        return JsonResponse({"msg": result})

    def make_finish(self, **kwargs):
        __lst__ = self.account
        if isinstance(__lst__, str):
            __lst__ = [self.account]

        obj = User.objects.filter(username__in=__lst__)
        obj.update(is_finish=True)

        return JsonResponse({"msg": True})

    def _init_account(self):
        query = User.objects.filter(username=self.account).first()
        if query:
            setattr(self, "obj", MixClient(zone=query.region, **model_to_dict(query)))

