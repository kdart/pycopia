/* Transparently proxy Javascript methods to and from Python methods.
 * Requires MochiKit.js to be loaded first.
 */

/**
 * PythonProxy works with json.JSONDispatcher to transparently call
 * functions on the server side, and return the function's return value.
 * This should be mapped with a URL map of the form
 * "/base/path/(?P<methodname>\w+)/" to a json.JSONDispatcher
 * instance on the server side. The PythonProxy object, when instantiated,
 * automatically fills in extra methods mapped to the functions that
 * JSONDispatcher exports. They will have the same name. Then call any one
 * of these new methods with any object serializable to JSON. If there is
 * one parameter, and it is an Object, then it will be mapped to Python
 * keyword arguments on the server.
 *
 * However, since this needs to be asynchronous they return a Deferred
 * that you add a callback to get the return value from the function. Your
 * callback gets whatever the server side function returns, as native
 * objects.
 *
 * Signals "proxyready" when methods are ready to use.
 */
function PythonProxy(basepath) {
  this.initialized = false;
  this.basepath = basepath;
  bindMethods(this);
  // Fetch the dispatchers registered names, add them to this object.
  // You may then use the same names as methods on this PythonProxy
  // instance.
  var req = this._call("_methods");
  req.addCallback(this._fillMethods);
};

/**
 *  Method caller of PythonProxy.
 * @param {String} methodname name of the registered function that the
 * JSONDispatcher will call.
 * @param {Object} obj An Object that will map to Python keywords
 * arguments for the method called.
 * @return {Deferred} d a Deffered that will callback data returned from
 * server function.
 */

PythonProxy.prototype._call = function(methodname /* more */) {
  var url = this.basepath + methodname;
  var req = doXHR(url, {
                  method: "POST",
                  mimeType: 'text/plain',
                  headers: {"Content-Type": "application/x-www-form-urlencoded"},
                  sendContent: queryString({
                    "data": serializeJSON(arguments)
                  })
                });
  req.addCallbacks(evalProxyJSONRequest, this._exception);
  return req;
};

PythonProxy.prototype._exception = function(pyerror) {
  var exclist = evalJSONRequest(pyerror.req);
  var exc = exclist[0];
  var val = exclist[1];
  // list of tuples (filename, line_number, function_name, text) 
  var tracebacklist = exclist[2];
  console.error(exc, val, tracebacklist); 
  throw new Error(exc + val); // TODO something nicer here?
};

/**
 * Helper for PythonProxy that fills in methods in the new object,
 * dynamically, with proxy methods having the same names as the server
 * side json handlers.
 */
PythonProxy.prototype._fillMethods = function(methodlist) {
  for (var i = 0; i < methodlist.length; i++) {
    name = methodlist[i];
    this[name] = partial(this._call, name);
  };
  this.initialized = true;
  signal(this, "proxyready");
};


/**
 * Special JSON evaluator handles embedded special objects in tree.
 * @param {Request} req an XMLHttpRequest to be evaluated as JSON
 * response. This is a part of extensible JSON deserialization that can
 * handle any registered objects. 
 * @return {Any} an object ot set of objects.
 */
function evalProxyJSONRequest(req) {
  var obj = evalJSON(req.responseText);
  var newobj = null;
  newobj = convertClasses(obj);
  return newobj;
};

/**
 * Recursive function to find special Object (has _class_ attribute) an
 * replace them with converted object.
 */

function convertClasses(o) {
  var objtype = typeof(o);
  var me = arguments.callee;

  if (isArrayLike(o)) {
    var newarr = [];
    for (var i = 0; i < o.length; i++) {
      var val = me(o[i]);
      newarr.push(val);
    };
    return newarr;
  } else if (objtype == "object") {
    if (isUndefinedOrNull(o)) {
      return o;
    // special objects have _class_ attribute.
    } else if (o["_class_"] == null) { 
      var temp = items(o);
      for (var i = 0; i < temp.length; i++) {
        o[temp[i][0]] = me(temp[i][1]);
      };
      return o;
    } else {
      return jsonEvalRegistry.match(o);
    };
  } else {
    return o;
  };
};


/** 
 * Support for Date serialization (not part of standard conversions,
 * unfortunately).
 */

// For Date -> JSON
function jsonCheckDatetime(obj) {
  return (obj instanceof Date);
};

function simplifyDatetime(dt) {
  return {_class_: "datetime", value: dt.getTime()};
};


// For JSON -> datetime object
function jsonDecodeCheckDatetime(obj) {
  return obj._class_ == "datetime";
};

function jsonConvertDatetime(obj) {
  return new Date(obj.value);
};


/// date objects
function jsonCheckDate(obj) {
  return (obj instanceof Date) && (obj.getUTCHours() == 0);
};

function simplifyDate(dt) {
  return {_class_: "date", value: dt.getTime()};
};

function jsonDecodeCheckDate(obj) {
  return obj._class_ == "date";
};

function jsonConvertDate(obj) {
  var newdate = new Date(obj.value);
  return newdate;
};
/// end date objects

// Mimic Python set type
function Set(arr) {
  for (var i = 0; i < arr.length; i++) {
    this[arr[i]] = null;
  };
}
Set.prototype = new Object();
Set.prototype.constructor = Set;

Set.prototype.contains = function(v) {
  return this.hasOwnProperty(v);
};


// For Set --> JSON
function jsonCheckSet(obj) {
  return (typeof(obj) == "object") && (obj.constructor == Set);
};

function simplifySet(s) {
  var l = [];
  for (var k in s) {l.push(k);};
  return {_class_: "set", value: l};
};

// For JSON -> Set
function jsonDecodeCheckSet(obj) {
  return obj._class_ == "set";
};

function jsonConvertSet(obj) {
  var theset = new Set(obj.value);
  return theset;
};

// Mirror pycopia Enum type
function Enum(value, str) {
    this._str_ = str;
    this.value = value;
}
Enum.prototype = new Object();
Enum.prototype.constructor = Enum;

Enum.prototype.toString = function() {
  return this._str_;
};

// For pycopia.aid.Enum --> JSON
function jsonCheckEnum(obj) {
  return (typeof(obj) == "object") && (obj.constructor == Enum);
};

function simplifyEnum(o) {
  return {_class_: "Enum", value: {"value":o.value, "_str_":o._str_}};
};

// For JSON -> pycopia.aid.Enum
function jsonDecodeCheckEnum(obj) {
  return obj._class_ == "Enum";
};

function jsonConvertEnum(obj) {
  return new Enum(obj.value, obj._str_);
};



function proxyInit() {
  registerJSON("datetime", jsonCheckDatetime, simplifyDatetime);
  registerJSON("date", jsonCheckDate, simplifyDate);
  registerJSON("set", jsonCheckSet, simplifySet);
  registerJSON("enum", jsonCheckEnum, simplifyEnum);
  // Create a new registry for special JSON deserialization handlers.
  window.jsonEvalRegistry = new AdapterRegistry();
  // and add first handler, a Date handler.
  jsonEvalRegistry.register("datetime", jsonDecodeCheckDatetime, jsonConvertDatetime);
  jsonEvalRegistry.register("date", jsonDecodeCheckDate, jsonConvertDate);
  jsonEvalRegistry.register("set", jsonDecodeCheckSet, jsonConvertSet);
  jsonEvalRegistry.register("enum", jsonDecodeCheckEnum, jsonConvertEnum);
};

// connect(window, "onload", proxyInit);

proxyInit();

