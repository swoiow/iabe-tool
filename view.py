#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import functools
import hashlib
import importlib
import threading
import uuid

import tornado.concurrent
import tornado.escape
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.queues
import tornado.template
import tornado.web
from sqlalchemy import or_, and_

importlib.import_module("Config")
from utils import *

if PY_VERSION == 3:
    B = char_transform
    S = lambda p: char_transform(p, to_str=True)

PER_SIZE = 10


def TWorker(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        def t_func(*args, **kwargs):
            """
            :param args:
            :param kwargs:
                    t_name
                    callback
            :return:
            """
            result = func(*args, **kwargs)

            if kwargs.get("callback"):
                return kwargs["callback"](result)

            return True

        if kwargs.get("t_name", None) in [item.name for item in threading.enumerate()]:
            return False

        t = threading.Thread(target=t_func, args=args, kwargs=kwargs)
        t.setName(kwargs.get("t_name", func.__name__))
        t.setDaemon(True)
        t.start()

        return True

    return wrapper


class MyStaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        if self._headers.get("Server"):
            del self._headers["Server"]


class BaseRequest(tornado.web.RequestHandler):
    def set_default_headers(self):
        if self._headers.get("Server"):
            del self._headers["Server"]

    def get(self, *args, **kwargs):
        self.send_error(404)


class BaseHandler(BaseRequest):
    def initialize(self):
        self.db_session = db_session
        self.user = self.get_current_user()

    def get_current_user(self):
        user = self.get_secure_cookie("user")
        return user and user.decode()

    def get_accounts(self, param):
        block_rule = re.compile("[\w]+")
        params = self.request.arguments.get(param)

        if all([isinstance(params, list), len(params) == 1]):
            params = params[0]
        result = re.findall(block_rule, S(params))
        if len(result) > 0:
            return map(lambda user: user.lower(), result)

        return []

    def render(self, template_name, *args, **kwargs):
        kwargs.update(dict(dateformat=self.datetime2str, data2photo=self.enc_data2base64))
        html = self.render_string(os.path.normpath(os.path.join(Config.TEMPLATES_DIR, template_name)), **kwargs)
        return self.finish(html)

    @staticmethod
    def datetime2str(date, format_='%Y.%m.%d'):
        date_obj = None
        if isinstance(date, datetime.datetime):
            date_obj = date
        elif isinstance(date, float):
            return datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')

        elif isinstance(date, str):
            guest_lt = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f"]

            for item in guest_lt:
                try:
                    date_obj = datetime.datetime.strptime(date, item) + datetime.timedelta(hours=8)
                except ValueError:
                    pass

            try:
                date = float(date)
                return datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass

        if date_obj:
            return date_obj.strftime(format_)

    def enc_data2base64(self, data):
        if data:
            array = data.split("|")
            data = bytearray([int(i) for i in array])
            return base64.b64encode(data)

    def debug_request(self, **kwargs):
        _debug_request = {"method": self.request.method}
        _debug_request.update(**kwargs)
        return self.finish(_debug_request)

    def setup_page(self, page_number):
        f = lambda data: "?" + parse.urlencode(data)
        req_query = {k: v[0] for k, v in list(self.request.query_arguments.items())}
        prev_pn = 1 if (page_number < 2) else (page_number - 1)
        next_pn = page_number + 1

        return f(dict(req_query, **dict(page=prev_pn))), f(dict(req_query, **dict(page=next_pn)))

    def get_page_number(self):
        pn = int(self.get_argument("page", 1))
        pn = re.search(r"\d+", str(pn))
        pn = int(pn.group(0)) if pn else 1
        # pn = 1 if (pn < 1) else pn
        return pn

    def _get_user_orm(self, username):
        username = username.lower()
        with db_read() as db_ctx:
            query = db_ctx.query(User).filter(User.username == username).first()
            return query


class Authenticate(BaseHandler):
    def get(self, action):
        if action == "logout":
            return self.logout()
        elif action == "login":
            self.secure_func()
            return self.login()

    def post(self, *args, **kwargs):
        if self.secure_func():
            login_eml = self.get_argument("eml", "")
            check_eml = self.check(login_eml) if login_eml else None

            if check_eml in Config.ALLOW_LOGIN:
                self.set_secure_cookie("user", check_eml, expires_days=None)
                self.set_secure_cookie("lv", str(100), expires_days=None)

                return self.redirect(self.get_argument("next", "/"))

        return self.redirect(self.settings['login_url'])

    def login(self):
        return self.render("loginPage.html", post_url=self.get_login_url(), next=self.get_argument("next", "/"))

    def logout(self):
        self.clear_all_cookies()
        return self.redirect("/login")

    @staticmethod
    def check(eml):
        rv = encrypt(eml, key="Login!ck", iv="Login1ck")

        return S(rv)

    def secure_func(self):
        # cookie 伪防爆破, 正确的做法, 日志入数据库查询
        if not self.get_secure_cookie("google", None):
            self.set_secure_cookie("google", self.request.remote_ip + "#0", expires_days=None)
        else:
            ip, c = S(self.get_secure_cookie("google")).split("#")

            if int(c) > 6:
                self.set_secure_cookie("google", "#%s" % (int(c) + 1), expires_days=None)
                return False
            else:
                self.set_secure_cookie("google", self.request.remote_ip + "#%s" % (int(c) + 1), expires_days=None)
                return True


class UsersHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, action=None, *args, **kwargs):
        if action == "add":
            return self.render("usersAdd.html")

        elif action == "index":
            # is_filter = self.get_argument("filter", 0)
            page = self.get_page_number()

            with db_read() as db_ctx:
                query_users = db_ctx.query(User). \
                    filter(User.is_finish != 1). \
                    order_by(User.create_date.desc()). \
                    limit(PER_SIZE). \
                    offset((page - 1) * PER_SIZE)

                result = query_users.all()
                return self.render("usersList.html", users=result, page=self.setup_page(page))

    @tornado.web.authenticated
    def post(self, action=None, *args, **kwargs):
        if action == "search":
            result = self.do_search()
            if not result:
                result = dict(result=None)

            return self.finish(result)

        return self.send_error()

    def delete(self, *args, **kwargs):
        username = self.get_accounts("username")

        for user in username:
            with db_write() as session:
                session.query(User).filter(User.username == user).update(dict(is_finish=1))

        return self.finish(dict(success=True, rv="1"))

    def do_search(self):
        # 可以搜索备注 用户名 添加日期
        keyword = self.get_argument("kw", "")
        try:
            date_rule = datetime.strptime(keyword, '%Y%m%d')
        except ValueError:
            date_rule = datetime.today()

        if keyword:
            with db_read() as db_ctx:
                query = db_ctx.query(User.username, User.notes, User.create_date). \
                    filter(or_(
                    User.username.like("%" + keyword + "%"),
                    User.notes.like("%s" + keyword + "%"),
                    User.create_date.between(date_rule, date_rule + timedelta(days=5))
                )).limit(10)

                data = query.all()
                rtn_data = dict()
                for item in data:
                    rtn_data[item.username] = {k: str(v) for k, v in zip(item._fields, item) if not k.startswith("_")}
                return dict(items=rtn_data)


class WorkerHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self, action, *args, **kwargs):
        users_lts = self.get_accounts("u")

        results = []
        for username in users_lts:
            result = self.task(username, action, t_name="%s_%s" % (action, username))
            result_msg = result and "任务添加成功" or "任务队列中"
            results.append((username, result_msg))

        self.write(dict(result=repr(results)))
        self.finish()

    @TWorker
    def task(self, username, action, **kwargs):
        var = self.get_argument("v")

        action_map = dict(cg="call_cgw", mn="call_moni_v2")
        func = action_map[action]
        user = self._get_user_orm(username)
        if isinstance(user, User):
            with db_read() as db_ctx:
                client = Iabe.set_account(user, db_obj=db_ctx, log_var="db", log_level="info")

                if action == "mn" and any([
                            user.zone == "yl",
                            user.password == "1234",
                ]):  # 强制使用v1方法
                    func = "call_moni_v1"

                getattr(client, func)(var)


class ApiHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self, action, username=None, *args, **kwargs):
        action_map = dict(
            face=self.show_face,
            logs=self.show_log,
            note=self.show_note,
            process=self.show_process,
            status=self.show_status,
            xue=self.show_xue,
        )
        func = action_map.get(action)
        if not func:
            return self.send_error(404)
        else:
            username = set_strip(username) if username else username
            resp = func(username)

            return self.finish(resp) if resp else resp

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def post(self, action, *args, **kwargs):
        action_map = dict(
            add=self.add_account,
            face=self._add_face,
            pwd=self.show_pwd,
            exchange=self.do_exchange,
        )
        func = action_map.get(action, None)
        if not func:
            return self.send_error(404)
        else:
            username = self.get_argument("username")
            resp = func(username)

            return self.finish(resp)

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def delete(self, action, *args, **kwargs):
        if action == "face":
            resp = self._del_face()
            return self.finish(resp)
        else:
            return self.send_error(404)

    def show_face(self, username, *args, **kwargs):
        face_md5 = self.get_argument("md5", None)
        if face_md5:
            with db_read() as db_ctx:
                query = db_ctx.query(Face.enc_data).filter(
                    Face.photo_md5 == face_md5,
                    Face.used == 0,
                    Face.photo_type == "children"
                ).one()

                return dict(data=query.enc_data)

        with db_read() as db_ctx:
            query = db_ctx.query(Face).filter(
                and_(
                    Face.username == username,
                    Face.used == 0,
                    Face.photo_type == "children"
                )
            )

            return self.render("faceList.html", username=username, data=query.all())

    def show_xue(self, username):
        user = self._get_user_orm(username)
        with db_read() as db_ctx:
            client = IabeWebService.from_orm(user, db_obj=db_ctx, log_var="db", log_level="info")
            result = client.get_xueshi()

            return dict(result=result)

    def show_process(self, username):
        user = self._get_user_orm(username)
        with db_read() as db_ctx:
            client = Iabe.set_account(user, db_obj=db_ctx, log_var="db", log_level="info")
            result = client.call_learn_progress()

            return result

    def show_status(self, username):
        with db_read() as db_ctx:
            query = db_ctx.query(Loger.content). \
                filter(Loger.loger_name == "log_" + username). \
                order_by(Loger.create_date.desc()). \
                limit(1)
            return dict(account=username, result=query.first())

    def show_pwd(self, username):
        with db_read() as db_ctx:
            query = db_ctx.query(User.password).filter(User.username == username).first()
            return dict(account=username, result=query)

    def show_log(self, username):
        page = self.get_page_number()

        with db_read() as db_ctx:
            query = db_ctx.query(Loger.create_date, Loger.content). \
                filter(Loger.loger_name == "log_" + username). \
                order_by(Loger.create_date.desc()). \
                limit(PER_SIZE). \
                offset((page - 1) * PER_SIZE)

            result = query.all()
            log_data = [(self.datetime2str(item.create_date, "%m-%d %H:%M:%S"), item.content) for item in result]
            return dict(account=username, result=log_data, page=self.setup_page(page))

    def show_note(self, username):
        with db_read() as db_ctx:
            query = db_ctx.query(User.notes).filter(User.username == username).first()
            return dict(account=username, result=query)

    def add_account(self, *args, **kwargs):
        users_lt = self.get_accounts(param="username")
        password = self.get_argument("password")
        zone = self.get_argument("zone")
        note = self.get_argument("para3", "None")

        has_prefix = to_bool(self.get_argument("has_prefix", False))
        if has_prefix:
            zone = self.get_argument("prefix")
            users_lt = map(lambda user: zone + user, users_lt)

        self._add_account(username=users_lt, pwd=password, note=note, zone=zone)

        return dict(result=True, detail=u"全部添加完成")

    @TWorker
    def _add_account(self, *args, **kwargs):
        pwd = kwargs["pwd"]
        note = kwargs["note"]
        zone = kwargs["zone"]

        with db_write() as db_ctx:
            for user in kwargs["username"]:
                query_user = db_ctx.query(User).filter(User.username == user)
                if query_user.first():
                    new_data = dict(password=pwd, notes=note, is_finish=0)
                    if not query_user.first().lscode:
                        o = IabeWebService.from_orm(query_user.first(), zone=zone)
                        hao = o.get_hao()
                        zone = zone and zone or o.zone
                        new_data.update(dict(lscode=hao, zone=zone))

                    query_user.update(new_data)
                else:
                    o = IabeWebService.from_simple(user, pwd, zone=zone)
                    hao = o.get_hao()
                    zone = zone and zone or o.zone
                    u = User(username=user, password=pwd, notes=note, lscode=hao, zone=zone, responsible=self.user)
                    db_ctx.add(u)

    def _add_face(self, username):
        assert username is not None
        files = self.request.files['photo']

        for item in files:
            photo_md5 = hashlib.md5(item.body).hexdigest()
            query = self.db_session.query(Face.id).filter(Face.photo_md5 == photo_md5).all()
            if not query:
                s_name = str(uuid.uuid4()) + ".jpg"
                p = os.path.join(Config.IMG_DIR, s_name)
                with open(p, "wb") as wf:
                    wf.write(item.body)

                try:
                    detectFaceUnit = importlib.import_module("utils.detectFaceUnit")

                    face_discern = detectFaceUnit.detect_faces(p)
                except Exception as e:
                    os.remove(p)
                    return dict(success=False, result=repr(e))

                with db_write() as session:
                    i = Face(username=username, photo=s_name.encode(), photo_md5=photo_md5, photo_type="source", used=0)
                    session.add(i)

                    for c in face_discern:
                        file_md5 = hashlib.md5(c["path"].encode()).hexdigest()
                        with open(c["path"], "r") as rf:
                            i = Face(
                                username=username,
                                photo=c["src"].encode(),
                                photo_md5=file_md5,
                                enc_data=rf.read(),
                                photo_type="children",
                                used=0
                            )
                        session.add(i)

                return dict(result=True, found=len(face_discern))

            else:
                return dict(result=False, msg="exist !")

    def _del_face(self):
        md5 = self.get_argument("md5")
        with db_write() as session:
            query_imgs = session.query(Face).filter(Face.photo_md5 == md5, Face.photo_type == "children")
            for img_item in query_imgs.all():
                img_item.used = 1
                session.add(img_item)
                # TODO: rm file

                return dict(result=True)
            else:
                return dict(result=None)

    def do_exchange(self, username):
        var = self.get_argument("var", None)
        user = self._get_user_orm(username)

        with db_read() as db_ctx:
            client = Iabe.set_account(user, db_obj=db_ctx, log_var="db", log_level="info")
            if var:
                result = client.call_exchange(var)
                return dict(success=True, result=result)
        return self.send_error(410)


settings = {
    "gzip": True,
    "compress_response": True,
    "debug": Config.DEBUG,
    "address": Config.HOST,
    "port": Config.PORT,
    "login_url": "/login",
    "xsrf_cookies": True,
    "cookie_secret": Config.SECRET_TOKEN,
    "static_path": Config.STATIC_DIR,
    "template_path": Config.TEMPLATES_DIR,
    "static_handler_class": MyStaticFileHandler,
    "default_handler_class": BaseRequest
    # "xsrf_cookie_kwargs": dict(httponly=True, secure=True),
}

application = tornado.web.Application([
    (r"/robots.txt", tornado.web.StaticFileHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings['static_path']}),
    (r"/", tornado.web.RedirectHandler, dict(url=r"/index")),
    (r"/(index|add|search)", UsersHandler),
    (r"/api/users?method=add", tornado.web.RedirectHandler, dict(url=r"/api/add")),
    (r"/(login|logout)", Authenticate),
    (r"/api/(add|pwd)", ApiHandler),
    (r"/api/(face|logs|note||process|status|xue|exchange)/(\w{2}\d{7})", ApiHandler),
    (r"/do/(cg|mn)", WorkerHandler),
], **settings)

if __name__ == '__main__':
    if not Config.DEBUG:
        tornado.options.options.logging = "warning"
        tornado.options.options.log_file_prefix = os.path.join(Config.LOG_DIR, "tornado.log")
        tornado.options.parse_command_line()

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(Config.PORT, address=Config.HOST)
    tornado.ioloop.IOLoop.current().start()
    print("Server Run On {0}:{1}".format(Config.HOST, Config.PORT))
