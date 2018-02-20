#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from configparser import ConfigParser, ExtendedInterpolation

from django.apps import AppConfig

base_dir = os.environ.get("ENV_DATA_DIR", os.path.abspath(os.path.dirname(__file__)))
data_dir = os.path.join(base_dir, "data")


class NewIabeConfig(AppConfig):
    name = 'iabe'

    PKL_PATH = os.path.join(data_dir, "data.pkl")
    LOG_DIR = os.path.join(data_dir, "logs")
    IMG_DIR = os.path.join(data_dir, "imgs")


cfg_path = os.environ.get("DIY_INI_CONFIG", os.path.join(data_dir, "config.ini"))
cfg = ConfigParser(interpolation=ExtendedInterpolation())
cfg.read(cfg_path)

try:
    for k, v in cfg["COMMON"].items():
        os.environ[k] = v

    for k, v in cfg["MAIL"].items():
        os.environ[k] = v

    for k in dir():
        v = globals()[k]
        if k.endswith("DIR"):
            os.path.exists(v) or os.makedirs(v)
        if k.isupper() and any([k.endswith("DIR"), k.endswith("PATH")]):
            os.environ["IABE_" + k] = v
except KeyError:
    print("%s: Please note! Initialization of environment variables failed." % __file__)
