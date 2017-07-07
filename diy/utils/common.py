#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import pickle
import random
import re
import time
from functools import partial

import requests
from suds.client import Client

import Config
import utils.basic as BasicItf
from utils.logerUnit import LogerInterface
from utils.loginUnit import *
from utils.sudsUnit import Requests2Transport

URLSeeker = BasicItf.URLSeeker
default_header = BasicItf.default_header
req_kwargs = dict(headers=default_header)


class BaseClass(LogerInterface):
    """
    初始化信息的入口，包括http头，帐号信息
    """
    _web_session = requests.Session()
    _default_header = dict(default_header.items())

    def __init__(self, username="", password="", *args, **kwargs):
        """
        prefix, zone: 要求小写
        :param username: 要求不带空格
        :param password: 要求不带空格
        :param kwargs: 
                level: debug
        """
        if not kwargs.get("log_level"):
            kwargs["log_level"] = "debug"
        super(BaseClass, self).__init__(log_name=username, **kwargs)

        self.username = username
        self.password = password
        self.is_login = False
        self.zone = self._initialize()
        self.prefix = self.SUB_DOMAIN

    def login(self):
        if not self.is_login:
            self._login()

        return self.web_session

    @property
    def web_session(self):
        return self._web_session

    def _initialize(self):
        cfg = Config.cfg
        # 进行地区服务地址初始化
        if not hasattr(self, "zone"):
            for prefix in cfg.sections():
                if self.username.upper().startswith(prefix):
                    for k, v in cfg[prefix].items():
                        k = k.upper()
                        if k.find("URI") > 0:
                            v = "http://" + v
                        setattr(self, k, v)

                    return prefix.lower()

            err = u"[!!!] Unable to initialize this account. Please provide Username or Zone. 该地区不支持!"
            return Exception(self.logger.error(err))

    def _login(self):
        assert all([self.username, self.password])

        retry = 3
        while retry > 0:
            try:
                if hasattr(self, "CITY_CODE"):
                    if not self._go_login_1():
                        raise requests.ConnectionError

                else:
                    if not self._go_login_2():
                        raise requests.ConnectionError

                self.is_login = True
                self.logger.info(u"登录成功...")
                cookies = BasicItf.encrypt(self._web_session.cookies, key="+cookIes", iv="+cookIes")
                self.logger.debug(u"登录后的Cookie: %s\n" % cookies)

                return self.web_session

            except AssertionError:
                retry -= 1
                self.logger.error(u"[!!!] 登录失败，或密码错误。\n")

            except requests.ConnectionError as e:
                retry -= 1
                self.logger.info("More info: %s\n" % repr(e))
                self.logger.warning(u"[!!] 网络连接异常, Retrying...%s\n" % (3 - retry))

        raise Exception(self.logger.error(u"[!!!] 多次登录不成功，退出。"))

    def _go_login_1(self):
        """新登录"""
        default_login_uri = "http://iabe.cn/Index.aspx"
        assert hasattr(self, "CITY_CODE")

        code = self._asp_web_code_1()
        payload = {
            "ctl00$ContentPlaceHolder1$txtUserName": self.username,
            "ctl00$ContentPlaceHolder1$txtPassword": self.password,
            "ctl00$ContentPlaceHolder1$selcitycode": self.CITY_CODE,
            "__VIEWSTATE": code,
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnlogin",
        }
        self.web_session.post(default_login_uri, data=payload, headers=self._default_header)

        assert self._login_cookies_check()
        return True

    def _go_login_2(self):
        """旧登录"""
        default_login_uri = "http://yl.iabe.cn/Index.aspx"
        assert hasattr(self, "LOGIN_URI")

        username, password = self.username, self.password
        code = self._asp_web_code_2()
        payload = {
            "__VIEWSTATE": code,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$UserName": username,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$Password": password,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$BtnLogin": ""
        }
        self._web_session.post(default_login_uri, data=payload, headers=self._default_header)

        payload = {"userName": username, "password": password}
        self._web_session.post(self.LOGIN_URI, data=payload, headers=self._default_header)

        assert self._login_cookies_check()
        return True

    @staticmethod
    def _asp_web_code_1():
        return get_net_code_with_htmlparser()

    @staticmethod
    def _asp_web_code_2():
        return get_net_code_with_htmlparser2()

    def _login_cookies_check(self):
        cookies_keys = self.web_session.cookies.keys()
        return any(["citycode" in cookies_keys, "User" in cookies_keys, self.username in cookies_keys])

    @staticmethod
    def fake_ip(headers):
        randint = random.randint
        modify_list = [
            "Via", "CLIENT_IP", "X-Real-Ip", "REMOTE_ADDR", "REMOTE_HOST", "X-Forwarded-For", "X_FORWARDED_FOR"
        ]
        random_ip = lambda: "%s.%s.%s.%s" % (randint(1, 255), randint(0, 255), randint(0, 255), randint(1, 255))
        headers.update({k: random_ip() for k in modify_list})
        return headers

    def cg_headers(self):
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.8",
            "X-Requested-With": "ShockwaveFlash/26.0.0.131",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # headers = self.fake_ip(headers)

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.prefix,
            "Referer": "http://%s.iabe.cn/ecar/ProjectEcar.swf?v=123456" % self.prefix,
        }

        headers.update(self._default_header, **swf_headers)
        return headers

    def ws_headers(self):
        headers = {"X-Requested-With": "ShockwaveFlash/26.0.0.131", "Content-Type": "text/xml; charset=utf-8", }

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.prefix,
            "Referer": self.WS_REFERER,
        }

        headers.update(self._default_header, **swf_headers)
        return headers

    def ex_headers(self):
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://%s.iabe.cn/public/Index.aspx?area=8" % self.prefix,
        }

        headers.update(self._default_header)
        return headers


class BaseWebService(object):
    __default_ws_url__ = "http://" + Config.cfg["FS"]["WEBSERVICE_URI"] + "?wsdl"

    def __init__(self, *args, **kwargs):
        self._client = Client(self.__default_ws_url__)

    def _get_ti_mu_100(self):
        result = self._client.service.GetRandom100TiMuString(allowDriveCarType="C1")
        return result.unescape()

    def _get_ti_mu_50(self):
        result = self._client.service.GetRandom50TiMuString()
        return result.unescape()


class IabeWebService(BaseClass, BaseWebService):
    __default_header__ = dict(default_header.items())
    meta = {}

    @classmethod
    def from_orm(cls, orm_obj, **kwargs):
        o = cls(orm_obj.username, orm_obj.password, **kwargs)

        o.meta = {k: v for k, v in orm_obj.__dict__.items() if not k.startswith("_")}
        http = Requests2Transport(**req_kwargs)
        # http.session = o.web_session
        o._client = Client(o.WEBSERVICE_URI + "?wsdl", transport=http)
        o._ws = o._client

        return o

    @classmethod
    def from_simple(cls, username, password, *args, **kwargs):
        o = cls(username, password, **kwargs)
        o.init_ws(**req_kwargs)

        return o

    def init_ws(self, login=False, session=None, **kwargs):
        try:
            assert hasattr(self, "WEBSERVICE_URI")
        except AssertionError:
            Exception(self.logger.error(u"[!!!] 操作失败。未能初始化服务，用户名错误或该地区不被支持。"))

        http = Requests2Transport(**kwargs)
        if session:
            http.session = session
        if login and (not self.is_login):
            self.login()
            http.session = self.web_session

        SoapClient = partial(Client, transport=http)
        self._client = SoapClient(self.WEBSERVICE_URI + "?wsdl", )
        self.get_hao()  # 临时执行

    def get_xinxi(self):
        # return dict
        return self._get_xin_xi_v1()

    def get_hao(self):
        # [完成]
        hao = getattr(self.meta, "lscode", None)
        if not hao:
            hao = self._get_liu_shui_hao(self._get_xin_xi_v1())
            self.LiuShuiHao = hao
        return self.LiuShuiHao

    def get_xueshi(self):
        """今天学时"""
        # [完成]
        result = u"不支持"
        self.logger.info(u" 准备执行'查询学时情况' ".center(30, "="))
        if self.zone not in ["cz"]:
            result = self._get_jin_tian_xue_shi()

        self.logger.info(u"今天已学 %s 小时" % result)
        return result

    def get_stage(self):
        """学习阶段"""
        # [完成]
        self.logger.info(u" 准备执行'查询学习阶段情况' ".center(30, "="))

        return self._get_learn_stage()

    def _get_jin_tian_xue_shi(self):
        # [完成]
        hao = getattr(self, "LiuShuiHao", None)
        if not hao:
            hao = self.get_hao()

        result = self._client.service.GetTrainTimePassedToday(hao)
        return result  # float

    def _get_learn_stage(self):
        hao = getattr(self, "LiuShuiHao", None)
        if not hao:
            hao = self.get_hao()

        result = self._client.service.GetStudentsubjectInfoByCardNum(hao)
        return result  # float

    def _get_xin_xi_v1(self):
        # [完成]
        result = self._client.service.GetXueYuanJiBenXinXiToWebServer(self.username)
        return result.unescape()

    def _get_xin_xi_v2(self):
        # [完成]
        result = self._client.service.XueYuanJiBenXinXi_ChaXunSuoYouXinXiNew(self.username, self.password)
        return result.unescape()

    def _get_liu_shui_hao(self, text):
        # [完成]
        ls_rule = re.compile(r'(?<=<XueYuanLiuShuiHao>)[0-9]+(?=</XueYuanLiuShuiHao>)')
        ls_code = re.findall(ls_rule, text)

        assert len(ls_code) > 0
        return ls_code[0]

    def _get_moni4(self):
        # [未通过测试]
        self.login()

        result = self._client.service.ZQ_XueXiRiZhiToExamThree(
            XueYuanLiuShuiHao=str(BasicItf.encrypt_ws(self.LiuShuiHao), "utf8"),
            BeiZhu=str(BasicItf.encrypt_ws(90), "utf8")
        )
        print(result.unescape())


class Iabe(BaseClass):
    __default_header__ = dict(default_header.items())

    @classmethod
    def set_account(cls, orm_obj, **kwargs):
        o = cls(orm_obj.username, orm_obj.password, **kwargs)  # 初始化了loger，info
        o.meta = {k: v for k, v in orm_obj.__dict__.items() if not k.startswith("_")}

        return o

    @classmethod
    def set_simple(cls, username, password, **kwargs):
        o = cls(username, password, **kwargs)  # 初始化了loger，info
        return o

    @property
    def ws(self):
        if not hasattr(self, "_ws"):
            self._ws = IabeWebService.from_simple(self.username, self.password)

        return self._ws

    def call_cgw(self, var="cg1", part=None, g_retry=3, **kwargs):
        """
        :param part: Default: map(str, [1, 2, 3, 4, 11, 12, 13, 15, 16])
        :param var: choose in [cg1, cg4, cg0]. Default: cg0
        """
        __msg_ = u" 准备执行'闯关任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.logger.error(u"[!!!] 出现异常。")
            return

        part = part and [str(i) for i in list(part)] or [str(i) for i in [1, 2, 3, 4, 11, 12, 13, 15, 16]]
        _keys, _values = self.__CG_choose__(var)
        _zip = [dict(zip(_keys, item)) for item in _values]
        action_data = [item for item in _zip if str(item["p7"]) in part]

        self.login()

        for idx, d_item in enumerate(action_data):
            self._core_cg(d_item)

            sleep = d_item["p5"] / 2 * 2
            percent = round(float(idx + 1) / len(action_data) * 100, 2)
            self.logger.info(u"当前进度: %s%%: " % percent + u"第%(p7)s章 第%(p8)s节 第%(p9)s条目" % d_item)
            self.logger.debug(repr(d_item) + u"\n已完成{0}题，准备休息{1}秒...".format(d_item["p5"] / 2, sleep))
            time.sleep(sleep)

        self.logger.info(u"闯关已完成...")
        return

    def call_cgw_v2(self, var="cg1", part=None, g_retry=3, **kwargs):
        __msg_ = u" 准备执行'闯关任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.logger.error(u"[!!!] 出现异常。")
            return

        action_data = self.__CG_choose__v2(var)
        self.login()
        for idx, d_item in enumerate(action_data[2:]):
            self._core_cg(d_item, version=3)

            sleep = d_item["p5"] / 2 * 2
            percent = round(float(idx + 1) / len(action_data) * 100, 2)

            self.logger.info(u"当前进度: %s%%: " % percent + u"第%(p7)s章 第%(p8)s节 第%(p9)s条目" % d_item)
            self.logger.debug(repr(d_item) + u"\n已完成{0}题，准备休息{1}秒...".format(d_item["p5"] / 2, sleep))
            time.sleep(sleep)

        self.logger.info(u"闯关已完成...")
        return True

    def call_moni_v1(self, var="mn_old", g_retry=3, lscode="", **kwargs):
        """
        :param var: choose in "mn_old, mnks4". Default: mn_old
        """
        __msg_ = u" 准备执行'模拟任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.error(u"[!!!] 出现异常。")
            return

        client = self.WebService
        ls_code = lscode or self.call_get_ls_code(**kwargs)
        resp_code = ""

        if not self.is_login:
            self.login()
            return self.call_moni_v1(var=var, g_retry=g_retry - 1, lscode=lscode, **kwargs)

        if var == "mn_old":
            data = {
                "ls_code": self.encrypt_ws(ls_code),
                "x_code": self.encrypt_ws(self.username),
                "password": self.encrypt_ws(self.password),
                "timuls_code": self.encrypt_ws("0"),
                "bool": self.encrypt_ws("T"),
                "mark": self.encrypt_ws(random.randint(90, 100)),
            }

            resp_code = client.func_hb_shujushangchuanjiekou_xuexirizhi(sessionObj=self.session, **data)

        if var == "mnks4":
            data = {
                "ls_code": self.encrypt(ls_code),
                "mark": self.encrypt(random.randint(90, 100)),
            }
            data.update(dict(zone=self.zone))
            resp_code = client.func_zq_xuexirizhitoexamthree(sessionObj=self.session, **data)

        if resp_code == "true":
            self.info(u"已完成一套！10秒后自动退出...\n\n")
        else:
            self.warning(u"[!!] 返回结果: %s，请手动检查任务情况，或该任务已达到上限。\n\n" % repr(resp_code))

        return time.sleep(10)

    def call_moni_v2(self, var, retry=3):
        # assert var in [2, 9]
        _var_ = 9 if var == "mn4" else 2
        __msg_ = u" 准备执行'模拟任务: %s' " % var
        self.logger.info(__msg_.center(30, "="))

        if retry < 0:
            self.logger.error(u"[!!!] 超出重试限制。")
            return
        else:
            self.login()

            try:
                result = self._call_moni_v2(_var_)
                if result:
                    self.logger.info(u"已完成一套！10秒后自动退出...\n\n")
                    return dict(result=True) if result == "1" else dict(result=result)

            except requests.exceptions.ConnectionError:
                retry -= 1
                self.call_moni_v2(var=var, retry=retry)

        return time.sleep(10)

    def call_exchange(self, var="1"):
        self.logger.info(u" 准备执行'兑换{}任务' ".format(var).center(30, "="))
        if self.zone in ["cz"]:
            self.logger.warning(u"此地区兑换功能有待完善。")
            return dict(msg=u"此地区兑换功能有待完善。")
        self.login()

        exchange_uri = self.EXCHANGE_URI
        if var == "4":
            exchange_uri = self.EXCHANGE_URI2

        resp = self.web_session.get(exchange_uri, headers=self._default_header)
        if resp.status_code < 400:
            try:
                response = resp.json()
                exchange_rv = response["ExChange"][0]["result"]
                self.logger.info(u"兑换完成。返回信息: %s\n" % exchange_rv)
                return exchange_rv
            except ValueError:
                self.logger.warning(u"[!!] 兑换失败。未知异常，请重试。")
        return dict(msg=u"[!!] 兑换失败。未知异常，请重试。")

    def call_learn_progress(self):
        """学习进度"""
        self.logger.info(u" 准备执行'查询学习进度情况' ".center(30, "="))
        self.login()

        req = self.web_session.get(self.SCHEDULE_URI, headers=self.__default_header__)
        data = ""
        for item in [("dl", "class", "traningResul")]:
            url_seeker = URLSeeker(item)
            url_seeker.feed(req.text)
            data += url_seeker.data

        result = u"学习进度: " + data
        self.logger.info(result)
        return dict(result=result)

    def _call_moni_v2(self, var):
        self.login()

        headers = dict(self.__default_header__.items())
        headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://iabe.cn/student/ExamTestRecord.aspx?subject=%s" % var,
            "Origin": "http://iabe.cn",
        })

        gt = self.web_session.get(
            "http://iabe.cn/student/ExamTestRecord.aspx?subject=%s" % var,
            headers=self._default_header
        )
        url_seeker = URLSeeker(("input", "id", "ctl00_ContentPlaceHolder1_Subject"), dom_attr=(True, "value"))
        url_seeker.feed(gt.text)

        payload = dict(Score=random.randint(90, 100), Subject=url_seeker.dom_attr_value)

        resp = self.web_session.post(
            "http://iabe.cn/student/ExamTestRecord.aspx",
            data=payload,
            headers=headers,
            # proxies=proxy_settings
        )
        return resp.text

    def _core_cg(self, d_item, version=None):
        if version == 3:
            _data = BasicItf.data2urlencode(self.username, is_post=False, **d_item)
        else:
            _data = BasicItf.data2urlencode(self.username, is_post=True, **d_item)

        retry = 3
        while retry > 0:
            try:
                resp = self.web_session.post(self.POST_URI, data=_data, headers=self.cg_headers())
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

    def __call_get_learned_cgw__(self):
        """ 已过时 (2017-04-24) """
        self.logger.info(u" 准备执行'查询闯关情况' ".center(30, "="))

        if not self.is_login: self.login()
        client = self.web_session
        gt = client.get("http://www.iabe.cn/public/Index.aspx?area=8", headers=self._default_header)
        url_seeker = URLSeeker(("a", "id", "ctl00_ContentPlaceHolder1_ctl00_labYiHouDeXueShi"))
        url_seeker.feed(gt.text)

        return {"data": u"闯关王: " + url_seeker.data}

    def __call_get_learned_mnks__(self):
        """ 已过时 (2017-04-24) """
        self.logger.info(u" 准备执行'查询模拟情况' ".center(30, "="))

        if not self.is_login: self.login()
        client = self._web_session
        gt = client.get("http://www.iabe.cn/public/Index.aspx?area=3", headers=self._default_header)
        url_seeker = URLSeeker(("span", "id", "ctl00_ContentPlaceHolder1_ctl00_labHuoDeXueShi"))
        url_seeker.feed(gt.text)
        return {"data": u"模拟考试: " + url_seeker.data}

    _keys = ["p7", "p8", "p9", "p5"]
    _values = []

    def _params_cg0(self):
        self._p7, self._p8, self._p9 = 1, 1, 1

        # 第1章
        self.__f_([104, 14, 28, 68, 44, 54, 92, 40, 18, 40, 26, 42, 36])
        self.__f_([28, 16])
        self.__f_([30, 10])
        self.__f_([22, 2, 18, 12, 4])
        self.__f_([16, 10, 24, 10, 6, 4, 12, 4, 10, 16, 6, 54, 18, 14, 10, 10, 14])
        self.__f_([20, 8, 6, 4, 6])

        # 第2章
        self._p7 = 2
        self.__f_([16, 14, 10, 10, 14, 10, 4])
        self.__f_([200, 82, 104, 102, 10])
        self.__f_([84, 54, 16])
        self.__f_([6, 4, 6, 4, 6, 4, 4, 2])

        # 第3章
        self._p7 = 3
        self.__f_([246, 28, 22, 4, 30, 86, 26, 18])
        self.__f_([84, 30, 6, 10, 20, 6, 6, 12])

        # 第4章
        self._p7 = 4
        self._p9 = 85  # patch 跳过84
        self.__f_([22, 12, 12, 24, 10, 14, 10, 8, 10, 12, 46])
        self.__f_([6, 2, 8, 6, 6, 2, 8, 12, 18])
        self.__f_([2, 16, 18, 6])

    def _params_cg1(self):
        self._p7, self._p8, self._p9 = 1, 1, 1

        # 第1章
        self.__f_([60, 60, 80])
        self.__f_([50])

        # 第2章
        self._p7 = 2
        self.__f_([60, 60, 60, 60, 60, 60, 60, 60, 100, 136])
        self.__f_([80, 80, 80, 80, 80, 80, 80, 80, 120, 124])
        self.__f_([60, 62])

        # 第3章
        self._p7 = 3
        self.__f_([48])
        self.__f_([78])
        self.__f_([102])

        # 第4章
        self._p7 = 4
        self.__f_([72])

    def _params_cg4(self):
        self._p7, self._p8, self._p9 = 15, 18, 46

        self.__f_([20])
        self.__f_([12])
        self.__f_([50, 50])
        self.__f_([60, 60, 60, 60, 60, 60, 58])

        self._p7 = 16
        self.__f_([60, 64])  # p8 = 22
        self.__f_([60, 72])
        self.__f_([36])
        self.__f_([56])

        self._p7, self._p8, self._p9 = 11, 29, 70

        self.__f_([52])  # p9 = 70
        self.__f_([50, 58])
        self.__f_([58])
        self.__f_([80, 88])
        self.__f_([60, 70])

        self._p7 = 12
        self.__f_([60, 82])
        self.__f_([74])

        self._p7 = 13
        self.__f_([60])
        self.__f_([36])

        self._p7 = 14
        self.__f_([12])
        self.__f_([54])
        self.__f_([18])

    def __CG_choose__(self, var=""):
        var = var or "cg0"
        ac_map = {"cg1": self._params_cg1, "cg4": self._params_cg4, "cg0": self._params_cg0}
        ac_map[var]()
        return self._keys, self._values

    def __f_(self, *arg):
        length = len(*arg)
        self._values += zip(
            [self._p7] * length,
            [self._p8] * length,
            range(self._p9, self._p9 + length),
            *arg
        )

        self._p8 += 1
        self._p9 += length

    def __CG_choose__v2(self, var=""):
        var = var or "cg1"
        ac_map = {"cg1": list(range(1, 5)), "cg4": list(range(11, 17))}

        data = [item for item in load_data() if item["p7"] in ac_map[var]]
        return data


def load_data():
    def _base_info_1():
        url = "http://www.iabe.cn/EcarServer/LoadBaseData.aspx"
        data = dict()

        method = BasicItf.encrypt("3", key=os.environ.get("common_key"), iv=os.environ.get("common_iv"))
        resp = requests.post(url, data=dict(method=method), headers=default_header)
        raw = resp.json()
        for item in raw["Ecar_Topic"]:
            # data.append((item["TopicId"], item["ColumnId"]))
            data[item["TopicId"]] = dict(
                TopicName=item["TopicName"],
                ColumnId=item["ColumnId"],
            )
        return dict(data)

    def _base_info_2():
        url = "http://www.iabe.cn/EcarServer/LoadBaseData.aspx"
        base_data = []
        column_data = _base_info_1()

        m = BasicItf.encrypt("4", key=os.environ.get("common_key"), iv=os.environ.get("common_iv"))
        resp = requests.post(url, data=dict(method=m), headers=default_header)
        raw = resp.json()
        for item in raw["Ecar_Knowledge"]:
            for i in ["OpenClaim", "PassClaim", "OpenClaimByKnowledgeNo", "IsEmphasis", "MaxHours", "TiMuCount"]:
                item.pop(i)
            item["TopicName"] = column_data[item["TopicId"]]["TopicName"]

            item["p5"] = int(item["MaxPoint"])
            item["p7"] = int(column_data[item["TopicId"]]["ColumnId"])
            item["p8"] = item["TopicId"]
            item["p9"] = item["KnowledgeNo"]
            base_data.append(item)

        return base_data

    PKL_PATH = Config.PKL_PATH
    if not os.path.exists(PKL_PATH):
        base_data = _base_info_2()

        with open(PKL_PATH, "wb") as wf:
            pickle.dump(base_data, wf)

        return load_data()
    else:
        with open(PKL_PATH, "rb") as rf:
            return pickle.load(rf)
