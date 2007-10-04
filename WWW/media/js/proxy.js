/* Transparently proxy Javascript methods to and from Python methods.
 * Requires MochiKit.js to be loaded first.
 */

/**
 * PythonProxy works with views_base.JSONDispatcher to transparently call
 * functions on the server side, and return the function's return value.
 * This should be mapped with a URL map of the form
 * "/base/path/(?P<methodname>\w+)/" to a views_base.JSONDispatcher
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
 */
function PythonProxy(basepath) {
  this.basepath = basepath;
  // Fetch the dispatchers registered names, add them to this object.
  // You may then use the same names as methods on this PythonProxy
  // instance.
  var req = this._call("_methods");
  req.addCallback(partial(_fillMethods, this));
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
  var url = this.basepath + methodname + "/";
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
  // Note: console object provided by firebug extension.
  throw new Error(exc + val); // TODO something nicer here?
};

/**
 * Helper for PythonProxy that fills in methods in the new object,
 * dynamically, with proxy methods having the same names as the server
 * side json handlers.
 */
function _fillMethods(obj, methodlist) {
  for (var i = 0; i < methodlist.length; i++) {
    name = methodlist[i];
    obj[name] = partial(obj._call, name);
  };
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
  try {
    var newobj = convertClasses(obj);
  } catch (e) {
    console.error(e);
  };
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
        var value = me(temp[i][1]);
        o[temp[i][0]] = value;
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
function jsonCheckDate(obj) {
  return (typeof(obj) == "date");
};

function simplifyDate(dt) {
  return {_class_: "date", value: dt.getTime()};
};

// For JSON -> Date object
function jsonDecodeCheckDate(obj) {
  return obj._class_ == "date";
};

function jsonConvertDate(obj) {
  var newdate = new Date(obj.value);
  return newdate;
};


function proxyInit() {
  registerJSON("date", jsonCheckDate, simplifyDate);
  // Create a new registry for special JSON deserialization handlers.
  window.jsonEvalRegistry = new AdapterRegistry();
  // and add first handler, a Date handler.
  jsonEvalRegistry.register("date", jsonDecodeCheckDate, jsonConvertDate);
};

// Initialize after page load.
connect(window, "onload", proxyInit);


