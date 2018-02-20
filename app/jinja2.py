#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
more document:
    https://docs.djangoproject.com/en/2.0/topics/templates/#django.template.backends.jinja2.Jinja2
    https://docs.djangoproject.com/en/2.0/ref/csrf/#using-csrf-in-jinja2-templates
"""
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        "static": staticfiles_storage.url,
        "url": reverse,
    })
    return env
