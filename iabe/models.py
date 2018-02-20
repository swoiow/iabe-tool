#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class User(models.Model):
    REGION_CZ = "CZ"
    REGION_FS = "FS"
    REGION_JM = "JM"
    REGION_SG = "SG"
    REGION_YL = "YL"

    REGION_CHOICES = [
        (REGION_CZ, "沧州"),
        (REGION_FS, "佛山"),
        (REGION_JM, "江门"),
        (REGION_SG, "韶关"),
        (REGION_YL, "玉林"),
    ]

    sn = models.IntegerField(verbose_name="流水号")
    username = models.CharField(verbose_name="账户名",
                                max_length=12)
    password = models.CharField(verbose_name="账户密码",
                                max_length=255,
                                default="1234")
    region = models.CharField(verbose_name="所属地区",
                              max_length=8,
                              choices=REGION_CHOICES)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.DO_NOTHING)
    is_finish = models.BooleanField(verbose_name="是否完成",
                                    default=False)
    note = models.TextField(verbose_name="备注",
                            max_length=255)

    updated_at = models.DateTimeField(verbose_name="更新时间",
                                      db_index=True, auto_now=True)
    created_at = models.DateTimeField(verbose_name="添加时间",
                                      auto_now_add=True)


class Face(models.Model):
    MASTER = 1
    SLAVE = 0

    TYPE_CHOICES = [
        (MASTER, "主"),
        (SLAVE, "从"),
    ]

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    path = models.CharField(verbose_name="图片路径",
                            max_length=255)
    hash = models.CharField(verbose_name="图片MD5",
                            max_length=32)
    type = models.IntegerField(verbose_name="所属地区",
                               choices=TYPE_CHOICES)
    is_use = models.BooleanField(verbose_name="是否使用",
                                 default=False)
    created_at = models.DateTimeField(verbose_name="添加时间",
                                      auto_now_add=True)


class Log(models.Model):
    LOG_DEBUG = 1
    LOG_INFO = 2
    LOG_WARNING = 3
    LOG_ERROR = 4

    # LOG_CHOICES = [
    #     (LOG_DEBUG, "DEBUG"),
    #     (LOG_INFO, "INFO"),
    #     (LOG_WARNING, "WARNING"),
    #     (LOG_ERROR, "ERROR"),
    # ]

    name = models.CharField(verbose_name="账户名",
                            max_length=12)
    lv = models.IntegerField(verbose_name="日志等级")  # , choices=LOG_CHOICES)
    content = models.TextField(verbose_name="日志内容")
    created_at = models.FloatField(verbose_name="添加时间")
