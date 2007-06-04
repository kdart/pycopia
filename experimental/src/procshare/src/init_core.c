/* init_procshare_core.c */
/* Initialization of the _procshare_core module. */

#include "_core.h"
#include "Process.h"
#include "SharedRegion.h"
#include "SharedAlloc.h"
#include "Proxy.h"
#include "SharedHeap.h"
#include "SharedListAndTuple.h"
#include "SharedDictBase.h"
#include "SharedObject.h"
#include "share.h"
#include "Address.h"
#include "Monitor.h"
#include "LockObject.h"

PyObject *ErrorObject = NULL;
PyObject *TypeMap = NULL;

/* Returns the address of the given object as an Address object. */
static PyObject *
address_of(PyObject *null, PyObject *obj)
{
  return Address_FromVoidPtr(obj);
}

/* Maps a regular type to a shared type, proxy type and initializer */
static PyObject *
register_type(PyObject *null, PyObject *args)
{
  PyObject *tp, *stp, *ptp, *init, *tuple;
  
  /* Parse the arguments, which should be three types and a function */
  if(!PyArg_ParseTuple(args, "O!O!O!O!:map_type", &PyType_Type, &tp,
	    &PyType_Type, &stp, &PyType_Type, &ptp, &PyFunction_Type, &init))
	return NULL;

  /* Build a tuple of the shared type, proxy type and initializer */
  tuple = Py_BuildValue("(OOO)", stp, ptp, init);
  if (tuple == NULL)
	return NULL;

  /* Map the regular type to the tuple */
  if (PyDict_SetItem(TypeMap, tp, tuple)) {
	Py_DECREF(tuple);
	return NULL;
  }
  /* Also map the shared type to the tuple */
  if (PyDict_SetItem(TypeMap, stp, tuple)) {
	Py_DECREF(tuple);
	return NULL;
  }
  
  Py_DECREF(tuple);
  Py_INCREF(Py_None);
  return Py_None;
}

/* Shares an object and returns a proxy object for it. */
static PyObject *share(PyObject *null, PyObject *obj)
{
  SharedObject *shobj;

  shobj = ShareObject(obj);
  if(shobj == NULL)
	return NULL;
  return MakeProxy(shobj);
}

/* Initializes a recently forked child process */
static PyObject *
init_child(PyObject *null, PyObject *noargs)
{
  PyObject *map, *values;
  int i, len;

  if (Process_Init()) {
	PyErr_SetString(ErrorObject, "too many processes");
	return NULL;
  }
  map = GetProxyMap();
  if (map == NULL)
	return NULL;
  values = PyMapping_Values(map);
  if (values == NULL)
	return NULL;
  len = PySequence_Length(values);
  for (i = 0; i < len; i++) {
	PyObject *item = PySequence_GetItem(values, i);
	assert(Proxy_Check(item));
	SharedObject_SetProxyBit(((ProxyObject *) item)->referent);
	Py_DECREF(item);
  }
  Py_INCREF(Py_None);
  return Py_None;
}

/* Handles the death of a child process */
static PyObject *
child_died(PyObject *null, PyObject *args)
{
  int pid, killsignal, status, corefile;

  if (!PyArg_ParseTuple(args, "iiii:child_died", 
					   &pid, &killsignal, &status, &corefile))
	return NULL;
  if (killsignal != 0 || status != 0)
	Process_CleanupChild(pid);
  Py_INCREF(Py_None);
  return Py_None;
}

/* Overrides the allocation methods of a type to use
 * SharedObject_Alloc and SharedObject_Free. */
static PyObject *
override_allocation(PyObject *null, PyObject *args)
{
  PyTypeObject *type;

  if (!PyArg_ParseTuple(args, "O!:override_allocation", &PyType_Type, &type))
	return NULL;

  /* Override tp_alloc and tp_free; there are no descriptors for these, so
	 it's only a matter of updating the slots directly. */
  type->tp_alloc = SharedObject_Alloc;
  type->tp_free = SharedObject_Free;
  /* SharedObject_Alloc() and SharedObject_Free() don't support
	 cyclic garbage collection, so the new type can't be
	 garbage collected */
  type->tp_flags &= ~Py_TPFLAGS_HAVE_GC;

  Py_INCREF(Py_None);
  return Py_None;
}

/* Returns true if the given type overrides __getattr__, 
   __getattribute__, __setattr__ or __delattr__. */
static PyObject *
overrides_attributes(PyObject *null, PyObject *args)
{
  PyTypeObject *type;
  PyObject *desc = NULL;
  PyObject *result = NULL;

  if (!PyArg_ParseTuple(args, "O!:override_allocation", &PyType_Type, &type))
	goto Done;

  if ((type->tp_setattr != 0 && 
       type->tp_setattr != PyBaseObject_Type.tp_setattr) ||
      (type->tp_setattro != 0 && 
       type->tp_setattro != PyBaseObject_Type.tp_setattro)) {
    /* Overrides __setattr__ / __delattr__ */
    result = Py_True;
    goto Done;
  }
  if ((type->tp_getattr != 0 &&
       type->tp_getattr != PyBaseObject_Type.tp_getattr)
      || (type->tp_getattr != 0 && 
          type->tp_getattro != PyBaseObject_Type.tp_getattro)) {
    /* Overrides __getattribute__ and/or __getattr__.
       The latter is allowed, so we have to find out which it is. */
    desc = PyObject_GetAttrString((PyObject *) type, "__getattribute__");
    if (desc==NULL)
      goto Done;
    if (desc->ob_type == &PyWrapperDescr_Type) {
      void *wrapped = ((PyWrapperDescrObject *) desc)->d_wrapped;
      if (wrapped == (void *) PyBaseObject_Type.tp_getattro) {
        /* Only overrides __getattr__, which is fine. */
        result = Py_False;
        goto Done;
      }
    }
    result = Py_True;
    goto Done;
  }
  result = Py_False;

 Done:
  Py_XDECREF(desc);
  Py_XINCREF(result);
  return result;
}

static PyObject *
shared_getattribute(PyObject *null, PyObject *args)
{
  PyObject *self, *name;

  if (!PyArg_ParseTuple(args, "OO", &self, &name))
	return NULL;
  return SharedObject_GetAttr(self, name); 
}

static PyObject *
shared_setattr(PyObject *null, PyObject *args)
{
  PyObject *self, *name, *value;

  if (!PyArg_ParseTuple(args, "OOO", &self, &name, &value))
	return NULL;
  if (SharedObject_SetAttr(self, name, value))
	return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
shared_delattr(PyObject *null, PyObject *args)
{
  PyObject *self, *name;

  if (!PyArg_ParseTuple(args, "OO", &self, &name))
	return NULL;
  if (SharedObject_SetAttr(self, name, NULL))
	return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static char address_of_doc[] =
"address_of(obj) -> The object's address in memory";
static char register_type_doc[] =
"register_type(tp, stp, ptp, init)";
static char share_doc[] =
"share(obj) -> Proxy object for a shared object equal to obj";
static char init_child_doc[] =
"init_child()";
static char child_died_doc[] =
"child_died(pid, killsignal, status, corefile)";
static char override_allocation_doc[] =
"override_allocation(type)";
static char overrides_attributes_doc[] =
"overrides_attributes(type) -> True if type overrides __getattribute__, "\
"__setattr__ or __delattr__";
static char shared_getattribute_doc[] =
"__getattribute__ for shared objects";
static char shared_setattr_doc[] =
"__setattr__ for shared objects";
static char shared_delattr_doc[] =
"__delattr__ for shared objects";


/* List of functions defined in the module */
static PyMethodDef functions[] = {
  {"address_of", address_of, METH_O, address_of_doc},
  {"register_type", register_type, METH_VARARGS, register_type_doc},
  {"share", share, METH_O, share_doc},
  {"init_child", init_child, METH_NOARGS, init_child_doc},
  {"child_died", child_died, METH_VARARGS, child_died_doc},
  {"override_allocation", override_allocation, METH_VARARGS, 
   override_allocation_doc},
  {"overrides_attributes", overrides_attributes, METH_VARARGS, 
   overrides_attributes_doc},
  {"shared_getattribute", shared_getattribute, METH_VARARGS,
   shared_getattribute_doc},
  {"shared_setattr", shared_setattr, METH_VARARGS, shared_setattr_doc},
  {"shared_delattr", shared_delattr, METH_VARARGS, shared_delattr_doc},
  {NULL, NULL} /* sentinel */
};

/* Initialization function for the module (*must* be called init_procshare_core) */
DL_EXPORT(void)
init_procshare_core(void)
{
  PyObject *m, *d, *nulladdr, *type_map;
  int ok;

  if (Process_Init())
	goto Error;

  /* Create the error object for the module */  
  ErrorObject = PyErr_NewException("_procshare_core.Error", NULL, NULL);
  if (ErrorObject == NULL)
	goto Error;

  /* Create the type map */
  TypeMap = PyDict_New();
  if (TypeMap == NULL)
	goto Error;

  /* Ready built-in types */
  PyType_Ready(&Address_Type);
  PyType_Ready(&SharedHeap_Type);
  PyType_Ready(&SharedListBase_Type);
  PyType_Ready(&SharedTupleBase_Type);
  PyType_Ready(&SharedDictBase_Type);
  PyType_Ready(&Proxy_Type);
  PyType_Ready(&Monitor_Type);
  PyType_Ready(&Lock_Type);

  /* Create the module and get its dictionary */
  m = Py_InitModule("_procshare_core", functions);
  if (m == NULL)
	goto Error;
  d = PyModule_GetDict(m);
  if (d == NULL)
	goto Error;

  /* Add symbols to the module */
  nulladdr = Address_FromVoidPtr(NULL);
  if (nulladdr == NULL)
	goto Error;
  ok = !PyDict_SetItemString(d, "null", nulladdr);
  Py_DECREF(nulladdr);

  type_map = PyDictProxy_New(TypeMap);
  if (type_map == NULL)
	goto Error;
  ok = ok && !PyDict_SetItemString(d, "type_map", type_map);
  Py_DECREF(type_map);

  ok = ok && !PyDict_SetItemString(d, "Error", ErrorObject);
  ok = ok && !PyDict_SetItemString(d, "SharedHeap", 
								   (PyObject *) &SharedHeap_Type);
  ok = ok && !PyDict_SetItemString(d, "SharedListBase",
								   (PyObject *) &SharedListBase_Type);
  ok = ok && !PyDict_SetItemString(d, "SharedTupleBase",
								   (PyObject *) &SharedTupleBase_Type);
  ok = ok && !PyDict_SetItemString(d, "SharedDictBase",
								   (PyObject *) &SharedDictBase_Type);
  ok = ok && !PyDict_SetItemString(d, "Proxy", (PyObject *) &Proxy_Type);
  ok = ok && !PyDict_SetItemString(d, "Monitor", (PyObject *) &Monitor_Type);
  ok = ok && !PyDict_SetItemString(d, "Lock", (PyObject *) &Lock_Type);

  if (ok)
	return;

 Error:
  Py_XDECREF(ErrorObject);
  Py_XDECREF(TypeMap);
  if (PyErr_Occurred() == NULL)
	PyErr_SetString(PyExc_ImportError, "module initialization failed");
}
