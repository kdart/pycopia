/* LockObject.c */

#include "LockObject.h"
#include "Lock.h"

typedef struct {
  PyObject_HEAD
  Lock lock;
} LockObject;

static int
lock_tp_init(PyObject *self_, PyObject *args, PyObject *kwargs)
{
  LockObject *self = (LockObject *) self_;
  LockObject *copy = NULL;
  static char *kwlist[] = {"copy", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O!", kwlist, 
								   &Lock_Type, &copy))
	return -1;
  if (copy != NULL) {
	/* XXX Verify that the lock is unlocked. */
  }
  Lock_Init(&self->lock);
  return 0;
}

static PyObject *
lock_acquire(PyObject *self_, PyObject *noargs)
{
  LockObject *self = (LockObject *) self_;

  if (Lock_Acquire(&self->lock))
	return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
lock_try_acquire(PyObject *self_, PyObject *noargs)
{
  LockObject *self = (LockObject *) self_;
  int success;

  success = !Lock_TryAcquire(&self->lock);
  return PyInt_FromLong(success);
}

static PyObject *
lock_release(PyObject *self_, PyObject *noargs)
{
  LockObject *self = (LockObject *) self_;

  if (Lock_Release(&self->lock))
	return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static char lock_acquire_doc[] =
"lock.acquire() -- acquires the lock; blocks if necessary";

static char lock_try_acquire_doc[] =
"lock.try_acquire() -> bool -- tries to acquire the lock; never blocks";

static char lock_release_doc[] =
"lock.release() -- releases the lock";

static PyMethodDef lock_tp_methods[] = {
	{"acquire", lock_acquire, METH_NOARGS, lock_acquire_doc},
	{"try_acquire", lock_try_acquire, METH_NOARGS, lock_try_acquire_doc},
	{"release", lock_release, METH_NOARGS, lock_release_doc},
	{NULL, NULL} /* sentinel */
};

static char lock_tp_doc[] = "Lock([copy]) -> A new reentrant lock.";

PyTypeObject Lock_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.Lock",
	sizeof(LockObject),
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
	0,          		/* tp_hash */
	0,                  /* tp_call */
	0,               	/* tp_str */
	0,                  /* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	lock_tp_doc,        /* tp_doc */
 	0,                  /* tp_traverse */
 	0,                  /* tp_clear */
	0,                  /* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	lock_tp_methods,    /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	lock_tp_init,       /* tp_init */
	0,                  /* tp_alloc */
	PyType_GenericNew,  /* tp_new */
	0,                  /* tp_free */
};
