#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url

from iabe import admin, views

app_name = 'iabe'
urlpatterns = [
    url('index/', view=views.index, name='index'),
    url('^login$', view=admin.Auth.as_view(), name='login'),
    url('^logout$', view=admin.Auth.logout, name='logout'),

    url('^adduser$', view=views.UserManage.as_view(), name='adduser'),
    url('^pools', view=views.Tasks.show_tasks, name='task_pool'),
    url('add_pool/(?P<account>\w{2}\d{7,8})', view=views.Tasks.as_view(), name='add_pool'),
    url('api/(?P<action>finish|logs|note|progress|pwd|xue|exchange)/(?P<account>\w{2}\d{7,8})',
        view=views.Api.as_view()),
    url('rest/(?P<action>finish)/(?P<account>[\w,\d]+)',
        view=views.Api.as_view()),
]
