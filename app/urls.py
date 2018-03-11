#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import include, path
from django.views.static import serve
from django.contrib import admin as django_admin

from iabe import admin, views

urlpatterns = [
    url("^$", view=views.index),
    url('^accounts/login/$', admin.Auth.as_view(), name="login"),
    url('^accounts/logout/$', admin.Auth.logout, name="logout"),

    path('iabe/', include("iabe.urls")),
]

if hasattr(settings, "ADMIN_PROTECT"):
    url_code = settings.ADMIN_PROTECT
    urlpatterns += [path('%s/admin/' % url_code, django_admin.site.urls)]
else:
    urlpatterns += [path('admin/', django_admin.site.urls)]

"""
http://blog.csdn.net/dong_W_/article/details/78767573
"""
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [url(r'^static/(?P<path>.*)$', serve, dict(document_root=settings.STATIC_ROOT))]
