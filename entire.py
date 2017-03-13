#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import tornado.web

src = ["templates", "static"]
src_dc = {}
for item in src:
    if not os.path.exists(os.path.join(os.environ['OPENSHIFT_DATA_DIR'], item)):
        os.mkdir(os.path.join(os.environ['OPENSHIFT_DATA_DIR'], item))
    src_dc["%s_path" % item] = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], item)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, Openshift")


settings = {
    "debug": False
}
settings.update(src_dc)

application = tornado.web.Application([
    (r"/", MainHandler),
], **settings)
