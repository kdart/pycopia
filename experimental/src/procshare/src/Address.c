/* Address.c */

#include "Address.h"

typedef struct {
  PyObject_HEAD
  void *ptr;
} AddressObject;

static int tp_compare(PyObject *self_, PyObject *other_)
{
  AddressObject *self = (AddressObject *) self_;
  AddressObject *other = (AddressObject *) other_;

  if(self->ptr < other->ptr)
	return -1;
  if(self->ptr > other->ptr)
	return 1;
  return 0;
}

static long tp_hash(PyObject *self)
{
  return _Py_HashPointer(((AddressObject *) self)->ptr);
}

static PyObject *
tp_str(PyObject *self)
{
  char buf[20];
  PyOS_snprintf(buf, sizeof(buf), "%p", ((AddressObject *) self)->ptr);
  return PyString_FromString(buf);
}

static char tp_doc[] = "Encapsulates a memory address.";

PyTypeObject Address_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.Address",
	sizeof(AddressObject),
	0,
	0,                  /* tp_dealloc */
	0,                  /* tp_print */
	0,                  /* tp_getattr */
	0,                  /* tp_setattr */
	tp_compare,         /* tp_compare */
	0,                  /* tp_repr */
	0,					/* tp_as_number */
	0,       			/* tp_as_sequence */
	0,					/* tp_as_mapping */
	tp_hash,     		/* tp_hash */
	0,                  /* tp_call */
	tp_str,          	/* tp_str */
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
	0,                  /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	0,      			/* tp_init */
	0,                  /* tp_alloc */
	0,                  /* tp_new */
	0,                  /* tp_free */
};

PyObject *
Address_FromVoidPtr(void *ptr)
{
  AddressObject *self = PyObject_New(AddressObject, &Address_Type);
  self->ptr = ptr;
  return (PyObject *) self;
}

void *
Address_AsVoidPtr(PyObject *self)
{
  return ((AddressObject *) self)->ptr;
}
