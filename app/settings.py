#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .settings_dbg import *

SECRET_KEY = os.urandom(50)

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
