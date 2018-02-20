#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin as django_admin
from django.urls import include, path
from django.views.static import serve
from iabe import admin, views

urlpatterns = [
    url("^$", view=views.index),
    url('^accounts/login/$', admin.Auth.as_view(), name="login"),
    url('^accounts/logout/$', admin.Auth.logout, name="logout"),

    path('admin/', django_admin.site.urls),
    path('iabe/', include("iabe.urls")),
]

"""
http://blog.csdn.net/dong_W_/article/details/78767573
"""
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [url(r'^static/(?P<path>.*)$', serve, dict(document_root=settings.STATIC_ROOT))]
