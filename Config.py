#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

basedir = os.environ.get("OPENSHIFT_DATA_DIR", os.getcwd())

HOST = ""  # os.environ["OPENSHIFT_PYTHON_IP"]
PORT = 80  # os.environ["OPENSHIFT_PYTHON_PORT"]
DEBUG = True
DB_PATH = os.path.join(basedir, "v2_data.db")
SECRET_TOKEN = os.urandom(128)

ALLOW_LOGIN = [
    # undefined
]

STATIC_DIR = os.path.join(basedir, "static")
TEMPLATES_DIR = os.path.join(basedir)
LOG_DIR = os.path.join(basedir, "log")

__all__ = [var for var in dir() if var.isupper()]
