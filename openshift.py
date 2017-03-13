#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import tornado.ioloop

try:
    import WebApp
except ImportError, ImportWarning:
     import entire as WebApp

if __name__ == "__main__":
    ip = os.environ['OPENSHIFT_DIY_IP']
    port = int(os.environ['OPENSHIFT_DIY_PORT'])
    WebApp.application.listen(port, ip)
    tornado.ioloop.IOLoop.instance().start()
