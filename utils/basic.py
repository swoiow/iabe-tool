#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import base64
import os
import random
import re
from datetime import (date)

from Crypto.Cipher import DES

from utils import PY_VERSION

if PY_VERSION == 3:
    from html.parser import HTMLParser
    import urllib.parse as urlparse_

    parse = urlparse_
    parse_qs = urlparse_.parse_qs
    urlparse = urlparse_.urlparse
    unquote = urlparse_.unquote
if PY_VERSION == 2:
    from HTMLParser import HTMLParser
    from urlparse import (urlparse, parse_qs, unquote)

    parse = urlparse

common_key = os.environ.get("common_key")
common_iv = os.environ.get("common_iv")
ws_key = os.environ.get("ws_key")
ws_iv = os.environ.get("ws_iv")
hb_key = os.environ.get("hb_key")
hb_iv = os.environ.get("hb_iv")


class URLSeeker(HTMLParser):
    def __init__(self, check_dom=(), dom_attr=(False, None), get_process=False):
        """
        :param check_dom: tag, attr, value
        """
        HTMLParser.__init__(self)
        self._tag, self._attr, self._value = check_dom
        self.data = ""
        self.__find__ = False
        self.get_process = get_process

        if dom_attr:
            self.dom_attr = dom_attr[0]
            self.dom_attr_name = dom_attr[1]
            self.dom_attr_value = ""

    def handle_starttag(self, tag, attrs):
        gid = dict(attrs).get(self._attr, "")
        if all([gid.find(self._value) > -1, tag == self._tag]):
            self.__find__ = True

            if self.dom_attr:
                self.dom_attr_value = dict(attrs).get(self.dom_attr_name)

    def handle_data(self, data):
        if self.__find__:
            self.data += data.strip()
            # if self.get_process:
            # self.data += data
            # else:
            # self.data = data

    def handle_endtag(self, tag):
        if tag == self._tag:
            self.__find__ = False


def encrypt(plaintext, key=None, iv=None, **kwargs):
    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = hb_key and hb_key or common_key, hb_iv and hb_iv or common_iv
        key, iv = key + str(day), iv + str(day)

    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    pad_num = 8 - (len(plaintext) % 8)
    for i in range(pad_num):
        plaintext += chr(pad_num)
    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.encrypt(plaintext)

    return base64.b64encode(text)


def decrypt(plaintext, key="", iv="", **kwargs):
    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = hb_key and hb_key or common_key, hb_iv and hb_iv or common_iv
        key, iv = key + str(day), iv + str(day)

    try:
        enc_text = base64.b64decode(plaintext)
    except ValueError:
        enc_text = unquote(base64.b64decode(plaintext))

    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.decrypt(enc_text)
    if isinstance(text, bytes):  # decode case py3
        text = text.decode()

    return re.sub(r'[\x01-\x08]', '', text)


def encrypt_ws(plaintext, key="", iv="", **kwargs):
    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = ws_key, ws_iv
        key, iv = key + str(day), iv + str(day)

    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    pad_num = 8 - (len(plaintext) % 8)
    for i in range(pad_num):
        plaintext += chr(pad_num)
    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.encrypt(plaintext)

    return base64.b64encode(text)


def decrypt_ws(plaintext, key="", iv="", **kwargs):
    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = ws_key, ws_iv
        key, iv = key + str(day), iv + str(day)

    try:
        enc_text = base64.b64decode(plaintext)
    except ValueError:
        enc_text = unquote(base64.b64decode(plaintext))

    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.decrypt(enc_text)

    return re.sub(r'[\x01-\x08]', '', text)


def data2urlencode(account, p5, p7, p8, p9, p6="1", method="15", is_post=False, **kwargs):
    """
        Instruction:
    :param method:  默认15, 挑战场。 
    :param account: param1: 登录的帐号。
                    param2: 登录的帐号。
                    param3: 头像信息。默认../Upload/UserHead/001.jpg
                    param4: 正确率。最高是100
    :param p5:      param5: 得分信息。需要分2次
    :param p6:      param6: 闯关为，1；挑战为，4。
    :param p7:      param7: 大类(章)。一共有4大类。
    :param p8:      param8: 按顺序的小类(节)。
    :param p9:      param9: 按顺序的条目。# 子条目。指每一个大类下小类的节。
                    param10: 未知。默认为随机数。

    :param is_post: return a Dict for payload.
    :return: return a string with url encode for payload.
    """
    _kw = {
        "method": encrypt(method),
        "param1": encrypt(account),
        "param2": encrypt(account),
        "param3": encrypt("../Upload/UserHead/001.jpg"),
        "param4": encrypt("100"),
        "param5": encrypt(int(p5 / 2.0)),
        "param6": encrypt(p6),
        "param7": encrypt(p7),
        "param8": encrypt(p8),
        "param9": encrypt(p9),
        "param10": encrypt(random.randint(0, 300000)),
        # "param10": encrypt("112300"),
    }

    if is_post:
        return _kw
    return parse.urlencode(_kw, safe='/=')


def data2urldecode(text, single=False):
    if single:
        print(decrypt(text))
    else:
        raw = []
        r = urlparse("http://localhost?" + text)
        d = parse_qs(r.query)
        for k, v in sorted(list(d.items()), key=lambda x: x[0]):
            print("the key: %s " % k + "decrypt: %s" % decrypt(v[0]))
            raw.append((k, v[0]))

        return dict(raw)


def set_strip(param, *args, **kwargs):
    if isinstance(param, str):
        param = param.lower()
    elif isinstance(param, int):
        param = str(param)

    return param.strip()


def char_transform(words, coding="utf-8", to_str=False, force=False):
    """
    :param to_str: 是否转换成str。默认返回utf8
    """
    if any([PY_VERSION == 2, force]):
        if to_str:
            if isinstance(words, str):
                return words

            if isinstance(words, unicode):
                try:
                    return words.encode(coding)
                except UnicodeEncodeError:
                    return char_transform(words.encode("gbk"), to_str=True)

        if isinstance(words, unicode):
            return words

        if isinstance(words, str):
            try:
                return words.decode(coding)
            except UnicodeDecodeError:
                return char_transform(words.decode("gbk"))

    else:
        if isinstance(words, bytes):
            if to_str:
                return str(words, coding)
            return words

        elif isinstance(words, str):
            if to_str:
                return words
            return bytes(words, coding)

        return words


def to_bool(value):
    if str(value).lower() in ("yes", "y", "true", "t", "1", "on"):
        return True
    elif str(value).lower() in ("no", "n", "false", "f", "0", "0.0", "off", "", " ", "none", "[]", "{}"):
        return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))


default_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:53.0) Gecko/20100101 Firefox/53.0"
}
