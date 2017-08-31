#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import (Column, DateTime, Integer, LargeBinary, Text, VARCHAR)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Face(Base):
    __tablename__ = 'face'

    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR(12))
    photo = Column(LargeBinary)
    enc_data = Column(Text)
    photo_md5 = Column(VARCHAR(32))
    photo_type = Column(VARCHAR(10))
    used = Column(Integer, server_default="0")
    create_date = Column(DateTime)

    def __init__(self, **kwargs):
        if not kwargs.get("create_date"):
            self.create_date = datetime.datetime.utcnow()

        for obj in (f for f in self.__class__.__dict__.keys() if not f.startswith("_")):
            if kwargs.get(obj):
                setattr(self, obj, kwargs[obj])


class Loger(Base):
    __tablename__ = 'loger'

    id = Column(Integer, primary_key=True)
    type = Column(VARCHAR(10))
    loger_name = Column(VARCHAR(20), index=True)
    create_date = Column(VARCHAR)
    content = Column(Text)

    def __init__(self, **kwargs):
        if not kwargs.get("create_date"):
            self.create_date = datetime.datetime.utcnow()

        for obj in (f for f in self.__class__.__dict__.keys() if not f.startswith("_")):
            if kwargs.get(obj):
                setattr(self, obj, kwargs[obj])


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    item = Column(Text)
    itemValue = Column(Text)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    lscode = Column(Integer)
    username = Column(VARCHAR(80), index=True)
    password = Column(VARCHAR(20), server_default="1234")
    create_date = Column(DateTime)
    zone = Column(VARCHAR(5))
    is_finish = Column(Integer, default=0)
    responsible = Column(Text)
    notes = Column(Text, default="")

    def __init__(self, **kwargs):
        if not kwargs.get("create_date"):
            self.create_date = datetime.datetime.utcnow()

        for obj in (f for f in self.__class__.__dict__.keys() if not f.startswith("_")):
            if kwargs.get(obj):
                setattr(self, obj, kwargs[obj])
