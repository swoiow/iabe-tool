#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import tornado.httpserver
import tornado.ioloop

try:
    from view import application as WebApp
except (ImportError, ImportWarning):
    from entire import application as WebApp

if __name__ == "__main__":
    ip = os.environ['OPENSHIFT_DIY_IP']
    port = int(os.environ['OPENSHIFT_DIY_PORT'])

    http_server = tornado.httpserver.HTTPServer(WebApp)
    http_server.bind(port, address=ip)
    http_server.start(2)
    tornado.ioloop.IOLoop.current().start()
