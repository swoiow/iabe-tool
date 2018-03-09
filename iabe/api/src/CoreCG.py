#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import pickle
import time
from functools import lru_cache

import requests

from . import crypto
from .WebBase import ClientWebBase
from iabe import apps
from .ihttp import HTTPHeaders


@lru_cache()
def load_data():
    KEY, IV = os.environ.get("common_key"), os.environ.get("common_iv")
    client = requests.session()
    client.headers = HTTPHeaders.get()

    def _base_info_1():
        url = "http://www.iabe.cn/EcarServer/LoadBaseData.aspx"
        content = dict()

        method = crypto.encrypt("3", key=KEY, iv=IV)
        resp = client.post(url, data=dict(method=method))
        raw = resp.json()
        for item in raw["Ecar_Topic"]:
            content[item["TopicId"]] = dict(
                TopicName=item["TopicName"],
                ColumnId=item["ColumnId"],
            )
        return dict(content)

    def _base_info_2():
        url = "http://www.iabe.cn/EcarServer/LoadBaseData.aspx"
        content = []
        column_data = _base_info_1()

        method = crypto.encrypt("4", key=KEY, iv=IV)
        resp = client.post(url, data=dict(method=method))
        raw = resp.json()
        for item in raw["Ecar_Knowledge"]:
            for i in ["OpenClaim", "PassClaim", "OpenClaimByKnowledgeNo", "IsEmphasis", "MaxHours", "TiMuCount"]:
                item.pop(i)
            item["TopicName"] = column_data[item["TopicId"]]["TopicName"]

            item["p5"] = int(item["MaxPoint"])
            item["p7"] = int(column_data[item["TopicId"]]["ColumnId"])
            item["p8"] = item["TopicId"]
            item["p9"] = item["KnowledgeNo"]
            content.append(item)

        return content

    pkl_path = apps.NewIabeConfig.PKL_PATH
    if not os.path.exists(pkl_path):
        data = _base_info_2()

        with open(pkl_path, "wb") as wf:
            pickle.dump(data, wf)

        return load_data()
    else:
        with open(pkl_path, "rb") as rf:
            return pickle.load(rf)


class CGApi(ClientWebBase):
    PARAM_CGW_1 = 1
    PARAM_CGW_4 = 4

    def __init__(self, username, password, *args, **kwargs):
        super(CGApi, self).__init__(username=username, password=password, *args, **kwargs)

    def call_cgw(self, var=PARAM_CGW_1, part=None, g_retry=3, **kwargs):
        __msg_ = u" 准备执行'闯关任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.logger.error(u"[!!!] 出现异常。")
            return

        action_data = list(self._action_data(var))
        self.login()
        for idx, d_item in enumerate(action_data):
            self._core_cg(d_item, version=3)

            sleep = d_item["p5"] / 2 * 2
            percent = round(float(idx + 1) / len(action_data) * 100, 2)

            self.logger.info(u"当前进度: %s%%: " % percent + u"第%(p7)s章 第%(p8)s节 第%(p9)s条目" % d_item)
            self.logger.debug(repr(d_item) + u"\n已完成{0}题，准备休息{1}秒...".format(d_item["p5"] / 2, sleep))
            time.sleep(sleep)

        self.logger.info(u"闯关已完成...")
        return True

    def call_exchange(self, var=PARAM_CGW_1):
        err_msg = ""
        self.logger.info(" 准备执行'兑换{}任务' ".format(var).center(30, "="))

        if self.meta.ZONE in ["cz"]:
            err_msg = "此地区兑换功能有待完善。"
            self.logger.warning(err_msg)
            return dict(msg=err_msg)
        self.login()

        exchange_uri = self.meta.EXCHANGE_URI
        if var == 4:
            exchange_uri = self.meta.EXCHANGE_URI2

        resp = self.client.get(exchange_uri, headers=self.ExchangeHeaders)
        if resp.status_code < 400:
            try:
                response = resp.json()
                exchange_rv = response["ExChange"][0]["result"]
                exchange_rv = "兑换完成。返回信息: %s\n" % exchange_rv
                self.logger.info(exchange_rv)
                return exchange_rv
            except ValueError:
                err_msg = "[!!] 兑换失败。未知异常，请重试。"
                self.logger.warning(err_msg)

        return dict(msg=err_msg)

    def _core_cg(self, d_item, version=None):
        if version == 3:
            _data = crypto.data2urlencode(self.username, is_post=False, **d_item)
        else:
            _data = crypto.data2urlencode(self.username, is_post=True, **d_item)

        retry = 3
        while retry > 0:
            try:
                resp = self.client.post(self.meta.POST_URI, data=_data, headers=self.CgwHeaders)
                # 188, 表示写入成功; 187, 表示写入不成功
                if resp.text not in ["188", 188]:
                    raise AssertionError(resp.text[:20])
                else:
                    return True
            except requests.exceptions.ConnectionError:
                retry -= 1
            except AssertionError as e:
                self.logger.warning("写入不成功。错误信息：%s" % e)
                retry -= 1
            except KeyboardInterrupt:
                exit(0)

        return False

    def _action_data(self, var):
        ac_map = {self.PARAM_CGW_1: list(range(1, 5)), self.PARAM_CGW_4: list(range(11, 17))}

        for item in load_data():
            if item["p7"] in ac_map[var]:
                yield item
