#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url

from iabe import admin, views

urlpatterns = [
    url('index/', view=views.index, name='index'),
    url('^login$', view=admin.Auth.as_view(), name='login'),
    url('^logout$', view=admin.Auth.logout, name='logout'),

    url('adduser', view=views.UserManage.as_view(), name='adduser'),
    url('^pools', view=views.task.show_tasks, name='task_pool'),
    url('add_pool/(?P<account>\w{2}\d{7,8})', view=views.task.add_task, name='add_pool'),
    url('api/(?P<action>logs|note|progress|pwd|xue|exchange)/(?P<account>\w{2}\d{7,8})',
        view=views.api.view),
]
