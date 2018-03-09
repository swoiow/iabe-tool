#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import copy
import logging
import time
from collections import OrderedDict
from functools import wraps

from iabe import apps
from .ihttp import PostHeaders
from .logger import Logger
from .login import login, login_cookies_check


def SessionCache(f):
    @wraps(f)
    def swap(cls, *args, **kwargs):
        cache_session = Cache.get(key=cls.username)
        if cache_session:
            cls.is_login = cls.login_check_by_cookies(cache_session)

            if cls.is_login:
                cls.set_client(cache_session)
                return cls.client

        session = f(cls)
        Cache.set(cls.username, session)
        return session

    return swap


class Bucket(object):
    _bucket = OrderedDict()

    def __init__(self, max_size=300, timeout=None):
        self._max_size = max_size
        self._timeout = timeout

    def set_timeout(self, v):
        self._timeout = v
        return v

    def get(self, key, default=None):
        data = self._bucket.get(key)

        if not data:
            return default
        o, expire = data
        if expire and time.time() > expire:
            del self._bucket[key]
            return default
        return o

    def set(self, key, o, timeout=None):
        self._check_limit()

        if not timeout:
            timeout = self._timeout

        if timeout:
            timeout = time.time() + timeout

        self._bucket[key] = (o, timeout)

    def pop(self, key):
        return self._bucket.pop(key, default=None)

    def clear(self):
        self._bucket = OrderedDict()

    def _check_limit(self):
        if len(self._bucket) >= self._max_size:
            self._bucket.popitem(last=False)


class ClientWebBase(PostHeaders):
    def __init__(self, username, password, *args, **kwargs):
        self.username = username
        self.password = password

        self.logger = Logger(name="log_" + self.username, log_db=True, **kwargs)

        self.__client = None
        self.is_login = False

        self.meta = Meta(self.username)
        self.meta.call_setting_init(**kwargs)

        for k, v in kwargs.items():
            if k != "username":
                setattr(self.meta, k, v)

    @classmethod
    def init_from_dict(cls, dc):
        return cls(**dc)

    @property
    def client(self):
        return self.__client

    def set_client(self, v):
        self.__client = v
        return self.client

    @SessionCache
    def login(self):
        if not self.is_login:
            kws = self.meta.as_dict()
            kws.pop("username")
            self.is_login, client = login(self.username, self.password, **kws)

            self.__default_header__ = copy.deepcopy(client.headers)
            self.set_client(client)

        return self.client

    def login_check_by_cookies(self, session=None):
        return login_cookies_check(self.username, session=session)

    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.username)


class Meta(object):
    def __init__(self, name):
        self.name = name
        self.username = name

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def call_setting_init(self, zone=None, **kwargs):
        # 进行地区服务地址初始化
        cfg = apps.cfg
        data = None

        if zone:
            data = cfg[zone.upper()].items()
        else:
            for prefix in cfg.sections():
                if self.username.upper().startswith(prefix):
                    data = cfg[prefix.upper()].items()
                    zone = prefix
                    break

        if data:
            for k, v in data:
                k = k.upper()
                if k.find("URI") > 0:
                    v = "http://" + v
                setattr(self, k, v)

            setattr(self, "ZONE", zone)
            return True

        else:
            err = u"[!!!] Unable to initialize this account. Please provide Username or Zone. 该地区不支持!"
            return Exception(logging.error(err))

    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.username)


Cache = Bucket(timeout=1800)
