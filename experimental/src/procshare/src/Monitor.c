/* Monitor.c */

#include "Monitor.h"
#include "SharedObject.h"
#include "Globals.h"

static PyObject *
enter(PyObject *self, PyObject *args)
{
  PyObject *obj, *opname = NULL;
  SharedObject *shobj;

  /* Parse the arguments, which should be the object and the name of
	 the operation to be performed */
  if (!PyArg_ParseTuple(args, "O|S", &obj, &opname))
	return NULL;
  shobj = SharedObject_FROM_PYOBJECT(obj);

  /* Lock the object's lock */
  if (Lock_Acquire(&shobj->lock))
	return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
leave(PyObject *self, PyObject *args)
{
  PyObject *obj, *ignored = NULL;
  SharedObject *shobj;

  /* Parse the arguments, which are the object and the return value
	 from the enter() call. */
  if (!PyArg_ParseTuple(args, "O|O", &obj, &ignored))
	return NULL;
  shobj = SharedObject_FROM_PYOBJECT(obj);

  /* Unlock the appropriate lock */
  Lock_Release(&shobj->lock);

  Py_INCREF(Py_None);
  return Py_None;
}

static char enter_doc[] =
"M.enter(x) -- Acquires the lock associated with x.";

static char leave_doc[] =
"M.leave(x) -- Releases the lock associated with x.";

static PyMethodDef tp_methods[] = {
  {"enter", enter, METH_VARARGS, enter_doc},
  {"leave", leave, METH_VARARGS, leave_doc},
  {NULL, NULL} /* sentinel */
};

static char tp_doc[] =
"Synchronization manager that enforces monitor access semantics.";

PyTypeObject Monitor_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.Monitor",
	sizeof(PyObject),
	0,
	0,                  /* tp_dealloc */
	0,                  /* tp_print */
	0,                  /* tp_getattr */
	0,                  /* tp_setattr */
	0,                  /* tp_compare */
	0,                  /* tp_repr */
	0,					/* tp_as_number */
	0,       			/* tp_as_sequence */
	0,					/* tp_as_mapping */
	0,                  /* tp_hash */
	0,                  /* tp_call */
	0,                  /* tp_str */
	0,                  /* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	tp_doc,             /* tp_doc */
 	0,                  /* tp_traverse */
 	0,                  /* tp_clear */
	0,                  /* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	tp_methods,         /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	0,      			/* tp_init */
	0,                  /* tp_alloc */
	PyType_GenericNew,  /* tp_new */
	0,                  /* tp_free */
};

