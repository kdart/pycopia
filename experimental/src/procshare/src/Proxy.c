/* Proxy.c */

#include "Proxy.h"

PyObject *
GetProxyMap(void)
{
  static PyObject *proxy_map = NULL;

  if (proxy_map != NULL)
	return proxy_map;
  else {
	PyObject *module = NULL, *dict = NULL, *type = NULL;

	/* Import the module "weakref" and instantiate a WeakValueDictionary */
	module = PyImport_ImportModule("weakref");
	if (module != NULL) {
	  dict = PyModule_GetDict(module);
	  if (dict != NULL) {
		type = PyDict_GetItemString(dict, "WeakValueDictionary");
		if (type != NULL)
		  proxy_map = PyObject_CallFunctionObjArgs(type, NULL);
	  }
	}
	Py_XDECREF(module);
	Py_XDECREF(dict);
	Py_XDECREF(type);
	return proxy_map;
  }
}

/*********************************************/
/* Creation and destruction of proxy objects */
/*********************************************/

PyObject *
proxy_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
  ProxyObject *self;
  PyObject *referent;

  if(type == &Proxy_Type) {
	PyErr_Format(PyExc_TypeError, "cannot create '%.100s' instances",
			     type->tp_name);
	return NULL;
  }
  if(!PyArg_ParseTuple(args, "O:Proxy.__new__", &referent))
	return NULL;

  self = (ProxyObject *) type->tp_alloc(type, 0);
  if(self != NULL) {
	/* Set the proxy bit of the referent */
	self->referent = SharedObject_FROM_PYOBJECT(referent);
	SharedObject_SetProxyBit(self->referent);
	/* tp_alloc initialized all fields to 0 */
	assert(self->weakreflist == NULL);
  }
  return (PyObject *) self;
}

static void 
proxy_tp_dealloc(PyObject *self_)
{
  ProxyObject *self = (ProxyObject *) self_;

  /* Notify weak references to the object */
  if (self->weakreflist != NULL)
	PyObject_ClearWeakRefs(self_);
  /* Clear the proxy bit of the referent */
  SharedObject_ClearProxyBit(self->referent);
  /* Free the memory occupied by the object */
  self->ob_type->tp_free(self_);
}

/*****************************/
/* Methods for proxy objects */
/*****************************/

static int
proxy_tp_print(PyObject *self_, FILE *fp, int flags)
{
  ProxyObject *self = (ProxyObject *) self_;

  return SharedObject_Print(self->referent, fp, flags);
}

static int
proxy_tp_compare(PyObject *self_, PyObject *other)
{
  ProxyObject *self = (ProxyObject *) self_;

  return SharedObject_Compare(self->referent, other);
}

static PyObject *
proxy_tp_repr(PyObject *self_)
{
  ProxyObject *self = (ProxyObject *) self_;

  return SharedObject_Repr(self->referent);
}

static long
proxy_tp_hash(PyObject *self_)
{
  ProxyObject *self = (ProxyObject *) self_;

  return SharedObject_Hash(self->referent);
}

static PyObject *
proxy_tp_str(PyObject *self_)
{
  ProxyObject *self = (ProxyObject *) self_;

  return SharedObject_Str(self->referent);
}

static PyObject *
proxy_tp_getattro(PyObject *self_, PyObject *name)
{
  static PyObject *opname = NULL;
  ProxyObject *self = (ProxyObject *) self_;
  PyObject *ref = SharedObject_AS_PYOBJECT(self->referent);
  PyObject *state, *result;
  
  /* Do normal attribute lookup on self, and try again on the referent
	 if it fails. */
  result = PyObject_GenericGetAttr(self_, name);
  if (result == NULL) {
	PyErr_Clear();
	state = SharedObject_EnterString(self->referent, "__getattr__", &opname);
	if (state == NULL)
	  return NULL;
	result = PyObject_GetAttr(ref, name);
	SharedObject_Leave(self->referent, state);
  }
  return result;
}

static int
proxy_tp_setattro(PyObject *self_, PyObject *name, PyObject *value)
{
  static PyObject *opname = NULL;
  ProxyObject *self = (ProxyObject *) self_;
  PyObject *ref = SharedObject_AS_PYOBJECT(self->referent);
  PyObject *state;
  int result;

  state = SharedObject_EnterString(self->referent, "__setattr__", &opname);
  if (state == NULL)
	return -1;
  result = PyObject_SetAttr(ref, name, value);
  SharedObject_Leave(self->referent, state);
  return result;
}

/* Macro to extract the referent object from a proxy object. */
#define UNWRAP(op) \
  if (op != NULL && Proxy_Check(op)) \
    op = SharedObject_AS_PYOBJECT(((ProxyObject *) op)->referent)

/* Maps a tuple of objects to a new tuple where proxy
   objects are substituted with their referents. */
static PyObject *
map_tuple_to_referents(PyObject *tuple)
{
  int i, size = PyTuple_GET_SIZE(tuple);
  PyObject *newtuple, *item;

  if(size == 0) {
	Py_INCREF(tuple);
	return tuple;
  }
  newtuple = PyTuple_New(size);
  if(newtuple == NULL)
	return NULL;
  for(i = 0; i < size; i++) {
	item = PyTuple_GET_ITEM(tuple, i);
	UNWRAP(item);
	/* This may do a normal INCREF on a shared object,
	   but this is allowed, and required to counter the
	   later normal DECREF when the tuple is destroyed. */
	Py_INCREF(item); 
	PyTuple_SET_ITEM(newtuple, i, item);
  }
  return newtuple;
}

/* Maps a dictionary to a new dictionary where proxy object
   values (not keys) are substituted with their referents. */
static PyObject *
map_dict_values_to_referents(PyObject *dict)
{
  PyObject *result, *key, *value;
  int pos = 0;

  result = PyDict_New();
  if (result == NULL)
	return NULL;
  while (PyDict_Next(dict, &pos, &key, &value)) {
	UNWRAP(value);
	if (PyDict_SetItem(result, key, value)) {
	  Py_DECREF(result);
	  return NULL;
	}
  }
  return result;
}

#undef UNWRAP

static char proxy_call_method_doc[] = 
"proxy._call_method(mname, args, kwargs)\n" \
"Calls the named method on the object referred to by the proxy\n" \
"object, using the given positional and keyword arguments.\n" \
"Note that this method takes 3 arguments regardless of how many\n" \
"arguments the named method takes!";

static PyObject *
proxy_call_method(PyObject *self_, PyObject *args)
{
  ProxyObject *self = (ProxyObject *) self_;
  PyObject *ref = SharedObject_AS_PYOBJECT(self->referent);
  /* Borrowed references */
  PyObject *mname;
  PyObject *state;
  PyObject *margs, *mkwargs; /* These are borrowed from the args tuple */
  /* New references */
  PyObject *result = NULL;
  PyObject *meth = NULL;

  /* Parse the arguments */
  if (!PyArg_ParseTuple(args, "SO!O!:call_method", &mname, 
			&PyTuple_Type, &margs, &PyDict_Type, &mkwargs))
      return 0;

  /* Enter the shared object */
  state = SharedObject_Enter(self->referent, mname);
  if (state == NULL)
      goto Error;

  /* Do the actual method call */
  meth = PyObject_GetAttr(ref, mname);
  if (meth != NULL)
      result = PyObject_Call(meth, margs, mkwargs);
  else
      LOGF("method not found");

  /* Leave the shared object */
  SharedObject_Leave(self->referent, state);

  /* If the method call returned self (the referent), return the proxy
     object instead.
     XXX: Sharing the result in all cases would be another approach,
     but it would prohibit shared objects from returning non-shareable
     objects. This is perhaps better anyway? */
  if (result == ref) {
	Py_DECREF(result);
	result = self_;
	Py_INCREF(result);
  }

 Error:
  Py_XDECREF(meth);
  return result;
}

static char proxy_doc[] = "Abstract base type for proxy types.";

static PyMethodDef proxy_tp_methods[] = {
  {"_call_method", proxy_call_method, METH_VARARGS, proxy_call_method_doc},
  {NULL,		NULL}		/* sentinel */
};

PyTypeObject Proxy_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.Proxy",
	sizeof(ProxyObject),
	0,
	proxy_tp_dealloc,   /* tp_dealloc */
	proxy_tp_print, 	/* tp_print */
	0,                  /* tp_getattr */
	0,                  /* tp_setattr */
	proxy_tp_compare,   /* tp_compare */
	proxy_tp_repr,		/* tp_repr */
	0,					/* tp_as_number */
	0,       			/* tp_as_sequence */
	0,					/* tp_as_mapping */
	proxy_tp_hash,      /* tp_hash */
	0,                  /* tp_call */
	proxy_tp_str,       /* tp_str */
	proxy_tp_getattro,  /* tp_getattro */
	proxy_tp_setattro,  /* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	proxy_doc,          /* tp_doc */
 	0,                  /* tp_traverse */
 	0,                  /* tp_clear */
	0,                  /* tp_richcompare */
	offsetof(ProxyObject, weakreflist),	/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	proxy_tp_methods,   /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	0,      			/* tp_init */
	0,                  /* tp_alloc */
	proxy_tp_new,       /* tp_new */
	0,                  /* tp_free */
};
