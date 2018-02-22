#!/usr/bin/env python
# -*- coding: utf-8 -*-


class CustomHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Server'] = "hidden"
        return response