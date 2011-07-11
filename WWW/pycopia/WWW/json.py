#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=2:sw=2:softtabstop=0:tw=74:smarttab:expandtab

"""
Provides transparent RPC between Javascript and Python, using JSON
encoding.
"""

import sys
import time
import traceback
from datetime import datetime, date
import simplejson

from pycopia import aid
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


### functions for handling datetime/date <=> Date conversion.
def _DtChecker(obj):
  return type(obj) is datetime

def _DtSimplifier(dt):
  return {"_class_": "datetime",
      "value": long(time.mktime(dt.timetuple())*1000)}

def _DtDecoder(timestamp):
  return datetime.fromtimestamp(float(timestamp)/1000.0)


def _DateChecker(obj):
  return type(obj) is date

def _DateSimplifier(dt):
  return {"_class_": "date",
      "value": long(time.mktime(dt.timetuple())*1000)}

def _DateDecoder(timestamp):
  return date.fromtimestamp(float(timestamp)/1000.0)

### End datetime conversions ###

### set encoding ###
def _set_checker(obj):
  return isinstance(obj, set)

def _set_simplifier(s):
  return {"_class_": "set",
      "value": list(s),
      }

def _set_decoder(s):
  return set(s)

### Enum conversion ###

def _enum_checker(obj):
    return isinstance(obj, aid.Enum)

def _enum_simplifier(obj):
    return {"_class_": "Enum",
            "_str_": str(obj),
            "value": int(obj)}

def _enum_decoder(d):
    return aid.Enum(int(d["value"]), d["_str_"])

### End Enum conversions ###

class JSONEncoder(simplejson.JSONEncoder):
  def __init__(self):
    super(JSONEncoder, self).__init__(ensure_ascii=False, encoding="utf-8")
    self._registry = {}

  def default(self, obj):
    for checker, simplifier in self._registry.itervalues():
      if checker(obj):
        return simplifier(obj)
    return super(JSONEncoder, self).default(obj)

#  def encode(self, obj):
#    for checker, simplifier in self._registry.itervalues():
#      if checker(obj):
#        return super(JSONEncoder, self).encode(simplifier(obj))
#    return super(JSONEncoder, self).encode(obj)

  def register(self, name, check, simplifier):
    self._registry[name] = (check, simplifier)

  def unregister(self, name):
    try:
      del self._registry[name]
    except KeyError:
      pass


# manage a global request reference for those JSON handlers that want access to the
# original request.

current_request = None

class GlobalRequest(object):

  def __init__(self, request):
    global current_request
    current_request = request

  def __enter__(self):
    global current_request
    return current_request

  def __exit__(self, type, value, traceback):
    global current_request
    current_request = None


class JSONDispatcher(object):
  """Pair with PythonProxy javascript object.

  Use this to call Python functions from javascript, with arguments and
  returns values transparently transported using JSON serialization.

  Requires a URL mapping of the form::

     (r'^base/path/(?P<methodname>\w+)$', 'views_module.dispatcher'),

  Your view.py will then have a line like this::

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
    keys = self._fmap.keys()
    keys.remove("_methods")
    return keys

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
          request.log_error("JSONDispatcher args: %s (%s)\n" % (ex, val))
          return JSONServerError(ex, val, tblist)
      else:
        args = ()
        kwargs = {}
      with GlobalRequest(request):
        rv = handler(*args, **kwargs)
      json = self._encoder.encode(rv)
      return HttpResponse(json, "application/json")
    except: # all exceptions are sent back to client.
      ex, val, tb = sys.exc_info()
      tblist = traceback.extract_tb(tb)
      del tb
      request.log_error("JSONDispatcher: %s (%s)\n" % (ex, val))
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
    decoder.register("datetime", _DtDecoder) # pre-register datetime objects
    decoder.register("date", _DateDecoder) # pre-register date objects
    decoder.register("set", _set_decoder) # pre-register set objects
    decoder.register("Enum", _enum_decoder) # pre-register Enum objects
    _DECODER =  simplejson.JSONDecoder(object_hook=decoder)
  return _DECODER

def GetJSONEncoder():
    # encoding: native -> JSON
  global _ENCODER
  if _ENCODER is None:
    _ENCODER = JSONEncoder()
    _ENCODER.register("datetime", _DtChecker, _DtSimplifier)
    _ENCODER.register("date", _DateChecker, _DateSimplifier)
    _ENCODER.register("set", _set_checker, _set_simplifier)
    _ENCODER.register("enums", _enum_checker, _enum_simplifier)
  return _ENCODER


