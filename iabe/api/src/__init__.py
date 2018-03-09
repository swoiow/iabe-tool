#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from . import WebApi
from . import WebService


class MixClient(
    WebApi.ClientWebApi,
    WebService.ClientWebServiceApi,
):
    pass
