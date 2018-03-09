#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
import re

import bs4

from . import CoreCG


class ClientWebApi(CoreCG.CGApi):
    def __init__(self, username, password, *args, **kwargs):
        super(ClientWebApi, self).__init__(username=username, password=password, *args, **kwargs)

    def get_today_learn(self):
        """
        获取今日已学
        :return:
        """
        self.client.get(self.meta.LOGIN_URI)  # [BUG 预警] URL 跳转的 COOKIES BUG

        resp = self.client.get(self.meta.INDEX)
        tree_html = bs4.BeautifulSoup(resp.text, "lxml")

        result = tree_html.find(id="ctl00_ContentPlaceHolder1_Hxueshitoday")

        if result:
            return dict(result=result.attrs["value"])
        else:
            return dict(result=-1)

    def get_total_stage(self):
        """
        获取学习进度
        :return:
        """
        text = lambda x: re.sub(re.compile("[</span>]+"), "", x)
        resp = self.client.get(self.meta.INDEX)
        tree_html = bs4.BeautifulSoup(resp.text, "lxml")

        result = [text(i.attrs["data-original-title"]) for i in tree_html.find_all("div", class_="progress")]
        return dict(result="; ".join(result))

    def get_total_learn(self):
        """
        获取各模块已学信息
        :return:
        """

        a = self._get_learn_cg()
        b = self._get_learn_mn()
        c = self._get_learn_vd()

        return {**a, **b, **c}

    def _change_pwd_v1(self, new_password=123456) -> dict:
        """
        第一次登录时修改密码。
        需要更新 models
        """
        self.login()

        uri = "http://iabe.cn/retrieve/guide-step1.aspx?NewPwd={}&Firstpwd=1234".format(new_password)
        resp = self.client.post(uri)

        if resp.text in [1, "1"]:
            return {"result": True, "msg": "修改密码成功", "new_password": new_password}

        return {"result": False, "msg": "修改密码失败"}

    def _change_pwd_v2(self, new_password=123456) -> dict:
        """
        普通方式修改密码。
        需要更新 models
        """
        self.login()

        uri = "http://iabe.cn/Login.ashx?type=1&oldPwd={}&pwd={}".format(self.password, new_password)
        resp = self.client.post(uri)
        if resp.text in [1, "true", True]:
            return {"result": True, "msg": "修改密码成功", "new_password": new_password}

        return {"result": False, "msg": "修改密码失败"}

    def _get_learn_cg(self):
        """
        获取闯关的已学信息
        :return:
        """
        result = {}
        payload = {"username": "%s" % self.username, "maxxueshiperday": "4"}

        resp = self.client.post(self.meta.QUERT_LEARN_CG_1, data=str(payload), headers=self.WebHeaders)
        result["cg1"] = json.loads(resp.json())[0]

        resp = self.client.post(self.meta.QUERT_LEARN_CG_4, data=str(payload), headers=self.WebHeaders)
        result["cg4"] = json.loads(resp.json())[0]

        return result

    def _get_learn_mn(self):
        """
        获取模拟的已学信息
        :return:
        """
        result = {}
        payload = {"username": "%s" % self.username, "citycode": self.meta.CITY_CODE}

        resp = self.client.post(self.meta.QUERT_LEARN_MN_1, data=str(payload), headers=self.WebHeaders)
        result["mn1"] = json.loads(resp.json())[0]

        resp = self.client.post(self.meta.QUERT_LEARN_MN_4, data=str(payload), headers=self.WebHeaders)
        result["mn4"] = json.loads(resp.json())[0]

        return result

    def _get_learn_vd(self):
        """
        获取视频的已学信息
        :return:
        """
        result = {}
        payload = {"username": "%s" % self.username}

        resp = self.client.post(self.meta.QUERT_LEARN_VD_1, data=str(payload), headers=self.WebHeaders)
        result["vd1"] = json.loads(resp.json())[0]

        resp = self.client.post(self.meta.QUERT_LEARN_VD_4, data=str(payload), headers=self.WebHeaders)
        result["vd4"] = json.loads(resp.json())[0]

        return result
