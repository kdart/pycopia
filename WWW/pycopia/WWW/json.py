#!/usr/bin/python2.4
# -*- coding: us-ascii -*-
# vim:ts=2:sw=2:softtabstop=0:tw=74:smarttab:expandtab
#
# Copyright Google Inc. All Rights Reserved.

"""Data access module for Droid WebUI.

Provides JSON mini-framework.
"""

__author__ = 'dart@google.com (Keith Dart)'

import sys
import time
import traceback
from datetime import datetime

import simplejson
from pycopia.WWW.framework import (HttpResponse, HttpResponseNotFound,
                                   HttpResponseServerError)


_DECODER = None
_ENCODER = None


class JSONNotFound(HttpResponseNotFound): 
  def __init__(self, msg=None):
    json = simplejson.dumps(msg)
    HttpResponseNotFound.__init__(self, json, "application/json")


class JSONServerError(HttpResponseServerError):
  """Exports server side Python exception to browser client."""
  def __init__(self, ex, exval, tblist):
    json = simplejson.dumps((str(ex), str(exval), tblist))
    HttpResponseServerError.__init__(self, json, "application/json")


### functions for handling datetime <=> Date conversion.
def _DtChecker(obj):
  return isinstance(obj, datetime)

def _DtSimplifier(dt):
  return {"_class_": "date",
      "value": long(time.mktime(dt.timetuple())*1000)}

def _DtDecoder(timestamp):
  return datetime.fromtimestamp(float(timestamp)/1000.0)
### End datetime conversions ###


class JSONEncoder(simplejson.JSONEncoder):
  def __init__(self):
    super(JSONEncoder, self).__init__(ensure_ascii=False,
        encoding="utf-8")
    self._registry = {}

  def default(self, obj):
    for checker, simplifier in self._registry.itervalues():
      if checker(obj):
        return simplifier(obj)
    return super(JSONEncoder, self).default(obj)

  def register(self, name, check, simplifier):
    self._registry[name] = (check, simplifier)

  def unregister(self, name):
    try:
      del self._registry[name]
    except KeyError:
      pass


class JSONDispatcher(object):
  """Pair with PythonProxy javascript object.

  Use this to call Python functions from javascript, with arguments and
  returns values transparently transported using JSON serialization.

  Requires a URL mapping of the form::

     (r'^base/path/(?P<methodname>\w+)/$', 'views_module.dispatcher'),

  Your views_module.py will then have a line like this::

    _exported = [my_function]
    dispatcher = json.JSONDispatcher(_exported)

  The javascript client can then call an exported Python function with
  native parameters, and get native return value.

  The javascript does this::

    window.myproxy = new PythonProxy("/base/path/");

    Your javascript now can do this:

      d = myproxy.my_function(1, "two");
      d.addCallback(myFunctionHandler);

    If my_function returns 42, The myFunctionHandler gets 42.

  Args:
    functions: A list of function objects that are exposed to the client.
  """
  def __init__(self, functions):
    self._fmap = fmap = {}
    for func in functions:
      fmap[func.func_name] = func
    fmap["_methods"] = self._methods
    self._encoder = GetJSONEncoder()
    self._decoder = GetJSONDecoder()

  def _methods(self):
    return self._fmap.keys()

  def __call__(self, request, methodname):
    handler = self._fmap.get(methodname)
    if handler is None:
      return JSONNotFound("No method " + methodname)
    try:
      data = request.POST.get("data")
      if data:
        try:
          arguments = self._decoder.decode(data)
          # First argument is method name.
          # Allow for keyword arguments as sole argument.
          if len(arguments) == 2 and isinstance(arguments[1], dict):
            args = ()
            kwargs = arguments[1]
          else: # otherwise, use positional arguments.
            args = tuple(arguments[1:])
            kwargs = {}
        except: # error in parameter conversion
          ex, val, tb = sys.exc_info()
          tblist = traceback.extract_tb(tb)
          request.log_error("JSONDispatcher args: %s (%s)" % (ex, val))
          return JSONServerError(ex, val, tblist)
      else:
        args = ()
        kwargs = {}
      json = self._encoder.encode(handler(*args, **kwargs))
      return HttpResponse(json, "application/json")
    except: # all exceptions are sent back to client.
      ex, val, tb = sys.exc_info()
      tblist = traceback.extract_tb(tb)
      del tb
      request.log_error("JSONDispatcher: %s (%s)" % (ex, val))
      return JSONServerError(ex, val, tblist)

  def register_encoder(self, name, check, simplifier):
    self._encoder.register(name, check, simplifier)

  def register_decoder(self, name, decoder):
    self._decoder.register(name, decoder)


class JSONObjectDecoder(object):
  """Decoder for various complex objects.

  Handles decoding complex objects defined by the JSON serialization
  protocol.

  You can register new decoders for any object.
  """
  def __init__(self):
    self._registry = {}

  def __call__(self, js_object):
    try:
      jsonclass = js_object["_class_"]
    except KeyError:
      # default returns dict with keys converted to strings.
      return dict((str(k), v) for k, v in js_object.items())
    else:
      try:
        decoder = self._registry[jsonclass]
      except KeyError:
        raise ValueError("JSON decoder for %r not registered." % (jsonclass,))
      else:
        return decoder(js_object["value"])

  def register(self, name, decoder):
    self._registry[name] = decoder

  def unregister(self, name):
    try:
      del self._registry[name]
    except KeyError:
      pass


# default encoder-decoder. This is all you need.
def GetJSONDecoder():
    # decoding: JSON -> native
  global _DECODER
  if _DECODER is None:
    decoder = JSONObjectDecoder()
    decoder.register("date", _DtDecoder)
    _DECODER =  simplejson.JSONDecoder(object_hook=decoder)
  return _DECODER

def GetJSONEncoder():
    # encoding: native -> JSON
  global _ENCODER
  if _ENCODER is None:
    _ENCODER = JSONEncoder()
    _ENCODER.register("date", _DtChecker, _DtSimplifier)
  return _ENCODER


