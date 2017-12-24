#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import os

from utils.dbModel import Loger
from utils.dbUnit import db_write


class Logger(logging.Logger):
    __default_format__ = "%(name)s, %(asctime)s, %(funcName)s: %(levelname)-8s %(message)s"

    def __init__(self, name, **kwargs):
        super(Logger, self).__init__(name)

        self.level = logging.DEBUG
        if kwargs.get("level"):
            self.level = getattr(logging, kwargs["level"])

        if kwargs.get("log_db"):
            db_obj = kwargs.get("db_obj", False)
            assert hasattr(db_obj, "__class__") is True

            dh = DBHandler()
            dh.setFormatter(logging.Formatter(self.__default_format__))
            self.addHandler(dh)

        if kwargs.get("log_file"):
            log_dir = os.environ.get("LOG_DIR", os.environ.get("IABE_LOG_DIR"))
            if not log_dir:
                raise EnvironmentError("Get LOG_DIR fail!")

            handler = logging.FileHandler(log_dir + "/" + self.name + ".log", encoding="utf8")
            handler.setFormatter(logging.Formatter(self.__default_format__))
            self.addHandler(handler)

        if kwargs.get("log_console"):
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(self.__default_format__))
            self.addHandler(handler)

    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.name)


class DBHandler(logging.Handler):
    def __init__(self):
        super(DBHandler, self).__init__()

    def emit(self, record):
        with db_write() as db_ctx:
            w_log = Loger(
                type=record.levelname,
                loger_name=record.name,
                create_date=record.created,
                content=record.msg
            )
            db_ctx.add(w_log)

    def close(self):
        logging.Handler.close(self)
