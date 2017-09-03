#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from utils.dbModel import Loger

try:
    from Config import LOG_DIR
except ImportError:
    pass


class LogerInterface(object):
    def __init__(self, log_var="file", log_name="root", log_level="debug", log_console=False, **kwargs):
        """
        :param var: choose record log way "db or file".
        """
        level_list = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR}

        self.log_var = log_var
        self.log_name = "log_" + log_name
        self.log_level = level_list[log_level]
        self.log_console = log_console
        self.logger = logging.Logger(name=self.log_name, level=self.log_level)

        self.__default_format__ = "%(name)s, %(asctime)s, %(funcName)s: %(levelname)-8s %(message)s"

        if log_var == "db":
            db_obj = kwargs.get("db_obj", False)
            assert hasattr(db_obj, "__class__") is True

            dh = DBHandler(db_obj)
            dh.setFormatter(logging.Formatter(self.__default_format__))
            self.logger.addHandler(dh)

        elif log_var == "file":
            assert "LOG_DIR" in globals().keys()
            handler = logging.FileHandler(LOG_DIR + "/" + self.log_name + ".log", encoding="utf8")
            handler.setFormatter(logging.Formatter(self.__default_format__))
            self.logger.addHandler(handler)

        if self.log_console:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(self.__default_format__))
            self.logger.addHandler(handler)


class DBHandler(logging.Handler):
    def __init__(self, db_obj):
        self.db_obj = db_obj
        super(DBHandler, self).__init__()

    def emit(self, record):
        if hasattr(self.db_obj, "write_db"):
            sql = "INSERT INTO loger (type, loger_name, create_date, content) VALUES (?, ?, ?, ?);"
            self.format(record)
            self.db_obj.write_db(sql, args=(record.levelname, record.name, record.asctime, record.message))

        else:
            w_log = Loger(
                type=record.levelname,
                loger_name=record.name,
                create_date=record.created,
                content=record.msg
            )
            self.db_obj.add(w_log)
            self.db_obj.commit()

    def close(self):
        logging.Handler.close(self)
