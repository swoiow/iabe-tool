#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from collections import OrderedDict

import requests
from six import BytesIO as StringIO
from suds.transport import Transport


class UAS(object):
    spider = [
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp/3.0; http://help.yahoo.com/help/us/ysearch/slurp)",
        "msnbot/1.0 (+http://search.msn.com/msnbot.htm)",
        "Mozilla/5.0 (compatible; YoudaoBot/1.0; http://www.youdao.com/help/webmaster/spider/; )",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    ]
    browser = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.32",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.3 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.9.2.1000 Chrome/39.0.2146.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.277.400 QBrowser/9.4.7658.400",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 UBrowser/5.6.12150.8 afari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36 TheWorld 7",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
        "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1",
    ]
    mobile = [
        "Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 950) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Mobile Safari/537.36 Edge/13.10586",
        "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 6.0.1; E6653 Build/32.2.A.0.253) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 6.0; HTC One M9 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
    ]


class UA(object):
    TYPE_BOT = "spider"
    TYPE_SPIDER = "spider"
    TYPE_PC = "browser"
    TYPE_BROWSER = "browser"
    TYPE_MOBILE = "mobile"
    TYPE_PHONE = "mobile"

    @staticmethod
    def get(type_=""):
        type_ = getattr(UAS, type_, None)
        if not type_:
            type_ = UAS.browser
        return random.choice(type_)


class HTTPHeaders(object):
    @staticmethod
    def ua_only(type_=None):
        return UA.get(type_=type_)

    @staticmethod
    def get(ua=None):
        if not ua:
            get_ua = UA.get()
        else:
            get_ua = ua

        return OrderedDict({
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "User-Agent": get_ua,
        })

    @staticmethod
    def get_bot():
        return OrderedDict({
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "User-Agent": UA.get(UA.TYPE_SPIDER),
        })

    @staticmethod
    def virtual_ip():
        def random_ip():
            return lambda: "%s.%s.%s.%s" % (randint(1, 255), randint(1, 255), randint(1, 255), randint(1, 255))

        randint = random.randint
        modify_list = [
            "Via", "CLIENT_IP", "X-Real-Ip", "REMOTE_ADDR", "REMOTE_HOST", "X-Forwarded-For", "X_FORWARDED_FOR"
        ]

        ip = random_ip()
        headers = {k: ip for k in modify_list}
        return headers


class PostHeaders(object):
    __default_header__ = HTTPHeaders.get()

    def _cg_headers(self):
        headers = {
            "X-Requested-With": "ShockwaveFlash/27.0.0.180",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        swf_headers = {
            # "Origin": "http://%s.iabe.cn" % self.SUB_DOMAIN,
            # "Referer": "http://%s.iabe.cn/ecar/ProjectEcar.swf?v=123456" % self.SUB_DOMAIN,
        }

        headers.update(self.__default_header__, **swf_headers)
        return headers

    def _ws_headers(self):
        headers = {
            "X-Requested-With": "ShockwaveFlash/27.0.0.180",
            "Content-Type": "text/xml; charset=utf-8",
        }

        swf_headers = {
            # "Origin": "http://%s.iabe.cn" % self.SUB_DOMAIN,
            # "Referer": self.WS_REFERER,
        }

        headers.update(self.__default_header__, **swf_headers)
        return headers

    def _ex_headers(self):
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            # "Referer": "http://%s.iabe.cn/public/Index.aspx?area=8" % self.SUB_DOMAIN,
        }

        headers.update(self.__default_header__)
        return headers

    def _normal_headers(self):
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        headers.update(self.__default_header__)
        return headers

    @property
    def CgwHeaders(self):
        return self._cg_headers()

    @property
    def WebHeaders(self):
        return self._normal_headers()

    @property
    def WebserviceHeaders(self):
        return self._ws_headers()

    @property
    def ExchangeHeaders(self):
        return self._ex_headers()


class Requests2Transport(Transport):
    def __init__(self, session=None, **kwargs):
        super(Requests2Transport, self).__init__()
        self.__session_ = session or requests.session()

        if kwargs.get("headers"):
            self.extra_headers = {k: v for k, v in kwargs.pop("headers").items()}

    def open(self, request):
        response = self.__session_.get(request.url, params=request.message)
        response.raise_for_status()
        return StringIO(response.content)

    def send(self, request):
        kwargs = {}
        if hasattr(self, "extra_headers"):
            kwargs.update({"headers": self.extra_headers})

        response = self.session.post(request.url, data=request.message, **kwargs)
        response.headers = response.headers
        response.message = response.content
        if response.headers.get('content-type') not in ('text/xml', 'application/soap+xml'):
            response.raise_for_status()
        return response

    @property
    def session(self):
        return self.__session_

    @session.setter
    def session(self, value):
        if not isinstance(value, requests.Session):
            raise TypeError("session must be requests.Session class!")
        self.__session_ = value


PostHeaderInstance = PostHeaders()
