/* SharedObject.c */

#include "SharedObject.h"
#include "Process.h"
#include "Lock.h"
#include "Globals.h"
#include "share.h"


/* 'Neutral' value for normal reference count */
#define NEUTRAL_OB_REFCNT ((int) (1 << ((sizeof(int)*8-2))))


void 
SharedObject_Init(SharedObject *obj, PyTypeObject *type, int nitems)
{
  PyObject *synch;

  /* Normal initialization of the PyObject part */
  if (type->tp_flags & Py_TPFLAGS_HEAPTYPE)
	Py_INCREF(type);
  if (type->tp_itemsize == 0)
	(void) PyObject_INIT(SharedObject_AS_PYOBJECT(obj), type);
  else
	(void) PyObject_INIT_VAR(SharedObject_AS_PYVAROBJECT(obj), type, nitems);

  /* Initialization specific to shared objects */

  /* The normal reference count has no meaning for shared objects, so
     we set it to a large number to prevent it from interfering with
     our own reference counting scheme.  This makes it safe to pass shared
     objects to functions that are refcount-neutral. */
  obj->pyobj.ob_refcnt = NEUTRAL_OB_REFCNT;

  /* Shared objects start out with a shared reference count of 0.  This
     indicates that there are no references to this object from other
     shared objects.  The process bitmap also starts out blank, since there
     are no proxy objects referring to the object.  Presumably, the
     initialization will be followed by either a SharedObject_IncRef() or a
     SharedObject_SetProxyBit().
  */
  assert(obj->srefcnt == 0);
  assert(ProcessBitmap_IS_ZERO(obj->proxybmp));

  /* Set the flags of the object according to its metatype */  
  synch = PyObject_GetAttrString((PyObject *) type->ob_type, S_SYNCH);
  if (synch == NULL) {
	PyErr_Clear();
	obj->no_synch = 1;
  }
  else {
	if (synch == Py_None)
	  obj->no_synch = 1;
	Py_DECREF(synch);
  }

  /* Initialize the remaining nonzero fields */
  Lock_Init(&obj->lock);
  Spinlock_Init(&obj->reflock);
  obj->dicth = SharedMemHandle_NULL;
}


static void
SharedObject_Dealloc(SharedObject *obj)
{
  PyObject *pyobj = SharedObject_AS_PYOBJECT(obj);

  Spinlock_Destroy(&obj->reflock);
  if (!SharedMemHandle_IS_NULL(obj->dicth)) {
    SharedObject *dict = (SharedObject *)
      SharedMemHandle_AsVoidPtr(obj->dicth);
    if (dict != NULL) {
      SharedObject_DecRef(dict);
    }
    obj->dicth = SharedMemHandle_NULL;
  }
  pyobj->ob_refcnt = 1;
  Py_DECREF(pyobj);
}


void
SharedObject_IncRef(SharedObject *obj)
{
  Spinlock_Acquire(&obj->reflock);
  obj->srefcnt++;
  Spinlock_Release(&obj->reflock);
}


void 
SharedObject_DecRef(SharedObject *obj)
{
  int dealloc;

  Spinlock_Acquire(&obj->reflock);
  obj->srefcnt--;
  dealloc = (obj->srefcnt == 0 && ProcessBitmap_IS_ZERO(obj->proxybmp));
  Spinlock_Release(&obj->reflock);
  if (dealloc)
	SharedObject_Dealloc(obj);
}


void
SharedObject_SetProxyBit(SharedObject *obj)
{
  Spinlock_Acquire(&obj->reflock);
  ProcessBitmap_SET(obj->proxybmp, my_pindex);
  Spinlock_Release(&obj->reflock);
}


void
SharedObject_ClearProxyBit(SharedObject *obj)
{
  int dealloc;

  Spinlock_Acquire(&obj->reflock);
  ProcessBitmap_CLEAR(obj->proxybmp, my_pindex);
  dealloc = (obj->srefcnt == 0 && ProcessBitmap_IS_ZERO(obj->proxybmp));
  Spinlock_Release(&obj->reflock);
  if (dealloc)
	SharedObject_Dealloc(obj);
}


PyObject *
SharedObject_Enter(SharedObject *obj, PyObject *opname)
{
  /* Disallow calls on the object if it is corrupt */
  if (obj->is_corrupt)
	goto Corrupt;

  if (obj->no_synch) {
	Py_INCREF(Py_None);
	return Py_None;
  }
  else {
	PyObject *pyobj = SharedObject_AS_PYOBJECT(obj);
	PyObject *meta_type = (PyObject *) pyobj->ob_type->ob_type;
	PyObject *synch, *result;

	/* Get the __synch__ attribute of the meta-type */
	synch = PyObject_GetAttrString(meta_type, S_SYNCH);
	if (synch == NULL)
	  return NULL;

	/* Call its enter() method */
	result = PyObject_CallMethod(synch, S_ENTER, "OO", pyobj, opname);

	/* The enter() method may have detected that the object is corrupt */
	if (obj->is_corrupt)
	  goto Corrupt;

	return result;
  }

 Corrupt:
  PyErr_SetString(ErrorObject, "shared object may be corrupt");
  return NULL;
}


PyObject *
SharedObject_EnterString(SharedObject *obj, char *opname, 
						 PyObject **opname_cache)
{
  if (opname_cache == NULL) {
	PyObject *str, *result;

	str = PyString_FromString(opname);
	if (str == NULL)
	  return NULL;
	result = SharedObject_Enter(obj, str);
	Py_DECREF(str);
	return result;
  }
  else {
	PyObject *str;

	if (*opname_cache == NULL) {
	  str = PyString_FromString(opname);
	  if (str == NULL)
		return NULL;
	  *opname_cache = str;
	}
	else
	  str = *opname_cache;
	return SharedObject_Enter(obj, str);
  }
}


void 
SharedObject_Leave(SharedObject *obj, PyObject *state)
{
  if (obj->no_synch) {
	Py_DECREF(state);
  }
  else {
	PyObject *pyobj = SharedObject_AS_PYOBJECT(obj);
	PyObject *meta_type = (PyObject *) pyobj->ob_type->ob_type;
	PyObject *synch, *result;
	PyObject *err_type, *err_value, *err_tb;
	int restore = 0;

	if (PyErr_Occurred()) {
	  PyErr_Fetch(&err_type, &err_value, &err_tb);
	  restore = 1;
	}

	/* Get the __synch__ attribute of the meta-type */
	synch = PyObject_GetAttrString(meta_type, S_SYNCH);
	if (synch == NULL)
	  result = NULL;
	else
	  /* Call its leave() method */
	  result = PyObject_CallMethod(synch, S_LEAVE, "OO", pyobj, state);

	Py_DECREF(state);
	Py_XDECREF(result);
	if (result == NULL)
	  PyErr_Clear();
	if (restore)
	  PyErr_Restore(err_type, err_value, err_tb);
  }
}


/* Helper that gets a proxy for the shared dictionary of a shared object. */
static int
get_dict(PyObject *obj, PyObject **dictptr)
{
  SharedObject *shobj = SharedObject_FROM_PYOBJECT(obj);
  SharedObject *shdict;
  PyObject *dict;

  if (SharedMemHandle_IS_NULL(shobj->dicth)) {
	*dictptr = NULL;
	return 0;
  }
  shdict = (SharedObject *) SharedMemHandle_AsVoidPtr(shobj->dicth);
  if (shdict == NULL)
	return -1;
  dict = MakeProxy(shdict);
  if (dict == NULL)
	return -1;
  *dictptr = dict;
  return 0;
}


/* Helper that creates a new empty shared dictionary for a shared object
   and returns a proxy for it. */
static PyObject *
set_empty_dict(PyObject *obj)
{
  SharedObject *shobj = SharedObject_FROM_PYOBJECT(obj);
  SharedObject *shdict;
  PyObject *dict;

  assert(SharedMemHandle_IS_NULL(shobj->dicth));
  dict = PyDict_New();
  if (dict == NULL)
    return NULL;
  shdict = ShareObject(dict);
  if (shdict == NULL)
    return NULL;
  dict = MakeProxy(shdict);
  if (dict == NULL)
    return NULL;
  shobj->dicth = SharedMemHandle_FromVoidPtr(shdict);
  return dict;
}

/* It may be useful to read PEP 252 for understanding the implementation
   of SharedObject_GetAttr() and SharedObject_SetAttr(). They mirror the
   implementation of PyObject_GenericGetAttr() and PyObject_GenericSetAttr()
   found in Objects/object.c */

PyObject *
SharedObject_GetAttr(PyObject *obj, PyObject *name)
{
  PyTypeObject *tp = obj->ob_type;
  PyObject *descr;
  PyObject *res = NULL;
  descrgetfunc f;
  PyObject *dict;

#ifdef Py_USING_UNICODE
  /* The Unicode to string conversion is done here because the
     existing tp_setattro slots expect a string object as name
     and we wouldn't want to break those. */
  if (PyUnicode_Check(name)) {
    name = PyUnicode_AsEncodedString(name, NULL, NULL);
    if (name == NULL)
      return NULL;
  }
  else 
#endif
    if (!PyString_Check(name)){
      PyErr_SetString(PyExc_TypeError,
		      "attribute name must be string");
      return NULL;
    }
    else
      Py_INCREF(name);

  /* Ready the object's type if needed */  
  if (tp->tp_dict == NULL) {
    if (PyType_Ready(tp) < 0)
      goto done;
  }
  
  /* Look for a descriptor in the type */
  descr = _PyType_Lookup(tp, name);
  f = NULL;
  if (descr != NULL) {
    f = descr->ob_type->tp_descr_get;
    if (f != NULL && PyDescr_IsData(descr)) {
      /* Data descriptors in the type override values 
	 in the object's dictionary */
      res = f(descr, obj, (PyObject *)obj->ob_type);
      goto done;
    }
  }

  /* Does the object have a dictionary? */
  if (obj->ob_type->tp_dictoffset) {
    /* Get the object's dictionary */  
    if (get_dict(obj, &dict))
      goto done;
    if (dict != NULL) {
      /* Get the value from the object's dictionary */
      res = PyObject_GetItem(dict, name);
      if (res != NULL)
	goto done;
    }
  }

  /* No object dictionary, or missing key - 
     use the non-data descriptor, if any */
  if (f != NULL) {
    res = f(descr, obj, (PyObject *)obj->ob_type);
    goto done;
  }

  /* Return the descriptor itself as a last resort */  
  if (descr != NULL) {
    Py_INCREF(descr);
    res = descr;
    goto done;
  }

  /* Everything failed - set an AttributeError exception */
  PyErr_Format(PyExc_AttributeError,
	       "'%.50s' object has no attribute '%.400s'",
	       tp->tp_name, PyString_AS_STRING(name));
 done:
  Py_DECREF(name);
  return res;
}


int
SharedObject_SetAttr(PyObject *obj, PyObject *name, PyObject *value)
{
  PyTypeObject *tp = obj->ob_type;
  PyObject *descr;
  descrsetfunc f;
  PyObject *dict;
  int res = -1;

#ifdef Py_USING_UNICODE
  /* The Unicode to string conversion is done here because the
     existing tp_setattro slots expect a string object as name
     and we wouldn't want to break those. */
  if (PyUnicode_Check(name)) {
    name = PyUnicode_AsEncodedString(name, NULL, NULL);
    if (name == NULL)
      return -1;
  }
  else 
#endif
    if (!PyString_Check(name)){
      PyErr_SetString(PyExc_TypeError,
		      "attribute name must be string");
      return -1;
    }
    else
      Py_INCREF(name);
  
  /* Ready the object's type if needed */
  if (tp->tp_dict == NULL) {
    if (PyType_Ready(tp) < 0)
      goto done;
  }
  
  /* Look for a descriptor in the type */
  descr = _PyType_Lookup(tp, name);
  f = NULL;
  if (descr != NULL) {
    f = descr->ob_type->tp_descr_set;
    if (f != NULL && PyDescr_IsData(descr)) {
      /* Data descriptors in the type override values 
	 in the object's dictionary */
      res = f(descr, obj, value);
      goto done;
    }
  }

  /* Does the object have a dictionary? */
  if (obj->ob_type->tp_dictoffset) {
    /* Get the object's dictionary */
    if (get_dict(obj, &dict))
      goto done;
    /* Create a new one if needed */
    if (dict == NULL && value != NULL) {
      dict = set_empty_dict(obj);
      if (dict == NULL)
	goto done;
    }
    if (dict != NULL) {
      /* Assign/delete the value from the dictionary */
      if (value == NULL)
	res = PyMapping_DelItem(dict, name);
      else
	res = PyObject_SetItem(dict, name, value);
      if (res < 0 && PyErr_ExceptionMatches(PyExc_KeyError))
	PyErr_SetObject(PyExc_AttributeError, name);
      goto done;
    }
  }

  /* No object dictionary - use the non-data descriptor, if any */
  if (f != NULL) {
    res = f(descr, obj, value);
    goto done;
  }

  /* Everything failed - set an AttributeError exception */
  if (descr == NULL) {
    PyErr_Format(PyExc_AttributeError,
		 "'%.50s' object has no attribute '%.400s'",
		 tp->tp_name, PyString_AS_STRING(name));
    goto done;
  }
  
  PyErr_Format(PyExc_AttributeError,
	       "'%.50s' object attribute '%.400s' is read-only",
	       tp->tp_name, PyString_AS_STRING(name));
 done:
  Py_DECREF(name);
  return res;
}


PyObject *
SharedObject_Repr(SharedObject *obj)
{
  static PyObject *opname = NULL;
  PyObject *state, *result;

  state = SharedObject_EnterString(obj, "__repr__", &opname);
  result = PyObject_Repr(SharedObject_AS_PYOBJECT(obj));
  SharedObject_Leave(obj, state);
  return result;
}


PyObject *
SharedObject_Str(SharedObject *obj)
{
  static PyObject *opname = NULL;
  PyObject *state, *result;

  state = SharedObject_EnterString(obj, "__str__", &opname);
  result = PyObject_Str(SharedObject_AS_PYOBJECT(obj));
  SharedObject_Leave(obj, state);
  return result;
}


long
SharedObject_Hash(SharedObject *obj)
{
  static PyObject *opname = NULL;
  PyObject *state;
  long result;

  state = SharedObject_EnterString(obj, "__hash__", &opname);
  if (state == NULL)
    return -1;
  result = PyObject_Hash(SharedObject_AS_PYOBJECT(obj));
  SharedObject_Leave(obj, state);
  return result;
}


int
SharedObject_Print(SharedObject *obj, FILE *fp, int flags)
{
  static PyObject *opname = NULL;
  PyObject *state;
  int result;

  state = SharedObject_EnterString(obj, "__print__", &opname);
  if (state == NULL)
    return -1;
  result = PyObject_Print(SharedObject_AS_PYOBJECT(obj), fp, flags);
  SharedObject_Leave(obj, state);
  return result;
}


int
SharedObject_Compare(SharedObject *a, PyObject *b)
{
  static PyObject *opname = NULL;
  PyObject *state;
  int result;

  state = SharedObject_EnterString(a, "__cmp__", &opname);
  if (state == NULL)
    return -1;
  result = PyObject_Compare(SharedObject_AS_PYOBJECT(a), b);
  SharedObject_Leave(a, state);
  return result;
}


PyObject *
SharedObject_RichCompare(SharedObject *a, PyObject *b, int op)
{
  char *opname;
  PyObject *state, *result;

  switch (op) {
  case Py_LT: opname = "__lt__"; break;
  case Py_LE: opname = "__le__"; break;
  case Py_EQ: opname = "__eq__"; break;
  case Py_NE: opname = "__ne__"; break;
  case Py_GT: opname = "__gt__"; break;
  case Py_GE: opname = "__ge__"; break;
  default: return NULL; /* cannot happen */
  }
  
  state = SharedObject_EnterString(a, opname, NULL);
  if (state == NULL)
    return NULL;
  result = PyObject_RichCompare(SharedObject_AS_PYOBJECT(a), b, op);
  SharedObject_Leave(a, state);
  return result;
}


int
SharedObject_RichCompareBool(SharedObject *a, PyObject *b, int op)
{
  char *opname;
  PyObject *state;
  int result;

  switch (op) {
  case Py_LT: opname = "__lt__"; break;
  case Py_LE: opname = "__le__"; break;
  case Py_EQ: opname = "__eq__"; break;
  case Py_NE: opname = "__ne__"; break;
  case Py_GT: opname = "__gt__"; break;
  case Py_GE: opname = "__ge__"; break;
  default: return -1; /* cannot happen */
  }
  
  state = SharedObject_EnterString(a, opname, NULL);
  if (state == NULL)
    return -1;
  result = PyObject_RichCompareBool(SharedObject_AS_PYOBJECT(a), b, op);
  SharedObject_Leave(a, state);
  return result;
}


