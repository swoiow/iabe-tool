#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from Crypto.Cipher import AES

from threading import Thread

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.forms.models import model_to_dict
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from iabe.api.Core import ClientWebApi, ClientWebService, iClient
from iabe.models import Log, User


def HexToByte(hexStr):
    bytes = []

    hexStr = ''.join(hexStr.split(" "))

    for i in range(0, len(hexStr), 2):
        bytes.append(chr(int(hexStr[i:i + 2], 16)))

    return ''.join(bytes)


pools = []
action_map = [
    ("cw1", ClientWebApi.PARAM_CGW_1),
    ("cw4", ClientWebApi.PARAM_CGW_4),
    ("mn1", ClientWebApi.PARAM_MONI_1),
    ("mn4", ClientWebApi.PARAM_MONI_4),
]


class Tasks:
    @staticmethod
    def show_tasks(request):
        return JsonResponse(dict(msg=repr(pools)))

    def add_task(self, request, account):
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
            query.zone = account[:2]
            return iClient.from_orm(query)

        return None


class UserManage(LoginView):
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

        username = username.split("\n")
        if area_prefix != "无":
            username = ["{}{}".format(area_prefix, user) for user in username]

        for user in username:
            user = user.strip()
            o = ClientWebService.from_simple(user, password, zone=area)
            sn = o.get_hao()

            user_obj = User(
                sn=sn,
                username=user,
                password=password,
                region=region_choices[area.upper()],
                creator_id=request.user.id,
                note=beizhu,
            )
            o_lst.append(user_obj)

        User.objects.bulk_create(o_lst)

        return HttpResponseRedirect('/iabe/index/')


@login_required
def index(request):
    page_size = 10
    page = request.POST.get("page", 1)
    s1, s2 = (page - 1) * page_size, page * page_size

    query_user = User.objects.order_by('updated_at').all()[s1:s2]
    context = dict(accounts=query_user, page=page, current_user=request.user)
    return render(request, "index.html", context=context)


class Api(LoginView):
    def view(self, request, *args, **kwargs):
        action_map = [
            ("exchange", self.get_exchange),
            ("logs", self.get_log),
            ("note", self.get_note),
            ("progress", self.get_progress),
            ("pwd", self.get_pwd),
            ("xue", self.get_xue),
        ]

        action = kwargs.get("action")
        self.account = kwargs.get("account")
        self._init_account()

        if dict(action_map).get(action):
            resp = dict(action_map)[action](request=request)
            if resp:
                return resp

        return HttpResponseNotFound(403)

    def get_log(self, request, **kwargs):
        lv = 0
        if request.GET.get("lv"):
            lv = getattr(Log, "%s_%s" % ("LOG", request.GET["lv"].upper()))

        query = Log.objects.filter(name="log_" + self.account)
        if lv:
            query = query.filter(lv__gte=lv)

        query = query.order_by("-created_at").all()[:20][::-1]
        if query:
            return JsonResponse([model_to_dict(o, exclude=["id"]) for o in query], safe=False)

    def get_note(self, request, **kwargs):
        obj = getattr(self, "obj")
        query = obj.meta["note"]

        return JsonResponse({"msg": query})

    def get_progress(self, request, **kwargs):
        obj = getattr(self, "obj")

        query = obj.call_learn_progress_v2()
        if query:
            return JsonResponse(query)

    def get_pwd(self, request, **kwargs):
        obj = getattr(self, "obj")
        query = obj.meta["password"]
        return JsonResponse({"msg": query})

    def get_xue(self, request, **kwargs):
        obj = getattr(self, "obj")

        query = obj.get_xueshi()
        if query:
            return JsonResponse(query)

    def get_exchange(self, request, **kwargs):
        obj = getattr(self, "obj")
        action = request.GET.get("action")

        result = obj.call_exchange(dict(action_map)[action])
        return JsonResponse({"msg": result})

    def _init_account(self):
        query = User.objects.filter(username=self.account).first()
        if query:
            query.zone = self.account[:2]
            setattr(self, "obj", iClient.from_orm(query))


api = Api()
task = Tasks()
