#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问题1，登录跳转的 URL 可能引发 COOKIES 检查错误
"""

from __future__ import absolute_import

import logging
import re

import requests

from .ihttp import HTTPHeaders


def login_cookies_check(username, session=None):
    assert isinstance(session, requests.Session) is True

    cookies_keys = session.cookies.keys()
    return any([
        all(["citycode" in cookies_keys, "ASP.NET_SessionId" in cookies_keys]),  # [BUG 预警] 问题1
        "User" in cookies_keys,
        username in cookies_keys
    ])


def send_login_v1(username, password, city_code):
    """新登录"""
    default_login_uri = "http://iabe.cn/Index.aspx"

    client = requests.Session()
    client.headers = HTTPHeaders.get()

    code = get_net_code_with_re()
    payload = {
        "ctl00$ContentPlaceHolder1$txtUserName": username,
        "ctl00$ContentPlaceHolder1$txtPassword": password,
        "ctl00$ContentPlaceHolder1$selcitycode": city_code,
        "__VIEWSTATE": code,
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnlogin",
    }
    client.post(default_login_uri, data=payload)

    return client


def send_login_v2(username, password, login_uri):
    """旧登录"""
    default_login_uri = "http://yl.iabe.cn/public/default.aspx"

    client = requests.Session()
    client.headers = HTTPHeaders.get()

    code = get_net_code_with_re()
    payload = {
        "__VIEWSTATE": code,
        "ctl00$ContentPlaceHolder1$LoginView1$Login1$UserName": username,
        "ctl00$ContentPlaceHolder1$LoginView1$Login1$Password": password,
        "ctl00$ContentPlaceHolder1$LoginView1$Login1$BtnLogin": ""
    }
    client.post(default_login_uri, data=payload)

    payload = {"userName": username, "password": password}
    client.post(login_uri, data=payload)

    return client


def login(username=None, password=None, *args, **kwargs):
    """
    :param username:
    :param password:
    :param kwargs:
            city_code
            login_uri /LOGIN_URI
    :return:
    """
    logging.info("准备进行的登录，帐号为: %s" % username)

    city_code = kwargs.get("CITY_CODE", kwargs.get("city_code"))
    login_uri = kwargs.get("LOGIN_URI", kwargs.get("login_uri"))

    retry = 3
    while retry > 0:
        try:
            if city_code:
                client = send_login_v1(username=username, password=password, city_code=city_code)
            else:
                assert login_uri is not None
                client = send_login_v2(username=username, password=password, login_uri=login_uri)

            if login_cookies_check(username, session=client):
                logging.info(u"登录成功...")
                return True, client
            else:
                raise requests.ConnectionError

        except AssertionError:
            retry -= 1
            logging.error(u"[!!!] 登录失败，或密码错误。\n")

        except requests.ConnectionError as e:
            retry -= 1
            logging.info("More info: %s\n" % repr(e))
            logging.warning(u"[!!] 网络连接异常, Retrying...%s\n" % (3 - retry))

    raise Exception(logging.error(u"[!!!] 多次登录不成功，退出。"))


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
