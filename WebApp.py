#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import functools
import hashlib
import logging
import random
import re
import sqlite3
import threading
import time
import urllib
from HTMLParser import HTMLParser
from collections import defaultdict
from datetime import (datetime, timedelta)
from urlparse import (urlparse, parse_qs)

import requests
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.queues
import tornado.template
import tornado.web
from Crypto.Cipher import DES

import Config

try:
    import cv2
except ImportError as e:
    pass

tp = lambda t: Config.TEMPLATES_DIR + t

class URLSeeker(HTMLParser):
    def __init__(self, check_dom=(), get_vs_code=False, get_process=False):
        """
        :param check_dom: tag, attr, value
        """
        HTMLParser.__init__(self)
        self._tag, self._attr, self._value = check_dom
        self.data = ""
        self.___find__ = False
        self.__is_vs_code = get_vs_code
        self.get_process = get_process

    def handle_starttag(self, tag, attrs):
        gid = dict(attrs).get(self._attr, "")
        if all([gid.find(self._value) > -1, tag == self._tag]):
            self.___find__ = True

            if self.__is_vs_code and (not hasattr(self, "VS_code")):
                setattr(self, "VS_code", dict(attrs).get('value'))

    def handle_data(self, data):
        if self.___find__:
            self.data += data.strip()
            # if self.get_process:
            # self.data += data
            # else:
            # self.data = data

    def handle_endtag(self, tag):
        if tag == self._tag:
            self.___find__ = False


class Common(object):
    def __init__(self):
        super(Common, self).__init__()

    @staticmethod
    def encrypt(plaintext, key="", iv="", **kwargs):
        # TODO: Enter the key &iv
        __key__ = key
        __iv__ = iv

        if not isinstance(plaintext, str):
            plaintext = str(plaintext)

        pad_num = 8 - (len(plaintext) % 8)
        for i in range(pad_num):
            plaintext += chr(pad_num)
        cipher = DES.new(__key__, DES.MODE_CBC, __iv__)
        text = cipher.encrypt(plaintext)

        return base64.b64encode(text)

    @staticmethod
    def decrypt(plaintext, key="", iv="", **kwargs):
        # TODO: Enter the key &iv
        __key__ = key
        __iv__ = iv

        try:
            enc_text = base64.b64decode(plaintext)
        except ValueError:
            enc_text = urlparse.unquote(base64.b64decode(plaintext))

        cipher = DES.new(__key__, DES.MODE_CBC, __iv__)
        text = cipher.decrypt(enc_text)

        return re.sub(r'[\x01-\x08]', '', text)

    @staticmethod
    def encrypt_ws(plaintext, key="", iv="", **kwargs):
        from datetime import date as dt_date

        if (not key) and (not iv):
            # TODO: Enter the key &iv

            _ = dt_date.today().day
            _ = _ < 10 and "%02d" % _ or _
            key, iv = key + str(_), iv + str(_)

        if not isinstance(plaintext, str):
            plaintext = str(plaintext)

        pad_num = 8 - (len(plaintext) % 8)
        for i in range(pad_num):
            plaintext += chr(pad_num)
        cipher = DES.new(key, DES.MODE_CBC, iv)
        text = cipher.encrypt(plaintext)

        return base64.b64encode(text)

    @staticmethod
    def decrypt_ws(plaintext, key="", iv="", **kwargs):
        from datetime import date as dt_date
        _ = dt_date.today().day
        _ = _ < 10 and "%02d" % _ or _
        if (not key) and (not iv):
            # TODO: Enter the key &iv
            key, iv = key + str(_), iv + str(_)

        try:
            enc_text = base64.b64decode(plaintext)
        except ValueError:
            enc_text = urlparse.unquote(base64.b64decode(plaintext))

        cipher = DES.new(key, DES.MODE_CBC, iv)
        text = cipher.decrypt(enc_text)

        return re.sub(r'[\x01-\x08]', '', text)

    @staticmethod
    def data2urlencode(acc, p5, p7, p8, p9, is_post=False):
        encrypt = Common.encrypt
        _kw = {
            "method": encrypt("15"),
            "param1": encrypt(acc),
            "param2": encrypt(acc),
            "param3": "ntBzt0a1Hd2QVg0ZMLYOhnwffVXYdAitWnrY+MEt2fs=",
            "param4": encrypt("100"),
            "param5": encrypt(p5 / 2),
            "param6": encrypt("1"),
            "param7": encrypt(p7),
            "param8": encrypt(p8),
            "param9": encrypt(p9),
            "param10": encrypt(random.randint(0, 30000)),
        }

        if is_post:
            return _kw
        return urllib.urlencode(_kw)

    @classmethod
    def data2urldecode(self, text, single=False):
        if single:
            print self.decrypt(text)
        else:
            r = urlparse("http://localhost?" + text)
            d = parse_qs(r.query)
            for k, v in sorted(d.items(), key=lambda x: x[0]):
                print "the key: %s " % k + "decrypt: %s" % self.decrypt(v[0])

    @staticmethod
    def char_format(param, var):
        if var == "unm":
            return param.lower().strip()
        elif var == "pwd":
            return str(param).strip()

    @staticmethod
    def char_transform(words, coding="utf-8", to_str=False):
        """
        :param to_str: 是否转换成str。默认返回utf8
        """
        if to_str:
            if isinstance(words, str):
                return words

            if isinstance(words, unicode):
                try:
                    return words.encode(coding)
                except UnicodeEncodeError:
                    return Common.char_transform(words.encode("gbk"), to_str=True)

        if isinstance(words, unicode):
            return words

        if isinstance(words, str):
            try:
                return words.decode(coding)
            except UnicodeDecodeError:
                return Common.char_transform(words.decode("gbk"))

    @staticmethod
    def to_bool(value):
        if str(value).lower() in ("yes", "y", "true", "t", "1", "on"):
            return True
        elif str(value).lower() in ("no", "n", "false", "f", "0", "0.0", "off", "", " ", "none", "[]", "{}"):
            return False
        raise Exception('Invalid value for boolean conversion: ' + str(value))


class HeaderInterface:
    DEFAULT_HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:45.0) Gecko/20100101 Firefox/45.0"}
    SUB_DOMAIN = {"fs": "www", "jm": "www1", "sg": "www", "cz": "hebei", "yl": "yl"}

    WS_HEADER_REFERER = {
        "fs": "http://www.iabe.cn/WebSiteFS/student/SimulatedExamination1_20140528.swf?v=444222222222222222222345&data=13-8-2",
        "jm": "http://www1.iabe.cn/student/SimulatedExamination1_20140528.swf?v=444222222222222222222345&data=13-8-2",
        "sg": "http://www.iabe.cn/WebSiteSG/student/SimulatedExamination1_20140528.swf?v=444222222222222222222345&data=13-8-2",
        "yl": "http://yl.iabe.cn/student/SimulatedExamination1_20140528.swf?v=444222222222222222222345&data=13-8-2",
    }

    def __init__(self, username=None, zone=None):
        """
        :param zone: Only Pick In: fs/jm/sg/cz/yl
        """
        prefix = ""

        if username:
            _ = username.lower().strip()
            for _prefix in self.SUB_DOMAIN.keys():
                if _.startswith(_prefix):
                    prefix = _prefix
                    break
        elif zone:
            prefix = Common.char_format(zone, var="unm")

        if not prefix:
            raise Exception("Unable To Init Header. Please Provide Username or zone.")

        self.zone = prefix
        self.prefix = self.SUB_DOMAIN[prefix]

    def choose_header(self, var):
        """
        :param var: cgw/ws/exchange
        :return: a dict of requests headers
        """
        if var == "ad":
            return self.ad_headers()
        elif var == "cgw":
            return self.cg_headers()
        elif var == "ws":
            return self.ws_headers()
        elif var == "exchange":
            return self.ex_headers()

    def ad_headers(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Win 9x 4.90; SG; rv:1.9.2.4) Gecko/20101104 Netscape/9.1.0"}
        headers = self.__fake_ip__(headers)

        return headers

    def cg_headers(self):
        headers = {"X-Requested-With": "ShockwaveFlash/22.0.0.192", "Content-Type": "application/x-www-form-urlencoded", }
        headers = self.__fake_ip__(headers)

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.prefix,
            "Referer": "http://%s.iabe.cn/ecar/ProjectEcar.swf?v=123456" % self.prefix,
        }

        headers.update(self.DEFAULT_HEADER, **swf_headers)
        return headers

    def ws_headers(self):
        headers = {"X-Requested-With": "ShockwaveFlash/22.0.0.192", "Content-Type": "text/xml; charset=utf-8", }

        swf_headers = {
            "Origin": "http://%s.iabe.cn" % self.prefix,
            "Referer": self.WS_HEADER_REFERER.get(self.zone, "http://%s.iabe.cn" % self.prefix),
        }

        headers.update(self.DEFAULT_HEADER, **swf_headers)
        return headers

    def ex_headers(self):
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://%s.iabe.cn/public/Index.aspx?area=8" % self.prefix,
        }

        headers.update(self.DEFAULT_HEADER)
        return headers

    @staticmethod
    def __fake_ip__(headers):
        randint = random.randint
        modify_list = [
            "Via", "CLIENT_IP", "X-Real-Ip", "REMOTE_ADDR", "REMOTE_HOST", "X-Forwarded-For", "X_FORWARDED_FOR"
        ]
        random_ip = lambda: "%s.%s.%s.%s" % (randint(1, 255), randint(0, 255), randint(0, 255), randint(1, 255))
        headers.update({k: random_ip() for k in modify_list})
        return headers


class DBInterface(object):
    class MetaStyle(object):
        # TODO:这里应该尝试支持 sqlite3.Row的用法, 即: obj[x]
        __metadata___ = defaultdict(dict)
        # __slots__ =[]

        # datas = __metadata___
        def __init__(self, data):
            if isinstance(data, sqlite3.Row):
                _data = zip(data.keys(), list(data))
                for k, v in _data:
                    self.__metadata___[k] = v

            elif isinstance(data, dict):
                for k, v in data.items():
                    self.__metadata___[k] = v

            self.__dict__.update(self.__metadata___)
            self.username = self.__metadata___.get(u"username", u"unset")

        def get(self, k, d=None):
            return self.__metadata___.get(k, d)

        def __getitem__(self, item):
            return self.__metadata___.get(item, None)

        def __setitem__(self, key, value):
            self.__metadata___[key] = value
            self.__dict__.update({key: value})

        # def __repr__(self):
        #     return '<{0}: {1}> at {2}'.format(type(self).__name__, self.username, hex(id(self)))

    def __init__(self, db_path, var="sqlite"):
        self.var = var
        self.db_path = db_path


    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def connect_db(self, dict_factory=False, **kwargs):
        _db = sqlite3.connect(self.db_path)
        if dict_factory:
            _db.row_factory = self.dict_factory
        else:
            _db.row_factory = sqlite3.Row

        return _db

    def query_db(self, query, args=(), one=False, **kwargs):
        """
        :param query: query sql
        :param args: query params
        :param one: return one result
        :param kwargs: in_meta, choose "True/ False", default: True
        :return: + return a list with "sqlite3.Row Object/ dict Object/ MetaStyle Object", default: sqlite3.Row Object
                 |- sqlite3.Row Object: dict_factory=False.
                 |- dict Object: dict_factory=True.
                 |- MetaStyle Object: in_meta=True.
        """
        conn = kwargs.get("in_dict") and self.connect_db(dict_factory=True, **kwargs) or self.connect_db(**kwargs)
        cur = conn.cursor()

        try:
            cur.execute(query, args)
            rv = cur.fetchall()
            if kwargs.get("in_meta"):  # default: True
                rv = [self.MetaStyle(item) for item in rv]

            return (rv[0] if rv else None) if one else rv

        except Exception as e:
            # logging.error(traceback.print_exception())
            return dict(error_msg=e.message, rtn_code=-1)

        finally:
            conn.close()

    def write_db(self, query, args=(), **kwargs):
        conn = self.connect_db(**kwargs)
        cur = conn.cursor()

        try:
            if isinstance(args, tuple): args = [args]

            cur.executemany(query, args)
            conn.commit()

            return dict(rtn_code=1, rv=1)

        except Exception as e:
            # logging.error(traceback.print_exception())
            return dict(error_msg=e.message, rtn_code=-1)

        finally:
            conn.close()

    def exec_schema_sql(self, schema_sql, **kwargs):
        conn = self.connect_db(**kwargs)
        cur = conn.cursor()

        try:
            with open(schema_sql, mode="r") as rf:
                cur.executescript(rf.read())
                conn.commit()
        finally:
            conn.close()


class LogerInterface(logging.Logger):
    def __init__(self, log_var="db", log_name="root", level="debug", log_console=False, **kwargs):
        level_list = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR}
        self.log_var = log_var
        self.log_name = "log_" + log_name
        self.log_level = level_list[level]
        self.log_console = log_console

        super(LogerInterface, self).__init__(name=self.log_name, level=self.log_level)

        if log_var == "db":
            dh = self.DBHandler(g_DB)
            dh.setFormatter(logging.Formatter("%(name)s, %(funcName)s: %(asctime)s %(levelname)-8s %(message)s"))
            self.addHandler(dh)
        else:
            # TODO: log in file
            pass

        if self.log_console:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(name)s, %(funcName)s: %(asctime)s %(levelname)-8s %(message)s"))
            self.addHandler(handler)

    class DBHandler(logging.Handler):
        def __init__(self, db_obj):
            self.db_obj = db_obj
            logging.Handler.__init__(self)
            # super(self.DBHandler, self).__init__()

        def emit(self, record):
            sql = "INSERT INTO loger (type, logerName, create_date, content) VALUES (?, ?, ?, ?);"
            self.format(record)
            self.db_obj.write_db(sql, args=(record.levelname, record.name, record.asctime, record.message))

        def close(self):
            logging.Handler.close(self)


class BaseInterface(LogerInterface, Common):
    def __init__(self, username, password, log_level="debug", **kwargs):
        if not kwargs.get("level", ""):
            kwargs["level"] = log_level

        self.username = self.char_format(username, "unm")
        self.password = self.char_format(password, "pwd")

        super(Common, self).__init__()
        super(BaseInterface, self).__init__(log_name=self.username, **kwargs)

        # 初始化 地区信息
        self.zone = self._initialize()
        self.ClsHeader = HeaderInterface(username=self.username)

        # 初始化 Requests信息
        self.session = requests.Session()
        self.is_login = False

    def login(self):
        def viewstate_code():
            """"通过正则方式获取ASP.NET的 __VIEWSTATE"""
            _code = ""
            rule = re.compile('(?<=ue=")[0-9a-zA-Z+/]*(?=")')

            urls = [
                (1, "http://www.iabe.cn/StaticPage/subject/comments.aspx"),
                (2, "http://www.iabe.cn/public/default.aspx"),
            ]
            for idx, uri in urls:
                _resp = requests.get(uri, headers=HeaderInterface.DEFAULT_HEADER)
                if idx == 1:
                    _code = re.findall(rule, _resp.text)[-1]
                elif idx == 2:
                    _code = re.findall(rule, _resp.text)[0]

                if _code:
                    return _code

            logging.warning(u"[!!] Get Code Failed.")
            raise requests.ConnectionError

        def viewstate_code_2():
            """"通过HTMLParser方式获取ASP.NET的 __VIEWSTATE"""
            urls = [
                "http://www.iabe.cn/public/Index.aspx?area=8",
                "http://www.iabe.cn/public/default.aspx",
                "http://www.iabe.cn/StaticPage/subject/comments.aspx",
                ]
            for uri in urls:
                gt = requests.get(uri, headers=self.ClsHeader.DEFAULT_HEADER)
                url_seeker = URLSeeker(("input", "id", "__VIEWSTATE"), get_vs_code=True)
                url_seeker.feed(gt.text)
                _code = getattr(url_seeker, "VS_code", None)
                if _code:
                    return _code
                else:
                    logging.warning(u"[!!] Get Code Failed.")
            raise requests.ConnectionError

        username = self.username
        password = self.password
        default_login_uri = "http://www.iabe.cn/public/default.aspx"

        retry = 3
        while retry > 0:
            try:
                code = viewstate_code_2()
                payload = {
                    "__VIEWSTATE": code,
                    "ctl00$ContentPlaceHolder1$LoginView1$Login1$UserName": username,
                    "ctl00$ContentPlaceHolder1$LoginView1$Login1$Password": password,
                    "ctl00$ContentPlaceHolder1$LoginView1$Login1$BtnLogin": ""
                }
                self.session.post(default_login_uri, data=payload, headers=self.ClsHeader.DEFAULT_HEADER)

                payload = {"userName": username, "password": password}
                self.session.post(self.LOGIN_URI, data=payload, headers=self.ClsHeader.DEFAULT_HEADER)

                assert username in self.session.cookies.keys()
                self.is_login = True
                self.info(u"登录成功...")
                cookies = self.encrypt(self.session.cookies, key="+cookIes", iv="+cookIes")
                self.debug(u"登录后的Cookie: %s\n" % cookies)

                return self.session

            except AssertionError:
                retry -= 1
                self.error(u"[!!!] 登录失败，或密码错误。\n")

            except requests.ConnectionError as e:
                retry -= 1
                self.info("More info: %s\n" % repr(e))
                self.warning(u"[!!] 网络连接异常, Retrying...%s\n" % (3 - retry))

        raise Exception(self.error(u"[!!!] 多次登录不成功，退出。"))

    def _initialize(self):
        """
        :POST_URI: 闯关王地址
        :LOGIN_URI: 登录地址
        :EXCHANGE_URI: 兑换积分地址
        :WEBSERVICE_URI: WS服务地址
        :SCHEDULE_URL: 查看进度地址
        """
        def init_fs():
            init_data = dict(
                POST_URI="http://www.iabe.cn/EcarServer/InsertPoints.aspx",
                LOGIN_URI="http://www.iabe.cn/public/default.aspx",
                EXCHANGE_URI="http://www.iabe.cn/WebSiteFS/ExchangeHours.ashx?type=3",
                WEBSERVICE_URI="",  # undefined
                SCHEDULE_URL="http://www.iabe.cn/WebSiteFS/student/Info_trainingSchedule.aspx"
            )
            return init_data

        def init_jm():
            init_data = dict(
                POST_URI="http://www1.iabe.cn/EcarServer/InsertPoints.aspx",
                LOGIN_URI="http://www1.iabe.cn/public/default.aspx",
                EXCHANGE_URI="http://www.iabe.cn/ExchangeHours.ashx?type=3",
                WEBSERVICE_URI="",  # undefined
                SCHEDULE_URL="http://www1.iabe.cn/student/Info_trainingSchedule.aspx"
            )
            return init_data

        def init_sg():
            init_data = dict(
                POST_URI="http://www.iabe.cn/EcarServer/InsertPoints.aspx",
                LOGIN_URI="http://www.iabe.cn/public/default.aspx",
                EXCHANGE_URI="http://www.iabe.cn/WebSiteSG/ExchangeHours.ashx?type=3",
                WEBSERVICE_URI="",  # undefined
                SCHEDULE_URL="http://www.iabe.cn/WebSiteSG/student/Info_trainingSchedule.aspx"
            )
            return init_data

        def init_hb():
            """由于兑换需要拍照。估计需要使用 WebService方式进行"""
            init_data = dict(
                POST_URI="http://hebei.iabe.cn/EcarService/InsertPoints.aspx",
                LOGIN_URI="http://hebei.iabe.cn/public/default.aspx",
            )
            return init_data

        def init_yl():
            init_data = dict(
                POST_URI="http://yl.iabe.cn/EcarServer/InsertPoints.aspx",
                LOGIN_URI="http://yl.iabe.cn/public/default.aspx",
                EXCHANGE_URI="http://yl.iabe.cn/ExchangeHours.ashx?type=3",
                WEBSERVICE_URI="",  # rm
            )
            return init_data

        # 进行地区服务地址初始化
        choose_unit = {"fs": init_fs, "jm": init_jm, "cz": init_hb, "yl": init_yl, "sg": init_sg}
        for prefix in choose_unit.keys():
            if self.username.startswith(prefix):
                for k, v in choose_unit[prefix]().items():
                    setattr(self, k, v)
                return prefix

        return Exception(self.error(u"[!!!] Unable to initialize the information."))


class DetectFaceInterface(object):
    def __init__(self):
        super(DetectFaceInterface, self).__init__()


class IabeWebService(BaseInterface):
    # TODO: use suds to replace this class
    base = """
    <?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            {body}
        </soap:Envelope>
    """

    def __init__(self, username, password="", **kwargs):
        super(IabeWebService, self).__init__(username, password, **kwargs)

        server_urls = {
            # undefined
        }

        for prefix in server_urls.keys():
            if (not hasattr(self, "WEBSERVICE_URI")) and self.username.startswith(prefix):
                self.WEBSERVICE_URI = server_urls[prefix]
                return

        try:
            assert hasattr(self, "WEBSERVICE_URI")
        except AssertionError:
            raise Exception(self.error(u"[!!!] 操作失败。未能初始化服务，用户名错误或该地区不被支持。"))

    @staticmethod
    def __payload_get_random100timustring__(dct="C1"):
        body = """ <soap:Body>
            <GetRandom100TiMuString xmlns="http://tempuri.org/">
              <allowDriveCarType>%(dct)s</allowDriveCarType>
            </GetRandom100TiMuString>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip() % {"dct": dct}

    @staticmethod
    def __payload_get_xueyuanjibenxinxitowebserver__(username):
        body = """ <soap:Body>
            <GetXueYuanJiBenXinXiToWebServer xmlns="http://tempuri.org/">
              <XueHao>%(username)s</XueHao>
            </GetXueYuanJiBenXinXiToWebServer>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip() % {"username": username}

    @staticmethod
    def __payload_get_traintimepassedtoday__(ls_code):
        body = """ <soap:Body>
            <GetTrainTimePassedToday xmlns="http://tempuri.org/">
              <XueYuanLiuShuiHao>%(ls_code)s</XueYuanLiuShuiHao>
            </GetTrainTimePassedToday>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip() % {"ls_code": ls_code}

    @staticmethod
    def __payload_hb_shujushangchuanjiekou_xuexirizhi__():
        body = """ <soap:Body>
            <Hb_ShuJuShangChuanJieKou_XueXiRiZhi xmlns="http://tempuri.org/">
              <XueYuanLiuShuiHao>%(ls_code)s</XueYuanLiuShuiHao>
              <XueHao>%(x_code)s</XueHao>
              <PassWord>%(password)s</PassWord>
              <TiMuLiuShuiHao>%(timuls_code)s</TiMuLiuShuiHao>
              <TrueOrFalse>%(bool)s</TrueOrFalse>
              <BeiZhu>%(mark)s</BeiZhu>
              <imagestring></imagestring>
              <imagestring2></imagestring2>
              <imagestring3></imagestring3>
              <subject></subject>
            </Hb_ShuJuShangChuanJieKou_XueXiRiZhi>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip()

    @staticmethod
    def __payload_get_studentsubjectinfobycardnum__(username):
        body = """ <soap:Body>
            <GetStudentsubjectInfoByCardNum xmlns="http://tempuri.org/">
              <xuehao>%(username)s</xuehao>
            </GetStudentsubjectInfoByCardNum>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip() % {"username": username}

    @staticmethod
    def __payload_ZQ_XueXiRiZhiToExamThree__():
        body = """ <soap:Body>
            <ZQ_XueXiRiZhiToExamThree xmlns="http://tempuri.org/">
              <XueYuanLiuShuiHao>%(ls_code)s</XueYuanLiuShuiHao>
              <BeiZhu>%(mark)s</BeiZhu>
            </ZQ_XueXiRiZhiToExamThree>
          </soap:Body> """

        payload = IabeWebService.base.format(body=body)
        return payload.strip()

    def func_getrandom100timustring(self, dct="C1", **kwargs):
        """ GetRandom100TiMuString 随机抽取的100道题目"""
        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/GetRandom100TiMuString"})
        kwargs.get("header", None) and header.update(kwargs["header"])

        payload = self.__payload_get_random100timustring__(dct)

        # resp = requests.post(self.WEBSERVICE_URI, data=payload, headers=header)

    def func_gettraintimepassedtoday(self, ls_code, **kwargs):
        """当天已训练学时"""
        time_rule = re.compile(r'(?<=<GetTrainTimePassedTodayResult>)[0-9.]+(?=</GetTrainTimePassedTodayResult>)')

        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/GetTrainTimePassedToday"})
        kwargs.get("header", None) and header.update(kwargs["header"])

        payload = self.__payload_get_traintimepassedtoday__(ls_code)

        resp = requests.post(self.WEBSERVICE_URI, data=payload, headers=header)
        _time = re.findall(time_rule, resp.text)[0]
        return {"today_trains": _time}

    def func_getxueyuanjibenxinxitowebserver(self, **kwargs):
        """查看学员基本信息字段"""
        ls_rule = re.compile(r'(?<=&lt;XueYuanLiuShuiHao&gt;)[0-9]+(?=&lt;/XueYuanLiuShuiHao&gt;)')

        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/GetXueYuanJiBenXinXiToWebServer"})
        kwargs.get("header", None) and header.update(kwargs["header"])

        payload = self.__payload_get_xueyuanjibenxinxitowebserver__(self.username)

        resp = requests.post(self.WEBSERVICE_URI, data=payload, headers=header)
        ls_code = re.findall(ls_rule, resp.text)

        try:
            assert len(ls_code) > 0
            self.debug(u"得到学员流水号: %s\n" % ls_code[0])
            return ls_code[0]

        except AssertionError:
            self.warning(u"Get LiuShuiHao Failed. Check The Length Of Your Username Or zone.")

    def func_hb_shujushangchuanjiekou_xuexirizhi(self, sessionObj=None, **kwargs):
        result_rule = re.compile(r'(?<=XueXiRiZhiResult>)\w+(?=</Hb_)')

        """"数据上传接口_河北记录做题记录(注意使用学员流水号+学号，可上传3张相片)"""
        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/Hb_ShuJuShangChuanJieKou_XueXiRiZhi"})
        kwargs.get("header", None) and header.update(kwargs["header"])

        try:
            assert all(map(lambda k: k in kwargs, ["ls_code", "x_code", "password", "timuls_code", "bool", "mark"]))
        except AssertionError:
            self.error(u"调用上传分数接口时，参数不足。")
            raise Exception("Operation Failed! Exit Exception.")
            # sys_exit()

        payload = self.__payload_hb_shujushangchuanjiekou_xuexirizhi__() % kwargs

        if sessionObj:
            resp = sessionObj.post(self.WEBSERVICE_URI, data=payload, headers=header)
        else:
            resp = requests.post(self.WEBSERVICE_URI, data=payload, headers=header)

        result = re.findall(result_rule, resp.text)
        if result:
            return result[0]

    def func_getstudentsubjectinfobycardnum(self, **kwargs):
        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/GetStudentsubjectInfoByCardNum"})
        kwargs.get("header", None) and header.update(kwargs["header"])

        payload = self.__payload_get_studentsubjectinfobycardnum__(self.username)

        resp = requests.post(self.WEBSERVICE_URI, data=payload, headers=header)

        return resp.text.replace("&lt;", "<").replace("&gt;", ">")

    def func_zq_xuexirizhitoexamthree(self, sessionObj=None, **kwargs):
        header = self.ClsHeader.choose_header("ws")
        header.update({"SOAPAction": "http://tempuri.org/ZQ_XueXiRiZhiToExamThree"})

        _zone = kwargs.get("zone", "")
        _map = {
            "sg": "http://www.iabe.cn/WebSiteSG/public/SimulatedExamination3_20140613.swf?v=1.1",
            "fs": "http://www.iabe.cn/WebSiteFS/public/SimulatedExamination3_20140613.swf?v=1.1",
        }
        header.update({"Referer": _map.get(_zone, _map["fs"])})
        kwargs.get("header", None) and header.update(kwargs["header"])

        payload = self.__payload_ZQ_XueXiRiZhiToExamThree__() % kwargs

        try:
            assert all(map(lambda k: k in kwargs, ["ls_code", "mark"]))
        except AssertionError:
            raise self.error(u"参数不足")

        if sessionObj:
            sessionObj.post(self.WEBSERVICE_URI, data=payload, headers=header)
        else:
            requests.post(self.WEBSERVICE_URI, data=payload, headers=header)

        return "true"  # TODO: Need to modify in reality result


class Iabe(BaseInterface):
    def __init__(self, username, password, init_webservice=True, **kwargs):
        super(Iabe, self).__init__(username, password, **kwargs)
        self.WebService = IabeWebService(self.username, self.password, **kwargs)

    def call_cgw(self, part=None, var="cg_old", g_retry=3, **kwargs):
        """
        :param part: Default: map(str, [1, 2, 3, 4, 11, 12, 13, 15, 16])
        :param var: choose in [cgw1, cgw4, cg_old]. Default: cg_old
        """
        __msg_ = u" 准备执行'闯关任务: %s' " %  var
        self.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.error(u"[!!!] 出现异常。")
            return

        part = part and map(str, list(part)) or map(str, [1, 2, 3, 4, 11, 12, 13, 15, 16])
        _keys, _values = self.__CG_choose__(var)
        _zip = [dict(zip(_keys, item)) for item in _values]
        action_data = [item for item in _zip if str(item["p7"]) in part]

        if not self.is_login:
            self.login()
            return self.call_cgw(part=part, var=var, g_retry=g_retry - 1, **kwargs)

        for idx, d_item in enumerate(action_data):
            _data = self.data2urlencode(self.username, is_post=True, **d_item)
            retry = 3
            while retry > 0:
                try:
                    self.session.post(self.POST_URI, data=_data, headers=self.ClsHeader.choose_header("cgw"))
                    break
                except requests.exceptions.ConnectionError:
                    retry -= 1
                except KeyboardInterrupt:
                    exit(0)

            percent = round(float(idx + 1) / len(action_data) * 100, 2)
            self.info(u"当前进度: %s%%: " % percent + u"第%(p7)s章 第%(p8)s节 第%(p9)s条目" % d_item)
            self.debug(repr(d_item) + u"\n已完成{0}题，准备休息{1}秒...".format(d_item["p5"] / 2, d_item["p5"] / 2 * 4))
            time.sleep(d_item["p5"] / 2 * 4)

        self.info(u"闯关已完成...")
        return

    def call_mnks(self, var="mn_old", g_retry=3, lscode="", **kwargs):
        """
        :param var: choose in "mn_old, mnks4". Default: mn_old
        """
        __msg_ = u" 准备执行'模拟任务: %s' " % var
        self.info(__msg_.center(30, "="))

        if g_retry < 0:
            self.error(u"[!!!] 出现异常。")
            return

        client = self.WebService
        ls_code = lscode or self.call_get_ls_code(**kwargs)
        resp_code = ""

        if not self.is_login:
            self.login()
            return self.call_mnks(var=var, g_retry=g_retry - 1, lscode=lscode, **kwargs)

        if var == "mn_old":
            data = {
                "ls_code": self.encrypt_ws(ls_code),
                "x_code": self.encrypt_ws(self.username),
                "password": self.encrypt_ws(self.password),
                "timuls_code": self.encrypt_ws("0"),
                "bool": self.encrypt_ws("T"),
                "mark": self.encrypt_ws(random.randint(90, 100)),
            }

            resp_code = client.func_hb_shujushangchuanjiekou_xuexirizhi(ssionObj=self.session, **data)

        if var == "mnks4":
            data = {
                "ls_code": self.encrypt(ls_code),
                "mark": self.encrypt(random.randint(90, 100)),
            }
            data.update(zone=self.zone)
            resp_code = client.func_zq_xuexirizhitoexamthree(ssionObj=self.session, **data)

        if resp_code == "true":
            self.info(u"已完成一套！10秒后自动退出...\n\n")
        else:
            self.warning(u"[!!] 返回结果: %s，请手动检查任务情况，或该任务已达到上限。\n\n" % repr(resp_code))

        time.sleep(10)

    def call_exchange(self):
        self.info(u" 准备执行'兑换任务' ".center(30, "="))
        if self.zone in ["cz"]:
            self.warning(u"此地区兑换功能有待完善。")
            return u"此地区兑换功能有待完善。"

        if not self.is_login:
            self.login()
            return self.call_exchange()

        resp = self.session.get(self.EXCHANGE_URI, headers=self.ClsHeader.choose_header("exchange"))
        if resp.status_code < 400:
            try:
                response = resp.json()
                exchange_rv = response["ExChange"][0]["result"]
                self.info(u"兑换结果: %s\n" % exchange_rv)
                return exchange_rv
            except ValueError:
                self.warning(u"[!!] 兑换失败。未知异常，请重试。")
        return u"[!!] 兑换失败。未知异常，请重试。"

    def call_get_ls_code(self, **kwargs):
        self.info(u" 准备执行'查询流水号' ".center(30, "="))

        client = self.WebService
        return client.func_getxueyuanjibenxinxitowebserver(**kwargs)

    def call_get_today_trains(self, ls_code="", result=u"不支持"):  # TODO: Check Run Error !!!
        """需要配合IabeWebservice"""
        client = self.WebService
        self.info(u" 准备执行'查询学时情况' ".center(30, "="))
        if self.zone not in ["cz"]:
            if not ls_code:
                ls_code = client.func_getxueyuanjibenxinxitowebserver()

            _trains_time = client.func_gettraintimepassedtoday(ls_code)
            result = _trains_time.get("today_trains")

        self.info(u"今天已学 %s 小时" % result)
        return dict(rv=result)

    def call_get_learn_progress(self):
        self.info(u" 准备执行'查询学习进度情况' ".center(30, "="))

        if not self.is_login: self.login()
        client = self.session
        req = client.get(self.SCHEDULE_URL, headers=self.ClsHeader.DEFAULT_HEADER)
        data = ""
        for item in [("dl", "class", "traningResul")]:
            url_seeker = URLSeeker(item)
            url_seeker.feed(req.text)
            data += url_seeker.data

        return dict(rv=u"学习进度: " + data)

    def call_get_learned_cgw(self):
        self.info(u" 准备执行'查询闯关情况' ".center(30, "="))

        if not self.is_login: self.login()
        client = self.session
        gt = client.get("http://www.iabe.cn/public/Index.aspx?area=8", headers=self.ClsHeader.DEFAULT_HEADER)
        url_seeker = URLSeeker(("a", "id", "ctl00_ContentPlaceHolder1_ctl00_labYiHouDeXueShi"))
        url_seeker.feed(gt.text)
        return {"data": u"闯关王: " + url_seeker.data}

    def call_get_learned_mnks(self):
        self.info(u" 准备执行'查询模拟情况' ".center(30, "="))

        if not self.is_login: self.login()
        client = self.session
        gt = client.get("http://www.iabe.cn/public/Index.aspx?area=3", headers=self.ClsHeader.DEFAULT_HEADER)
        url_seeker = URLSeeker(("span", "id", "ctl00_ContentPlaceHolder1_ctl00_labHuoDeXueShi"))
        url_seeker.feed(gt.text)
        return {"data": u"模拟考试: " + url_seeker.data}

    def call_get_user_stage_info(self):  # TODO: Check Run Error !!!
        self.info(u" 准备执行'查询学习阶段情况' ".center(30, "="))

        client = self.WebService
        return client.func_getstudentsubjectinfobycardnum()

    _keys = ["p7", "p8", "p9", "p5"]
    _values = []

    def __CG_old__(self):
        self._p7, self._p8, self._p9 = 1, 1, 1

        # 第1章
        self.__CG_iter__([104, 14, 28, 68, 44, 54, 92, 40, 18, 40, 26, 42, 36])
        self.__CG_iter__([28, 16])
        self.__CG_iter__([30, 10])
        self.__CG_iter__([22, 2, 18, 12, 4])
        self.__CG_iter__([16, 10, 24, 10, 6, 4, 12, 4, 10, 16, 6, 54, 18, 14, 10, 10, 14])
        self.__CG_iter__([20, 8, 6, 4, 6])

        # 第2章
        self._p7 = 2
        self.__CG_iter__([16, 14, 10, 10, 14, 10, 4])
        self.__CG_iter__([200, 82, 104, 102, 10])
        self.__CG_iter__([84, 54, 16])
        self.__CG_iter__([6, 4, 6, 4, 6, 4, 4, 2])

        # 第3章
        self._p7 = 3
        self.__CG_iter__([246, 28, 22, 4, 30, 86, 26, 18])
        self.__CG_iter__([84, 30, 6, 10, 20, 6, 6, 12])

        # 第4章
        self._p7 = 4
        self._p9 = 85  # patch 跳过84
        self.__CG_iter__([22, 12, 12, 24, 10, 14, 10, 8, 10, 12, 46])
        self.__CG_iter__([6, 2, 8, 6, 6, 2, 8, 12, 18])
        self.__CG_iter__([2, 16, 18, 6])

    def __CG_part1__(self):
        self._p7, self._p8, self._p9 = 1, 1, 1

        # 第1章
        self.__CG_iter__([60, 60, 80])
        self.__CG_iter__([50])

        # 第2章
        self._p7 = 2
        self.__CG_iter__([60, 60, 60, 60, 60, 60, 60, 60, 100, 136])
        self.__CG_iter__([80, 80, 80, 80, 80, 80, 80, 80, 120, 124])
        self.__CG_iter__([60, 62])

        # 第3章
        self._p7 = 3
        self.__CG_iter__([48])
        self.__CG_iter__([78])
        self.__CG_iter__([102])

        # 第4章
        self._p7 = 4
        self.__CG_iter__([72])

    def __CG_part4__(self):
        self._p7, self._p8, self._p9 = 15, 18, 46

        self.__CG_iter__([20])
        self.__CG_iter__([12])
        self.__CG_iter__([50, 50])
        self.__CG_iter__([60, 60, 60, 60, 60, 60, 58])

        self._p7 = 16
        self.__CG_iter__([60, 64])  # p8 = 22
        self.__CG_iter__([60, 72])
        self.__CG_iter__([36])
        self.__CG_iter__([56])

        self._p7, self._p8, self._p9 = 11, 29, 70

        self.__CG_iter__([52])  # p9 = 70
        self.__CG_iter__([50, 58])
        self.__CG_iter__([58])
        self.__CG_iter__([80, 88])
        self.__CG_iter__([60, 70])

        self._p7 = 12
        self.__CG_iter__([60, 82])
        self.__CG_iter__([74])

        self._p7 = 13
        self.__CG_iter__([60])
        self.__CG_iter__([36])

    def __CG_choose__(self, var=""):
        var = var or "cg_old"
        ac_map = {"cgw1": self.__CG_part1__, "cgw4": self.__CG_part4__, "cg_old": self.__CG_old__}
        ac_map[var]()
        return self._keys, self._values

    def __CG_iter__(self, *arg):
        length = len(*arg)
        self._values += zip(
            [self._p7] * length,
            [self._p8] * length,
            range(self._p9, self._p9 + length),
            *arg
        )

        self._p8 += 1
        self._p9 += length


class AccountInterface(Iabe):
    def __init__(self, username, password, **kwargs):
        super(AccountInterface, self).__init__(username, password, **kwargs)


u"""
    Tornado Part
"""

PER_SIZE = 10
g_DB = DBInterface(db_path=Config.DB_PATH)


def is_commission(func):  # hook worker
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _msg = u"任务队列中!"

        input_username = args[1] if args else None
        if input_username:
            alive_lts = [item.name for item in threading.enumerate()]
            if input_username + func.func_name in alive_lts:
                return dict(msg=_msg)

            t = func(*args, **kwargs)
            t.setDaemon(True)
            t.start()
        return dict(msg=u"成功添加任务!")

    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.db = g_DB
        self.user = self.get_current_user()

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def plus_get_argument(self, param, xsplit=" "):
        get_req_param = self.request.arguments.get(param)
        if isinstance(get_req_param, list) and len(get_req_param) == 1:
            get_req_param = get_req_param[0]

        for replace_item in [",", "\n", "\r"]:
            get_req_param = get_req_param.replace(replace_item, xsplit)
        rv = [item.strip() for item in get_req_param.split(xsplit) if item.strip()]
        return rv

    def render(self, template_name, **kwargs):
        kwargs.update(dateformat=self.datetime_format)
        html = self.render_string(tp(template_name), **kwargs)
        self.finish(html)

    @staticmethod
    def datetime_format(date, format_='%Y.%m.%d'):
        try:
            dateObj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            dateObj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=10)
        return dateObj.strftime(format_)

    def debug_request(self, **kwargs):
        _debug_request = {"method": self.request.method}
        _debug_request.update(**kwargs)
        return self.finish(_debug_request)


class FaceDetect(BaseHandler):
    # TODO
    pass


class Authenticate(BaseHandler):
    def get(self, action):
        if action == "logout":
            self.logout()
        if action == "login":
            self.login()

    def post(self, *args, **kwargs):
        login_eml = self.get_argument("eml", "")
        check_eml = self.check(login_eml) if login_eml else None

        if check_eml in Config.ALLOW_LOGIN:
            user = self.get_argument("eml").encode("utf8").encode("hex")
            self.set_secure_cookie("user", user, expires_days=None)

            return self.redirect("/")
        else:
            return self.redirect(self.settings['login_url'])

    def login(self):
        return self.render("/templates/loginPage.html", post_url=self.get_login_url())

    def logout(self):
        self.clear_all_cookies()
        return self.redirect("/")

    @staticmethod
    def check(eml):
        # undefined

        return eml


class UsersHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, param1=None, *args, **kwargs):
        if self.get_argument("method", "") == "add":
            return self.render("/templates/usersAdd.html")

        is_filter = self.get_argument("filter", 0)
        page = self.get_argument("pages", 1)
        r_page = re.search(r"\d+", str(page))
        page = int(r_page.group(0)) if r_page else 1

        if int(is_filter):
            sql = "SELECT * FROM users WHERE is_finish != 1 and responsible = ? ORDER BY create_date DESC LIMIT ? OFFSET ?;"
            rv = self.db.query_db(sql, args=(self.get_current_user(), PER_SIZE, PER_SIZE * (page - 1)), in_meta=True)
        else:
            sql = "SELECT * FROM users WHERE is_finish != 1 ORDER BY create_date DESC LIMIT ? OFFSET ?;"
            rv = self.db.query_db(sql, args=(PER_SIZE, PER_SIZE * (page - 1)), in_meta=True)

        return self.render("/templates/usersList.html", users=rv, page=str(page))

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self, param1=None, *args, **kwargs):
        _method = self.get_argument("method", "")
        if _method == "add":
            _add_zone_prefix = Common.to_bool(self.get_argument("has_zone", False))
            _zone = self.get_argument("zone", strip=True) if _add_zone_prefix else ""

            _username = self.plus_get_argument("username")
            _username = map(lambda u: _zone + u, _username) if _add_zone_prefix else _username

            _password = self.get_argument("password")
            _note = self.get_argument("para3")

            # rv = self._add_account(username=_username, pwd=_password, note=_note)
            t = threading.Thread(target=self._add_account, kwargs=dict(username=_username, pwd=_password, note=_note))
            t.setDaemon(True)
            t.start()

            self.write({"success": True, "data": 1})
            return self.finish()  # self.render("/templates/usersAdd.html")

        action = self.get_argument("action")
        if action == "exchange":
            sql = "SELECT username, password FROM users WHERE username = ?;"
            query = self.db.query_db(sql, args=(param1,), one=True, in_meta=True)
            _client = Iabe(username=query["username"], password=query["password"])
            msg = _client.call_exchange()

            self.write(dict(rv=msg))
            return self.finish()

        if action == "today_train":
            sql = "SELECT lscode FROM users WHERE username = ?;"
            query_lscode = self.db.query_db(sql, args=(param1,), one=True, in_meta=True)
            _lscode = query_lscode["lscode"]
            if not _lscode:
                sql = "UPDATE users SET lscode=? WHERE username = ?;"
                _lscode = Iabe(param1, password="").call_get_ls_code()
                self.db.write_db(sql, args=(_lscode, param1))

            _client = AccountInterface(param1, password="")
            rv = _client.call_get_today_trains(ls_code=_lscode)

            self.write(rv)
            return self.finish()

        if action == "note":
            sql = 'SELECT notes FROM users WHERE username = ?;'
            rv = self.db.query_db(sql, args=(param1,), one=True, in_meta=True)

            self.write(dict(rv=(rv["notes"] and rv["notes"] or u"没有备注记录")))
            return self.finish()

        if action == "progress":
            sql = "SELECT username, password FROM users WHERE username = ?;"
            query = self.db.query_db(sql, args=(param1,), one=True, in_meta=True)
            _client = Iabe(username=query["username"], password=query["password"])
            rv = _client.call_get_learn_progress()

            self.write(rv)
            return self.finish()

        if action == "face":
            return self.write({"action": action})
            # self.finish()

        self.send_error(400)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def delete(self, param1=None, *args, **kwargs):
        msg = []
        username = self.plus_get_argument("username", xsplit=",")

        for unm in username:
            if unm:
                sql = "UPDATE users SET is_finish=? WHERE username = ?"
                msg = self.db.write_db(sql, args=(1, unm,))

        self.finish(dict(success=True, rv=msg))

    def _add_account(self, username, pwd, note="", *args, **kwargs):
        msg = dict(error_msg=400)
        for _user in username:
            if all([_user, pwd]):
                client = AccountInterface(username=_user, password=pwd)
                ls_code = client.call_get_ls_code()

                sql = "SELECT * FROM users WHERE username = ?;"
                query = self.db.query_db(sql, args=(client.username,), one=True)
                if query:
                    sql = "UPDATE users SET password=?, is_finish=0, notes=?, responsible=? WHERE username = ?;"
                    msg = self.db.write_db(sql, args=(pwd, note, self.user, client.username))
                else:
                    sql = "INSERT INTO users (lscode, username, password, zone, responsible, notes) VALUES (?, ?, ?, ?, ?, ?);"
                    msg = self.db.write_db(sql, args=(
                        ls_code, client.username, client.password, client.zone, self.user, note))


class LogsHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self, param1=None, *args, **kwargs):
        param1 = Common.char_format(param1, var="unm")
        sql = "SELECT create_date, content FROM loger WHERE logerName = ? ORDER BY create_date DESC LIMIT 10;"
        log_data = [(item.create_date, item.content) for item in
                    self.db.query_db(sql, args=("log_" + param1,), in_meta=True)[::-1]]
        self.write(dict(account=param1, rv=log_data))
        self.finish()


class WorkerHandler(BaseHandler):
    def initialize(self):
        self.db = g_DB
        self.unm = self.get_argument("username")

        if self.unm.find(",") > -1:
            self.users_list = []
            for item in self.unm.split(","):
                sql = "SELECT username, password FROM users WHERE username = ?;"
                rv = self.db.query_db(sql, args=(item,), in_meta=True)
                self.users_list.extend(rv if rv else [])
        else:
            sql = "SELECT username, password FROM users WHERE username = ?;"
            rv = self.db.query_db(sql, args=(self.unm,), one=True, in_meta=True)
            self.users_list = [rv]

    @tornado.web.authenticated
    def get(self, param1=None, *args, **kwargs):
        kwargs.update(param1=param1)
        self.debug_request(**kwargs)

    @tornado.web.authenticated
    def post(self, action):
        if len(self.users_list) > 0:
            for user_obj in self.users_list:
                u, p = user_obj.username, user_obj.password
                if action in ["cg_old", "cgw1", "cgw4"]:
                    msg = self._cgw(u, p, action)

                if action in ["mn_old", "mnks4"]:
                    msg = self._mnks(u, p, action)
            return self.write(dict(code=200, rv=(msg and msg["msg"] or "None")))

        self.send_error()

    @is_commission
    def _cgw(self, u, p, action):
        iabeCilent = Iabe(username=u, password=p)
        kw = {"var": action, "log_console": False, "level": "debug", }
        return threading.Thread(target=iabeCilent.call_cgw, name=u + "_cgw", kwargs=kw)

    @is_commission
    def _mnks(self, u, p, action):
        sql = "SELECT lscode FROM users WHERE username = ?;"
        rv = self.db.query_db(sql, args=(u,), one=True, in_meta=True)

        iabeCilent = Iabe(username=u, password=p)
        kw = {"var": action, "lscode": rv["lscode"], "log_console": False, "level": "debug", }
        return threading.Thread(target=iabeCilent.call_mnks, name=u + "_mnks", kwargs=kw)


class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, param1=None, *args, **kwargs):
        sql = "SELECT create_date, content FROM loger WHERE type = 'syslog' ORDER BY create_date DESC LIMIT 5;"
        log_data = [(item.create_date, item.content) for item in self.db.query_db(sql, in_meta=True)]
        return self.render("/templates/settingPage.html", log_content=log_data, license="")

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.web.gen.engine
    def post(self, param1=None, *args, **kwargs):
        content = self.get_argument("content", "")
        if content:
            self.set_status(200)
            msg = self.wlog(content)
            self.write(msg)
        else:
            self.set_status(400)

        self.finish()

    def wlog(self, content):
        sql = "INSERT INTO loger (type, content) VALUES (?, ?);"
        msg = self.db.write_db(sql, args=("syslog", content))
        return {"success": True, "data": msg}


settings = {
    "debug": Config.DEBUG,
    "address": Config.HOST,
    "port": Config.PORT,
    "login_url": "/login",
    "xsrf_cookies": True,
    "cookie_secret": Config.SECRET_TOKEN,
    "static_path": Config.STATIC_DIR,
}
application = tornado.web.Application([
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings['static_path']}),
    (r"/", UsersHandler),
    (r"/index", UsersHandler),
    # (r"/face", FaceDetect),
    (r"/worker/(\w+)", WorkerHandler),
    (r"/(login|logout)", Authenticate),
    (r"/api/users", UsersHandler),
    (r"/api/users/(one|vl|(\w){2}(\d){7})", UsersHandler),
    (r"/api/logs/((\w){2}(\d){7}$)", LogsHandler),
    (r"/api/worker/(vl|(\w){2}(\d){7}$)", WorkerHandler),
    (r"/api/settings", SettingsHandler),
], **settings)

if __name__ == '__main__':
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
