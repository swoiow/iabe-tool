#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import sqlite3, Config
    from WebApp import DBInterface as DB_Instance
    
    try:
        DB_Instance(Config.DB_PATH).exec_schema_sql("db_init.sql")
    except sqlite3.OperationalError as e:
        if e[-1] == "no such table: users":
            pass
        else:
            raise Exception(e)
