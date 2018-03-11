from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View


class Auth(View):
    def get(self, request, *args, **kwargs):
        next_page = request.GET.get("next", '/iabe/index/')
        if request.user.is_authenticated:
            return HttpResponseRedirect(next_page)
        else:
            return render(request, "login.html")

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")

        # ts = request.POST.get("_")
        # tk = request.META['CSRF_COOKIE']

        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect(request.GET.get("next", '/iabe/index/'))
        else:
            ctx = dict()
            ctx["err_msg"] = "用户名不存在或密码错误"
            return render(request, "login.html", context=ctx)

    @staticmethod
    def logout(request, *args, **kwargs):
        auth.logout(request)
        return HttpResponseRedirect('/iabe/index/')
