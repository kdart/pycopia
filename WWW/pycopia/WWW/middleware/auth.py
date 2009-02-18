#!/usr/bin/python2.5
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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

"""
Authentication and authorization middleware.

"""


import PAM
from hashlib import sha1
import struct

from pycopia.urlparse import quote, unquote
from pycopia.WWW import framework
from pycopia.WWW.middleware import Middleware
from pycopia.db import models
from pycopia import sysrandom as random



class AuthenticationError(Exception):
    pass

# maps generic authservice names in the DB to actual PAM service profiles
# provided by pycopia.
_SERVICEMAP = {
    None: "pycopia", # default, use PAM
    "pam": "pycopia",
    "system": "pycopia", # alias
    "ldap": "pycopia_ldap", # ldap via PAM
    "local": None, # local means use password in DB (sha1 hashed)
}


# Following mimic the Javascript implementation of sha1 and HMAC_SHA1.
def sha1Hash(msg):
    h = sha1()
    h.update(msg)
    return h.digest()


def HMAC_SHA1(key, message):
  blocksize = 64
  ipad = "6666666666666666666666666666666666666666666666666666666666666666"
  opad = ("\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\" + 
      "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\")
  if (len(key) > blocksize):
    key = sha1Hash(key)
  key = key + chr(0) * (blocksize - len(key))
  return sha1Hash(_strxor(key, opad) +  sha1Hash(_strxor(key, ipad) + message))

def _strxor(s1, s2):
    return "".join(map(lambda x, y: chr(ord(x) ^ ord(y)), s1, s2))


class AuthorizeRemoteUser(Middleware):
    """Middleware that assures REMOTE_USER is set."""
    def __init__(self, app, config):
        self.app = app
        self.accept_empty = config.get("accept_empty_user", False)

    def __call__(self, environ, start_response):
        if 'REMOTE_USER' not in environ:
            raise framework.HttpErrorNotAuthenticated()
        elif environ['REMOTE_USER'] or self.accept_empty:
            return self.app(environ, start_response)
        raise framework.HttpErrorNotAuthorized("No user set.")


class Authenticate(object):
    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):

        def auth_start_response(response, headers, exc_info):
            if exc_info:
                if exc_info[0] is framework.HttpErrorNotAuthenticated:
                    return framework.HttpResponseRedirect("/auth/login") # XXX
                else:
                    start_response(response, headers, exc_info)
            else:
                pass # XXX
        return self.app(environ, auth_start_response)


class Authenticator(object):
    def __init__(self, user):
        self.username = user.username # a models.User object instance.
        self.password = user.password
        self.authservice = user.authservice

    def _pam_conv(self, auth, query_list):
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
        cram = HMAC_SHA1(key, self.password)
        if authtoken != cram:
            raise AuthenticationError("Invalid password.")

        # at this point the password is known, further authentication may
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
        pass


# For logging in, the User object 

# The old-fashoned way... just to verify the pain.
LOGIN_PAGE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.w3.org/1999/xhtml"
version="-//W3C//DTD XHTML 1.1//EN">
  <head>
    <title>Login</title>
    <link href="/media/css/login.css" type="text/css" rel="stylesheet" />
    <script src="/media/js/login.js" type="text/javascript;version=1.7"></script>
  </head>
  <body>
    <h1>Login</h1>
    %(message)s
    <p>Please log in.</p>
    <form name="loginform" action="/auth/login" method="post" onsubmit="return validateForm();" enctype="application/x-www-form-urlencoded">
      <label for="username">Name:</label><input type="text" name="username" id="id_username" />
      <label for="password">Password:</label><input type="password" name="password" id="id_password" />
      <input type="hidden" name="key" id="id_key" value="%(key)s" />
      <input type="hidden" name="redir" id="id_redir" value="%(redirect)s" />
      <input type="submit" name="enter" value="Log In" id="id_submit" />
    </form>
    <hr />
    <script><![CDATA[document.getElementById('id_username').focus()]]></script>
  </body>
</html>
"""


class LoginHandler(framework.RequestHandler):

    def get(self, request):
        # This key has to fit into a 32 bit int for the javascript side.
        key = quote(struct.pack("I", random.randint(0, 4294967295)))
        parms = {
            "redirect": request.GET.get("redir", '/'),
            "key": key,
        }
        msg = request.GET.get("message")
        if msg:
            parms["message"] = '<p class="error">%s</p>' % (msg,)
        else:
            parms["message"] = ''
        return framework.HttpResponse(LOGIN_PAGE % parms, "application/xhtml+xml")

    def post(self, request):
        name = request.POST["username"]
        cram = request.POST["password"]
        key = request.POST["key"]
        redir = request.POST["redir"]
        try:
            user = request.database.query(models.User).filter_by(username=name).one()
        except models.NoResultFound:
            return framework.HttpResponseRedirect(request.get_url(login), message="No such user.")
        try:
            good = Authenticator(user).authenticate(unquote(cram), unquote(key))
        except AuthenticationError, err:
            request.log_error("Did NOT authenticate: %r" % (name, ))
            return framework.HttpResponseRedirect(request.get_url(login), message=str(err))
        if good:
            request.log_error("Authenticated: %s" % (name,))
            # XXX set up session
            return framework.HttpResponseRedirect(redir)
        else:
            request.log_error("Authentication no good: %r" % (name, ))
            return framework.HttpResponseRedirect(request.get_url(login), message="Failed to authenticate.")


class LogoutHandler(framework.RequestHandler):

    def get(self, request):
        request.session.close()
        return framework.HttpResponseRedirect("/")



login = LoginHandler()
logout = LogoutHandler()

