#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os
import random
import re
from datetime import date

from Crypto.Cipher import DES
from six.moves import urllib

parse = urllib.parse


def load_key():
    # TODO: 改写从文件获得
    common_key = os.environ.get("common_key")
    common_iv = os.environ.get("common_iv")
    ws_key = os.environ.get("ws_key")
    ws_iv = os.environ.get("ws_iv")
    hb_key = os.environ.get("hb_key")
    hb_iv = os.environ.get("hb_iv")

    return common_key, common_iv, ws_key, ws_iv, hb_key, hb_iv


def encrypt(plaintext, key=None, iv=None, **kwargs):
    common_key, common_iv, ws_key, ws_iv, hb_key, hb_iv = load_key()

    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = key and key or (hb_key or common_key), iv and iv or (hb_iv or common_iv)
        key, iv = key + str(day), iv + str(day)

    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    pad_num = 8 - (len(plaintext) % 8)
    for i in range(pad_num):
        plaintext += chr(pad_num)
    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.encrypt(plaintext)

    return base64.b64encode(text)


def decrypt(plaintext, key=None, iv=None, **kwargs):
    common_key, common_iv, ws_key, ws_iv, hb_key, hb_iv = load_key()

    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = hb_key and hb_key or common_key, hb_iv and hb_iv or common_iv
        key, iv = key + str(day), iv + str(day)

    try:
        enc_text = base64.b64decode(plaintext)
    except ValueError:
        enc_text = parse.unquote(base64.b64decode(plaintext))

    cipher = DES.new(key, DES.MODE_CBC, iv)
    text = cipher.decrypt(enc_text)
    if isinstance(text, bytes):  # decode case py3
        text = text.decode()

    return re.sub(r'[\x01-\x08]', '', text)


def encrypt_ws(plaintext, key="", iv="", **kwargs):
    common_key, common_iv, ws_key, ws_iv, hb_key, hb_iv = load_key()

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
    common_key, common_iv, ws_key, ws_iv, hb_key, hb_iv = load_key()

    if (not key) and (not iv):
        day = date.today().day
        day = day < 10 and "%02d" % day or day

        key, iv = ws_key, ws_iv
        key, iv = key + str(day), iv + str(day)

    try:
        enc_text = base64.b64decode(plaintext)
    except ValueError:
        enc_text = parse.unquote(base64.b64decode(plaintext))

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
        "param5": encrypt("%s" % int(p5 / 2.0)),
        "param6": encrypt("%s" % p6),
        "param7": encrypt("%s" % p7),
        "param8": encrypt("%s" % p8),
        "param9": encrypt("%s" % p9),
        "param10": encrypt(random.randint(0, 1000000)),
    }

    if is_post:
        return _kw
    return parse.urlencode(_kw, safe='/=')


def data2urldecode(text, single=False):
    if single:
        print(decrypt(text))
    else:
        raw = []
        r = parse.urlparse("http://localhost?" + text)
        d = parse.parse_qs(r.query)
        for k, v in sorted(list(d.items()), key=lambda x: x[0]):
            # print("the key: %s " % k + "decrypt: %s" % decrypt(v[0]))
            raw.append((k, v[0]))

        return dict(raw)
