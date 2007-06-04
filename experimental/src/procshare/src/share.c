/* share.c */

#include "share.h"
#include "Proxy.h"
#include "SharedObject.h"
#include "Address.h"

SharedObject *
ShareObject(PyObject *obj)
{
  /* Borrowed references */
  PyTypeObject *type = obj->ob_type;
  PyObject *tuple, *stp, *init;

  /* Special-case proxy objects */
  if(Proxy_Check(obj))
	return ((ProxyObject *) obj)->referent;

  /* Special-case singletons None, True and False */
  if(obj == Py_None) {
  }
  else if(obj == Py_True) {
  }
  else if(obj == Py_False) {
  }

  /* Get the type's entry in the type map */
  tuple = PyDict_GetItem(TypeMap, (PyObject *) type);
  if(tuple == NULL) {
	PyErr_Format(ErrorObject, "%.100s instances cannot be shared",
				 type->tp_name);
	return NULL;
  }
  assert(PyTuple_Check(tuple));
  assert(PyTuple_GET_SIZE(tuple) == 3);
  stp = PyTuple_GET_ITEM((PyObject *) tuple, 0);
  init = PyTuple_GET_ITEM((PyObject *) tuple, 2);

  /* If the type is its own shared type, the object is already shared. */
  if(stp == (PyObject *) type)
	return SharedObject_FROM_PYOBJECT(obj);

  /* Create the shared object by calling the initialization function. */
  /*  LOGF("Instantiating %.100s object", 
	  ((PyTypeObject *) shtype)->tp_name); */
  obj = PyObject_CallFunctionObjArgs(init, stp, obj, NULL);
  if(obj == NULL)
	return NULL;
  return SharedObject_FROM_PYOBJECT(obj);
}

/* Creates a new proxy object for a shared object */
static PyObject *
new_proxy(SharedObject *obj)
{
  /* Borrowed references */
  PyObject *pyobj = SharedObject_AS_PYOBJECT(obj);
  PyTypeObject *type = pyobj->ob_type;
  PyObject *tuple, *ptype;

  /* Get the shared type's entry in the type map */
  tuple = PyDict_GetItem(TypeMap, (PyObject *) type);
  if(tuple == NULL) {
	PyErr_Format(ErrorObject, "no proxy type for %.100s", type->tp_name);
	return NULL;
  }
  assert(PyTuple_Check(tuple));
  assert(PyTuple_GET_SIZE(tuple) == 3);
  ptype = PyTuple_GET_ITEM(tuple, 1);

  /* Instantiate the new proxy object */
  return PyObject_CallFunctionObjArgs(ptype, pyobj, NULL);
}

/* Looks in the procy map for a proxy object for the shared object, or
   creates a new proxy object if there is none. */
PyObject *
MakeProxy(SharedObject *obj)
{
  /* New references */
  PyObject *addr = NULL, *proxy = NULL;
  /* Borrowed references */
  PyObject *map;

  map = GetProxyMap();
  if (map == NULL)
	goto Done;
  addr = Address_FromVoidPtr(obj);
  if (addr == NULL)
	goto Done;
  proxy = PyObject_GetItem(map, addr);
  if (proxy != NULL)
	/* Found an existing proxy object */
	goto Done;

  /* Clear the KeyError from the failed lookup */
  if (!PyErr_ExceptionMatches(PyExc_KeyError))
	goto Done; /* Other exceptions are passed on */
  PyErr_Clear();

  /* Create a new proxy object */
  proxy = new_proxy(obj);
  if (proxy != NULL) {
	/* Store the new proxy object in the proxy map */
	if (PyObject_SetItem(map, addr, proxy)) {
	  Py_DECREF(proxy);
	  proxy = NULL;
	}
  }
  else {
	/* Creation of the proxy object failed. In case the shared object has
	   no other proxy objects, and no references to it from other shared
	   objects, we should call SharedObject_ClearProxyBit() to let it be
	   reclaimed. */
	SharedObject_ClearProxyBit(obj);
  }

 Done:
  Py_XDECREF(addr);
  return proxy;
}

