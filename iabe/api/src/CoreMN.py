#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import random
import time

import bs4
import requests

from .WebBase import ClientWebBase


class MNApi(ClientWebBase):
    PARAM_MONI_1 = 1
    PARAM_MONI_4 = 4

    PARAM_MAP = [
        (PARAM_MONI_1, 2),
        (PARAM_MONI_4, 9),
    ]

    def __init__(self, username, password, *args, **kwargs):
        super(MNApi, self).__init__(username=username, password=password, *args, **kwargs)

    def call_moni(self, var, retry=3):
        # assert var in [2, 9]
        __msg_ = u" 准备执行'(v2)模拟任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if retry < 0:
            self.logger.error(u"[!!!] 超出重试限制。")
            return
        else:
            self.login()

            try:
                result = self._call_moni_v2(dict(self.PARAM_MAP)[var])
                if result:
                    self.logger.info(u"已完成一套！10秒后自动退出...\n\n")
                    time.sleep(10)
                    return dict(result=True) if result == "1" else dict(result=result)
                else:
                    self.logger.warning(u"[!!] 返回结果: %s，请手动检查任务情况，或该任务已达到上限。\n\n" % repr(result))
                    return False

            except requests.exceptions.ConnectionError:
                retry -= 1
                self.call_moni(var=var, retry=retry)

    def _call_moni_v1(self, var):
        """
        接口 1
        """
        pass

    def _call_moni_v2(self, var):
        """
        接口 2
        """
        self.login()

        headers = dict(self.__default_header__.items())
        headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://iabe.cn/student/ExamTestRecord.aspx?subject=%s" % var,
            "Origin": "http://iabe.cn",
        })

        resp = self.client.get(
            "http://iabe.cn/student/ExamTestRecord.aspx?subject=%s" % var,
            headers=self.__default_header__
        )
        tree_html = bs4.BeautifulSoup(resp.text, "lxml")
        subject_dom = tree_html.find(id="ctl00_ContentPlaceHolder1_Subject")
        subject = subject_dom.attrs["value"]

        payload = dict(Score=random.randint(90, 100), Subject=subject)

        resp = self.client.post(
            "http://iabe.cn/student/ExamTestRecord.aspx",
            data=payload,
            headers=headers,
        )
        return resp.text
