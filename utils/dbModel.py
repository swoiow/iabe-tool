#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, Text, text, REAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Face(Base):
    __tablename__ = 'face'

    id = Column(Integer, primary_key=True)
    username = Column(Text(12))
    photo = Column(LargeBinary)
    enc_data = Column(Text)
    photo_md5 = Column(Text(32))
    photo_type = Column(Text(10))
    used = Column(Integer, server_default=text("0"))
    create_date = Column(DateTime, server_default=text("(datetime(CURRENT_TIMESTAMP,'utc'))"))


class Loger(Base):
    __tablename__ = 'loger'

    id = Column(Integer, primary_key=True)
    type = Column(Text(10))
    logerName = Column(Text(20), index=True)
    create_date = Column(REAL, server_default=text("(datetime(CURRENT_TIMESTAMP,'utc'))"))
    content = Column(Text(250))


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    item = Column(Text)
    itemValue = Column(Text)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    lscode = Column(Integer)
    username = Column(Text(80), index=True)
    password = Column(Text(20), server_default=text("1234"))
    create_date = Column(DateTime, server_default=text("(datetime(CURRENT_TIMESTAMP,'utc'))"))
    zone = Column(Text(5))
    is_finish = Column(Boolean, server_default=text("0"))
    responsible = Column(Text(30))
    notes = Column(Text)
