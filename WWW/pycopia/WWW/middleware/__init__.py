#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=0:smarttab

"""
Collection of WSGI middleware.
"""


class Middleware(object):
    pass


class NullMiddleware(Middleware):

    def __init__(self, application, config=None):
        self.application = application

    def __call__(self, environ, start_response):

        def middle_start_response(status, response_headers, exc_info=None):
            return start_response(status, response_headers, exc_info)

        return self.application(environ, middle_start_response)


