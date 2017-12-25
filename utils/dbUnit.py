#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import SingletonThreadPool

engine = create_engine(os.environ["IABE_DB_PATH"],
                       poolclass=SingletonThreadPool,
                       echo=False)

db_session = Session(bind=engine)


@contextmanager
def db_write():
    """Provide a transactional scope around a series of operations."""
    session = Session(bind=engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def db_read():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


__all__ = ["db_session", "db_write", "db_read"]
