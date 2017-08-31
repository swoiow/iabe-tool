#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from configparser import ConfigParser, ExtendedInterpolation

DEBUG = False
HOST = os.environ.get("OPENSHIFT_PYTHON_IP", "")
PORT = os.environ.get("OPENSHIFT_PYTHON_PORT", 80)
SECRET_TOKEN = os.environ.get("OPENSHIFT_SECRET_TOKEN", os.urandom(16))

base_dir = os.environ.get("OPENSHIFT_DATA_DIR", os.path.abspath(os.path.dirname(__file__)))
STATIC_DIR = os.path.join(base_dir, "static")
TEMPLATES_DIR = os.path.join(base_dir, "templates")

data_dir = os.path.join(base_dir, "data36")
DB_PATH = os.environ.get("DIY_DB_PATH", r"sqlite:///" + os.path.join(data_dir, "data.db"))
PKL_PATH = os.path.join(data_dir, "data.pkl")
LOG_DIR = os.path.join(data_dir, "Logs")
IMG_DIR = os.path.join(data_dir, "Imgs")

cfg_path = os.environ.get("DIY_CONFIG_INI_PATH", os.path.join(data_dir, "config.ini"))
cfg = ConfigParser(interpolation=ExtendedInterpolation())
cfg.read(cfg_path)

for k, v in cfg["COMMON"].items():
    os.environ[k] = v

for k, v in cfg["SYNC"].items():
    os.environ[k] = v

for k, v in cfg["MAIL"].items():
    os.environ[k] = v

for k in dir():
    v = globals()[k]
    if k.endswith("DIR"):
        os.path.exists(v) or os.makedirs(v)
    if k.isupper() and any([k.endswith("DIR"), k.endswith("PATH")]):
        os.environ["IABE_" + k] = v

ALLOW_LOGIN = cfg.get("AUTH", "USERS").split("\n")

__all__ = [var for var in dir() if var.isupper()] + ["cfg"]
