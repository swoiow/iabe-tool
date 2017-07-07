#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import re

import requests

from utils.basic import URLSeeker

DEFAULT_HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:50.0) Gecko/20100101 Firefox/50.0"}


def get_net_code_with_re():
    """" 通过正则方式获取ASP.NET的 __VIEWSTATE """

    _code = ""
    rule = re.compile('(?<=ue=")[0-9a-zA-Z+/]*(?=")')

    urls = [
        (1, "http://yl.iabe.cn/StaticPage/subject/comments.aspx"),
        (2, "http://yl.iabe.cn/public/default.aspx"),
    ]
    for idx, uri in urls:
        _resp = requests.get(uri, headers=DEFAULT_HEADER)
        if idx == 1:
            _code = re.findall(rule, _resp.text)[-1]
        elif idx == 2:
            _code = re.findall(rule, _resp.text)[0]

        if _code:
            return _code

    logging.warning(u"[!!] Get Code Failed.")
    raise requests.ConnectionError


def get_net_code_with_htmlparser():
    """" 通过HTMLParser方式获取ASP.NET的 __VIEWSTATE """

    urls = [
        "http://www.iabe.cn/Index.aspx",
    ]
    for uri in urls:
        gt = requests.get(uri, headers=DEFAULT_HEADER)
        url_seeker = URLSeeker(("input", "id", "__VIEWSTATE"), dom_attr=(True, "value"))
        url_seeker.feed(gt.text)
        code = url_seeker.dom_attr_value
        if code:
            return code
        else:
            logging.warning(u"[!!] Get Code Failed.")
    raise requests.ConnectionError


def get_net_code_with_htmlparser2():
    """" 通过HTMLParser方式获取ASP.NET的 __VIEWSTATE """

    urls = [
        "http://yl.iabe.cn/public/Index.aspx?area=8",
        "http://yl.iabe.cn/public/default.aspx",
    ]

    for uri in urls:
        gt = requests.get(uri, headers=DEFAULT_HEADER)
        url_seeker = URLSeeker(("input", "id", "__VIEWSTATE"), dom_attr=(True, "value"))
        url_seeker.feed(gt.text)
        code = url_seeker.dom_attr_value
        if code:
            return code
        else:
            logging.warning(u"[!!] Get Code Failed.")
    raise requests.ConnectionError


__all__ = ["get_net_code_with_re", "get_net_code_with_htmlparser", "get_net_code_with_htmlparser2"]
