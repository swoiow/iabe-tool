#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import os
import pickle
import random
import re
import time
from functools import partial, wraps

import requests
from suds.client import Client

from . import CoreCommon
from .HttpCommon import HTTPHeaders
from .LogCommon import Logger
from .SudsCommon import Requests2Transport
from .. import apps

Cache = CoreCommon.Bucket(timeout=1800)
URLSeeker = CoreCommon.URLSeeker


def SessionCache(f):
    @wraps(f)
    def swap(cls, *args, **kwargs):
        cache_session = Cache.get(key=cls.username)
        if cache_session:
            cls.is_login = True
            return cache_session
        else:
            session = f(cls)
            Cache.set(cls.username, session)

    return swap


class Meta(object):
    def __init__(self, name):
        self.name = name
        self.username = name

    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.name)


class PostHeaders(object):
    __default_header__ = HTTPHeaders.get()

    def cg_headers(self):
        headers = {
            "X-Requested-With": "ShockwaveFlash/27.0.0.180",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.SUB_DOMAIN,
            "Referer": "http://%s.iabe.cn/ecar/ProjectEcar.swf?v=123456" % self.SUB_DOMAIN,
        }

        headers.update(self.__default_header__, **swf_headers)
        return headers

    def ws_headers(self):
        headers = {
            "X-Requested-With": "ShockwaveFlash/27.0.0.180",
            "Content-Type": "text/xml; charset=utf-8",
        }

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.SUB_DOMAIN,
            "Referer": self.WS_REFERER,
        }

        headers.update(self.__default_header__, **swf_headers)
        return headers

    def ex_headers(self):
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://%s.iabe.cn/public/Index.aspx?area=8" % self.SUB_DOMAIN,
        }

        headers.update(self.__default_header__)
        return headers

    @staticmethod
    def fake_ip(headers):
        def random_ip(): return "%s.%s.%s.%s" % (randint(1, 255), randint(0, 255), randint(0, 255), randint(1, 255))

        randint = random.randint
        modify_list = [
            "Via", "CLIENT_IP", "X-Real-Ip", "REMOTE_ADDR", "REMOTE_HOST", "X-Forwarded-For", "X_FORWARDED_FOR"
        ]
        ip = random_ip()
        headers.update({k: ip for k in modify_list})
        return headers


class BaseClient(object):
    """
    初始化信息的入口，包括http头，帐号信息
    """
    _default_header = HTTPHeaders.get()

    def __init__(self, username="", password="", zone=None, *args, **kwargs):
        """
        prefix, zone: 要求小写
        :param username: 要求不带空格
        :param password: 要求不带空格
        :param kwargs:
                level: debug
        """
        self.username = username
        self.password = password

        self.logger = Logger(name="log_" + self.username, log_db=True, **kwargs)

        assert zone is not None
        self.zone = zone

        self.is_login = False

        self.meta = Meta(self.username)
        self.zone = self.call_setting_init(self.zone)
        self.prefix = self.SUB_DOMAIN

        self._web_session = requests.Session()

    @SessionCache
    def login(self):
        if not self.is_login:
            self._login()

        return self.web_session

    @property
    def web_session(self):
        return self._web_session

    def call_setting_init(self, zone=None):
        # 进行地区服务地址初始化
        cfg = apps.cfg

        if zone:
            for k, v in cfg[zone.upper()].items():
                k = k.upper()
                if k.find("URI") > 0:
                    v = "http://" + v
                setattr(self, k, v)

            return self.zone

        for prefix in cfg.sections():
            if self.username.upper().startswith(prefix):
                for k, v in cfg[prefix].items():
                    k = k.upper()
                    if k.find("URI") > 0:
                        v = "http://" + v
                    setattr(self, k, v)

                break

        err = u"[!!!] Unable to initialize this account. Please provide Username or Zone. 该地区不支持!"
        return Exception(self.logger.error(err))

    def _login(self):
        assert all([self.username, self.password])

        retry = 3
        while retry > 0:
            try:
                if hasattr(self, "CITY_CODE"):
                    if not self._go_login_v1():
                        raise requests.ConnectionError

                else:
                    if not self._go_login_v2():
                        raise requests.ConnectionError

                self.is_login = True
                self.logger.info(u"登录成功...")
                cookies = CoreCommon.encrypt(self._web_session.cookies, key="+cookIes", iv="+cookIes")
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

    def _go_login_v1(self):
        """新登录"""
        default_login_uri = "http://iabe.cn/Index.aspx"
        assert hasattr(self, "CITY_CODE")

        code = self.get_net_code_with_re()
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

    def _go_login_v2(self):
        """旧登录"""
        default_login_uri = "http://yl.iabe.cn/public/default.aspx"
        assert hasattr(self, "LOGIN_URI")

        code = self.get_net_code_with_re()
        payload = {
            "__VIEWSTATE": code,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$UserName": self.username,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$Password": self.password,
            "ctl00$ContentPlaceHolder1$LoginView1$Login1$BtnLogin": ""
        }
        self._web_session.post(default_login_uri, data=payload, headers=self._default_header)

        payload = {"userName": self.username, "password": self.password}
        self._web_session.post(self.LOGIN_URI, data=payload, headers=self._default_header)

        assert self._login_cookies_check()
        return True

    def _login_cookies_check(self, session=None):
        if not session:
            session = self.web_session

        assert isinstance(session, requests.Session) is True
        cookies_keys = session.cookies.keys()
        return any(["citycode" in cookies_keys, "User" in cookies_keys, self.username in cookies_keys])

    @staticmethod
    def get_net_code_with_re():
        """" 通过正则方式获取ASP.NET的 __VIEWSTATE """
        client = requests.session()
        client.headers = HTTPHeaders.get()

        rule = re.compile('(?<=VIEWSTATE" value=")[\w/+=]+(?=")', re.MULTILINE)
        urls = [
            "http://www.iabe.cn/Index.aspx",
            "http://yl.iabe.cn/StaticPage/subject/comments.aspx",
            "http://yl.iabe.cn/public/default.aspx",
            "http://yl.iabe.cn/public/Index.aspx?area=8"
        ]

        for uri in urls:
            resp = client.get(uri)
            code = re.findall(rule, resp.text)

            if code:
                return code[0]

        logging.warning(u"[!!] Get Code Failed.")
        raise requests.ConnectionError


class BaseWebService(object):

    def __init__(self, *args, **kwargs):
        self.__default_ws_url__ = "http://" + apps.cfg["FS"]["WEBSERVICE_URI"] + "?wsdl"

        self._client = Client(self.__default_ws_url__)

    def _get_ti_mu_100(self):
        result = self._client.service.GetRandom100TiMuString(allowDriveCarType="C1")
        return result.unescape()

    def _get_ti_mu_50(self):
        result = self._client.service.GetRandom50TiMuString()
        return result.unescape()


class ClientWebService(BaseClient, BaseWebService):
    __default_header__ = HTTPHeaders.get()

    @classmethod
    def from_orm(cls, orm_obj, **kwargs):
        o = cls(orm_obj.username, orm_obj.password, zone=orm_obj.zone, **kwargs)

        if kwargs.get("zone"):
            o.call_setting_init(zone=kwargs["zone"])

        o.meta = {k: v for k, v in orm_obj.__dict__.items() if not k.startswith("_")}
        http = Requests2Transport(headers=cls.__default_header__, **kwargs)
        # http.session = o.web_session
        o._client = Client(o.WEBSERVICE_URI + "?wsdl", transport=http)
        o._ws = o._client

        return o

    @classmethod
    def from_simple(cls, username, password, **kwargs):
        o = cls(username, password, **kwargs)

        if kwargs.get("zone"):
            o.call_setting_init(zone=kwargs["zone"])
        o.init_ws(headers=cls.__default_header__, **kwargs)

        return o

    def init_ws(self, login=False, session=None, **kwargs):
        try:
            assert hasattr(self, "WEBSERVICE_URI")
        except AssertionError:
            Exception(self.logger.error(u"[!!!] 操作失败。未能初始化服务，用户名错误或该地区不被支持。"))

        http = Requests2Transport(headers=self.__default_header__)
        if session:
            http.session = session
        if login and (not self.is_login):
            self.login()
            http.session = self.web_session

        SoapClient = partial(Client, transport=http)
        self._client = SoapClient(self.WEBSERVICE_URI + "?wsdl")
        self.get_hao()  # 临时执行

    def get_xinxi(self):
        # return dict
        return self._get_xin_xi_v1()

    def get_hao(self):
        # [完成]
        if not getattr(self.meta, "lscode", None):
            xx = self.get_xinxi()
            hao = self._get_liu_shui_hao(xx)
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
        return dict(msg=result)

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

    def _get_moni1(self):
        # [完成]
        self.login()
        encrypt = CoreCommon.encrypt_ws

        result = self._client.service.Hb_ShuJuShangChuanJieKou_XueXiRiZhi(
            XueYuanLiuShuiHao=encrypt(self.LiuShuiHao).decode(),
            XueHao=encrypt(self.username).decode(),
            PassWord=encrypt(self.password).decode(),
            TiMuLiuShuiHao=encrypt("0").decode(),
            TrueOrFalse=encrypt("T").decode(),
            BeiZhu=encrypt(random.randint(90, 100)).decode(),
        )

        if CoreCommon.to_bool(result):
            return True

        return False

    def _get_moni4(self):
        # [完成]
        self.login()
        KEY, IV = os.environ.get("common_key"), os.environ.get("common_iv")
        encrypt = partial(CoreCommon.encrypt, key=KEY, iv=IV)

        result = self._client.service.ZQ_XueXiRiZhiToExamThree(
            XueYuanLiuShuiHao=str(encrypt(self.LiuShuiHao), "utf8"),
            BeiZhu=str(encrypt(90), "utf8")
        )
        if CoreCommon.to_bool(result.unescape()):
            return True

        return False


class ClientWebApi(BaseClient):
    PARAM_CGW_1 = 1
    PARAM_CGW_4 = 4
    PARAM_MONI_1 = 2
    PARAM_MONI_4 = 9

    __default_header__ = HTTPHeaders.get()

    @classmethod
    def set_account(cls, orm_obj, **kwargs):
        o = cls(orm_obj.username, orm_obj.password, zone=orm_obj.zone, **kwargs)  # 初始化了loger，info
        o.meta = {k: v for k, v in orm_obj.__dict__.items() if not k.startswith("_")}

        return o

    @classmethod
    def set_simple(cls, username, password, **kwargs):
        o = cls(username, password, **kwargs)  # 初始化了loger，info
        return o

    @property
    def ws(self):
        if not hasattr(self, "_ws"):
            setattr(self, "_ws", ClientWebService.from_simple(self.username, self.password))

        return getattr(self, "_ws", None)

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
                result = self._call_moni_v2(var)
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

    def call_exchange(self, var=PARAM_CGW_1):
        self.logger.info(u" 准备执行'兑换{}任务' ".format(var).center(30, "="))
        if self.zone in ["cz"]:
            self.logger.warning(u"此地区兑换功能有待完善。")
            return dict(msg=u"此地区兑换功能有待完善。")
        self.login()

        exchange_uri = self.EXCHANGE_URI
        if var == 4:
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

        req = self.web_session.get(self.SCHEDULE_URI, headers=self._default_header)
        data = []
        for item in [("dl", "class", "traningResul")]:
            url_seeker = URLSeeker(item)
            url_seeker.feed(req.text)
            data = url_seeker.data

        result = u"学习进度: " + "; ".join([i for i in data if i])
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

        visit_token = self.web_session.get(
            "http://iabe.cn/student/ExamTestRecord.aspx?subject=%s" % var,
            headers=self._default_header
        )
        url_seeker = URLSeeker(("input", "id", "ctl00_ContentPlaceHolder1_Subject"), dom_attr=(True, "value"))
        url_seeker.feed(visit_token.text)

        payload = dict(Score=random.randint(90, 100), Subject=url_seeker.dom_attr_value)

        resp = self.web_session.post(
            "http://iabe.cn/student/ExamTestRecord.aspx",
            data=payload,
            headers=headers,
        )
        return resp.text

    def _core_cg(self, d_item, version=None):
        if version == 3:
            _data = CoreCommon.data2urlencode(self.username, is_post=False, **d_item)
        else:
            _data = CoreCommon.data2urlencode(self.username, is_post=True, **d_item)

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

    def _action_data(self, var):
        ac_map = {self.PARAM_CGW_1: list(range(1, 5)), self.PARAM_CGW_4: list(range(11, 17))}

        for item in load_data():
            if item["p7"] in ac_map[var]:
                yield item


class iClient(PostHeaders, ClientWebService, ClientWebApi):
    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.username)


def load_data():
    KEY, IV = os.environ.get("common_key"), os.environ.get("common_iv")
    client = requests.session()
    client.headers = HTTPHeaders.get()

    def _base_info_1():
        url = "http://www.iabe.cn/EcarServer/LoadBaseData.aspx"
        content = dict()

        method = CoreCommon.encrypt("3", key=KEY, iv=IV)
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

        method = CoreCommon.encrypt("4", key=KEY, iv=IV)
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
