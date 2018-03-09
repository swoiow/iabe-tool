#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
from functools import partial

from suds.client import Client

from . import CoreMN
from .ihttp import Requests2Transport


class ClientWebServiceApi(CoreMN.MNApi):
    def __init__(self, username, password, *args, **kwargs):
        super(ClientWebServiceApi, self).__init__(username=username, password=password, *args, **kwargs)

    @property
    def ws_client(self):
        http = Requests2Transport(headers=self.WebserviceHeaders)
        if not self.is_login:
            self.login()
            http.session = self.client

        SoapClient = partial(Client, transport=http)
        client = SoapClient(self.meta.WEBSERVICE_URI + "?wsdl")
        # self.get_hao()  # 临时执行

        return client

    @property
    def get_hao(self):
        # [完成]
        if not getattr(self.meta, "SN", None):
            xx = self.get_xinxi()
            sn = self._get_liu_shui_hao(xx)
            self.__SN_CODE_ = sn
            self.logger.info("get sn: %s" % self.__SN_CODE_)
        return self.__SN_CODE_

    def get_xinxi(self):
        # return dict
        return self._get_xin_xi_v1()

    def _get_xin_xi_v1(self):
        # [完成]
        result = self.ws_client.service.GetXueYuanJiBenXinXiToWebServer(self.username)
        return result.unescape()

    def _get_xin_xi_v2(self):
        # [完成]
        result = self.ws_client.service.XueYuanJiBenXinXi_ChaXunSuoYouXinXiNew(self.username, self.password)
        return result.unescape()

    def _get_liu_shui_hao(self, text):
        # [完成]
        ls_rule = re.compile(r'(?<=<XueYuanLiuShuiHao>)[0-9]+(?=</XueYuanLiuShuiHao>)')
        ls_code = re.findall(ls_rule, text)

        assert len(ls_code) > 0
        return ls_code[0]
