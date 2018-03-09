#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import os

import django

try:
    import iabe

    LOG_DB = True
    django.setup()


    class DBHandler(logging.Handler):
        def __init__(self):
            super(DBHandler, self).__init__()

        def emit(self, record):
            lv = "%s_%s" % ("LOG", record.levelname)
            log = iabe.models.Log(
                lv=getattr(iabe.models.Log, lv.upper(), iabe.models.Log.LOG_DEBUG),
                name=record.name,
                created_at=record.created,
                content=record.msg
            )

            log.save()

        def close(self):
            logging.Handler.close(self)
except ImportError:
    LOG_DB = False


class Logger(logging.Logger):
    __default_format__ = "%(name)s, %(asctime)s, %(funcName)s: %(levelname)-8s %(message)s"
    __datefmt__ = "%Y-%m-%d %H:%M:%S"

    def __init__(self, name, **kwargs):
        """
        :param name:
        :param kwargs:
            level
            log_db
            log_file
            log_console
        """
        super(Logger, self).__init__(name)

        self.level = logging.DEBUG
        if kwargs.get("level"):
            self.level = getattr(logging, kwargs["level"])

        if kwargs.get("log_db"):
            if LOG_DB:
                dh = DBHandler()
                dh.setFormatter(logging.Formatter(self.__default_format__, datefmt=self.__datefmt__))
                self.addHandler(dh)

            else:
                logging.error("get log db class fail!")

        if kwargs.get("log_file"):
            log_dir = os.environ.get("LOG_DIR", os.environ.get("IABE_LOG_DIR"))
            if log_dir:
                handler = logging.FileHandler(log_dir + "/" + self.name + ".log", encoding="utf8")
                handler.setFormatter(logging.Formatter(self.__default_format__))
                self.addHandler(handler)
            else:
                logging.error("get log dir fail!")

        if kwargs.get("log_console"):
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(self.__default_format__))
            self.addHandler(handler)

    def __repr__(self):
        return "<%s @name:%s>" % (self.__class__.__name__, self.name)
