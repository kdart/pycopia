#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab:fenc=utf-8
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.


from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
from hashlib import sha1
import struct

import PAM

from pycopia.urlparse import quote, unquote
from pycopia.WWW import framework
from pycopia.db import models
from pycopia import sysrandom as random


HOSTNAME = os.uname()[1]
SESSION_KEY_NAME = b"PYCOPIA"

class AuthenticationError(Exception):
    pass

# maps generic authservice names in the DB to actual PAM service profiles
# provided by pycopia.
_SERVICEMAP = {
    None: b"pycopia", # default, use PAM
    "pam": b"pycopia",
    b"system": b"pycopia", # alias
    b"ldap": b"pycopia_ldap", # ldap via PAM
    b"local": None, # local means use password in DB (sha1 hashed)
    b"clear": None, # clear means use password in DB (clear text)
}


# Following mimic the Javascript implementation of sha1 and HMAC_SHA1.
def sha1Hash(msg):
    h = sha1()
    h.update(msg)
    return h.digest()


def HMAC_SHA1(key, message):
  blocksize = 64
  ipad = b"6666666666666666666666666666666666666666666666666666666666666666"
  opad = (b"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\" +
      b"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
  if (len(key) > blocksize):
    key = sha1Hash(key)
  key = key + chr(0) * (blocksize - len(key))
  return sha1Hash(_strxor(key, opad) +  sha1Hash(_strxor(key, ipad) + message))

def _strxor(s1, s2):
    return b"".join(map(lambda x, y: chr(ord(x) ^ ord(y)), s1, s2))



class Authenticator(object):
    def __init__(self, user):
        self.username = user.username # a models.User object instance.
        self.password = user.password
        self.authservice = user.authservice

    def _pam_conv(self, auth, query_list, *args):
        resp = []
        for query, type in query_list:
            if type == PAM.PAM_PROMPT_ECHO_ON:
                val = self.username
                resp.append((val, 0))
            elif type == PAM.PAM_PROMPT_ECHO_OFF:
                val = self.password
                resp.append((val, 0))
            elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
                resp.append(('', 0))
            else:
                return None
        return resp

    def authenticate(self, authtoken, key, **kwargs):
        if self.authservice == "clear":
            if authtoken != self.password:
                raise AuthenticationError("Invalid cleartext password.")
            else:
                return True

        cram = HMAC_SHA1(key, self.password)
        if authtoken != cram:
            raise AuthenticationError("Invalid local password.")

        # At this point the password is known, further authentication may
        # be specified in the user table via PAM.
        pamsvc = _SERVICEMAP.get(self.authservice)
        if pamsvc is not None:
            return self.authenticate_pam(pamsvc)
        else:
            return True

    def authenticate_pam(self, service):
        auth = PAM.pam()
        auth.start(service)
        auth.set_item(PAM.PAM_USER, self.username)
        auth.set_item(PAM.PAM_CONV, self._pam_conv)
        authenticated = False
        try:
            auth.authenticate()
            auth.acct_mgmt()
        except PAM.error, (resp, code):
            raise AuthenticationError('(%s: %s)' % (resp, code))
        else:
            authenticated = True
        return authenticated

    def set_password(self):
        return NotImplemented


# For logging in, the User object contains the session key.
# This page is hand-written, to keep the client and server implementation in one place.
LOGIN_PAGE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Login</title>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
    <link href="/media/css/login.css" type="text/css" rel="stylesheet" />
    <script src="/media/js/login.js" type="text/javascript" charset="utf-8"></script>
  </head>
  <body>
    <h1>Login</h1>
    %(message)s
    <p>Please log in.</p>
    <form name="loginform" action="/auth/login" method="post" onsubmit="return login.submitForm();" enctype="application/x-www-form-urlencoded">
      <label for="username">Name:</label>
            <input type="text" name="username" id="id_username" placeholder="account name" autofocus="autofocus" />
      <label for="password">Password:</label>
            <input type="password" name="password" id="id_password" placeholder="password" />
      <input type="hidden" name="key" id="id_key" value="%(key)s" />
      <input type="hidden" name="redir" id="id_redir" value="%(redirect)s" />
      <input type="submit" name="enter" value="Log In" id="id_submit" />
    </form>
    <script><![CDATA[
        if (!("autofocus" in document.createElement("input"))) {
            document.getElementById('id_username').focus();
        }
    ]]></script>
    <hr />
  </body>
</html>
"""


class LoginHandler(framework.RequestHandler):

    def get(self, request):
        # This key has to fit into a 32 bit int for the javascript side.
        key = quote(struct.pack(b"I", random.randint(0, 4294967295)))
        parms = {
            b"redirect": request.GET.get("redir", request.environ.get("HTTP_REFERER", "/")),
            b"key": key,
        }
        msg = request.GET.get("message")
        if msg:
            parms[b"message"] = '<p class="error">%s</p>' % (msg,)
        else:
            parms[b"message"] = ''
        return framework.HttpResponse(LOGIN_PAGE % parms, b"application/xhtml+xml")

    def post(self, request):
        try:
            if request.headers["x-requested-with"].value == "XMLHttpRequest":
                return handle_async_authentication(request)
            else:
                return framework.HttpResponseRedirect(request.get_url(login), message="Method not allowed.")
        except IndexError:
            return framework.HttpResponseRedirect(request.get_url(login), message="Method not allowed.")


def handle_async_authentication(request):
    name = request.POST[b"username"]
    cram = request.POST[b"password"]
    key = request.POST[b"key"]
    redir = request.POST[b"redir"]
    dbsession = models.SessionMaker()
    try:
        user = dbsession.query(models.User).filter_by(username=name).one()
    except models.NoResultFound:
        return framework.JSONResponse((401, b"No such user."))
    try:
        good = Authenticator(user).authenticate(cram, unquote(key))
    except AuthenticationError, err:
        request.log_error("Did NOT authenticate by async: %r\n" % (name, ))
        return framework.JSONResponse((401, str(err)))
    if good:
        request.log_error("Authenticated by async: %s\n" % (name,))
        user.set_last_login()
        resp = framework.JSONResponse((200, redir))
        session = _set_session(resp, user, request.get_host(), "/",
                    request.config.get("LOGIN_TIME", 24))
        dbsession.add(session)
        dbsession.commit()
        dbsession.close()
        return resp
    else:
        request.log_error("Invalid async authentication for %r\n" % (name, ))
        return framework.JSONResponse((401, "Failed to authenticate."))


def _set_session(response, user, domain, path, lifetime=24):
    sess = models.Session(user, lifetime=lifetime)
    response.set_cookie(SESSION_KEY_NAME, sess.session_key, domain=domain,
            path=path, max_age=lifetime * 3600)
    return sess


class LogoutHandler(framework.RequestHandler):

    def get(self, request):
        key = request.COOKIES.get(SESSION_KEY_NAME)
        if key is not None:
            dbsession = models.SessionMaker()
            try:
                sess = dbsession.query(models.Session).filter_by(session_key=key).one()
            except models.NoResultFound:
                pass
            else:
                dbsession.delete(sess)
                dbsession.commit()
                dbsession.close()
        request.session = None
        resp = framework.HttpResponseRedirect("/")
        resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
        return resp


login = LoginHandler()
logout = LogoutHandler()

# Decorator that requires a handler to only serve on a valid session.
def need_login(handler):
    def newhandler(request, *args, **kwargs):
        key = request.COOKIES.get(SESSION_KEY_NAME)
        redir = "/auth/login?redir=%s" % request.path
        if not key:
            return framework.HttpResponseRedirect(redir)
        dbsession = models.SessionMaker()
        try:
            session = dbsession.query(models.Session).filter_by(session_key=key).one()
        except models.NoResultFound:
            resp = framework.HttpResponseRedirect(redir)
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp

        if session.is_expired():
            dbsession.delete(session)
            dbsession.commit()
            dbsession.close()
            resp = framework.HttpResponseRedirect(redir)
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp
        # A check to thwart cross site request forgery
        referer = request.environ.get("HTTP_REFERER")
        if referer is None:
            request.log_error("No referer in authenticated request.\n")
            resp = framework.HttpResponseRedirect("/")
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp
        if HOSTNAME not in referer:
            request.log_error("Our host not in referer.\n")
            resp = framework.HttpResponseRedirect("/")
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp
        request.session = session
        return handler(request, *args, **kwargs)
    return newhandler


def need_authentication(handler):
    def newhandler(request, *args, **kwargs):
        key = request.COOKIES.get(SESSION_KEY_NAME)
        if not key:
            return framework.HttpResponseNotAuthenticated()
        dbsession = models.SessionMaker()
        try:
            session = dbsession.query(models.Session).filter_by(session_key=key).one()
        except models.NoResultFound:
            resp = framework.HttpResponseNotAuthenticated()
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp

        if session.is_expired():
            dbsession.delete(session)
            dbsession.commit()
            dbsession.close()
            resp = framework.HttpResponseNotAuthenticated()
            resp.delete_cookie(SESSION_KEY_NAME, domain=request.get_host())
            return resp
        request.session = session

        return handler(request, *args, **kwargs)
    return newhandler



def init(config):
    global SESSION_KEY_NAME
    SESSION_KEY_NAME = config.SESSION_KEY_NAME


