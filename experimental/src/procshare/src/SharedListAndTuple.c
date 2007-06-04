/* SharedListAndTuple.c */

#include "SharedListAndTuple.h"
#include "Handle.h"
#include "SharedObject.h"
#include "SharedAlloc.h"
#include "share.h"

typedef struct
{
  PyObject_VAR_HEAD
  int capacity;
  SharedMemHandle vectorh;
} SharedListBaseObject;

typedef struct
{
  PyObject_VAR_HEAD
  SharedMemHandle vector[1];
} SharedTupleBaseObject;

/***********************************************/
/* COMMON ROUTINES FOR SHARED LISTS AND TUPLES */
/***********************************************/

/* Parses an argument list consisting of a single sequence argument */
static int
arg_sequence(PyObject *args, char *funcname, PyObject **seq, int *size)
{
  static char fmt[110];
  PyObject *obj;

  PyOS_snprintf(fmt, sizeof(fmt), "O:%.100s", funcname);
  if(!PyArg_ParseTuple(args, fmt, &obj))
	return -1;
  if(!PySequence_Check(obj)) {
	PyErr_Format((PyObject *) PyExc_TypeError,
				 "%.100s expects a sequence", funcname);
	return -1;
  }
  *seq = obj;
  *size = PySequence_Length(obj);
  return 0;
}

static int
common_sq_length(PyObject *self_)
{
  PyVarObject *self = (PyVarObject *) self_;
  return self->ob_size;
}

/* VECTOR IMPLEMENTATION
   A vector in this context (this file) is an array of handles to
   shared objects. Both SharedListBase and SharedTupleBase objects
   are implemented using a vector. SharedListBase objects contain
   a handle to a vector, while SharedListTuple objects, which are
   immutable, have a vector embedded in them.
 */

/* Deinitializes a vector of shared objects */
static void
vector_deinit(SharedMemHandle *vector, int size)
{
  int i;
  SharedObject *obj;

  for(i = 0; i < size; i++) {
	obj = (SharedObject *) SharedMemHandle_AsVoidPtr(vector[i]);
	SharedObject_DecRef(obj);
  }
}

/* Initializes a vector of shared objects from a sequence */
static int
vector_init(SharedMemHandle *vector, PyObject *seq, int size)
{
  /* New references */
  PyObject *item;
  SharedObject *shared_item;

  int i;
  size_t bytes;

  /* Fill in the vector by sharing the items of the sequence */
  for(i = 0; i < size; i++) {
	item = PySequence_GetItem(seq, i);
	if(item == NULL)
	  goto Error;
	shared_item = ShareObject(item);
	Py_DECREF(item);
	if(shared_item == NULL)
	  goto Error;
	SharedObject_IncRef(shared_item);
	vector[i] = SharedMemHandle_FromVoidPtr(shared_item);
  }
  return 0;
  
 Error:
  vector_deinit(vector, i-1);
  return -1;
}

static PyObject *
vector_item(SharedMemHandle *vector, int size, int index)
{
  SharedObject *obj;

  if(index < 0)
	index += size;
  if(index < 0 || index >= size) {
	PyErr_SetString(PyExc_IndexError, "index out of range");
	return NULL;
  }
  obj = (SharedObject *) SharedMemHandle_AsVoidPtr(vector[index]);
  assert(obj != NULL);
  return MakeProxy(obj);
}

static int
vector_ass_item(SharedMemHandle *vector, int size, int index, PyObject *value)
{
  SharedObject *olditem, *newitem;

  if(index < 0)
      index += size;
  if(index < 0 || index >= size) {
      PyErr_SetString((PyObject *) &PyExc_IndexError, "index out of range");
      return -1;
  }
  newitem = ShareObject(value);
  if(newitem == NULL)
	return -1;
  SharedObject_IncRef(newitem);
  olditem = (SharedObject*) SharedMemHandle_AsVoidPtr(vector[index]);
  SharedObject_DecRef(olditem);
  vector[index] = SharedMemHandle_FromVoidPtr(newitem);
  return 0;
}

/*********************************/
/* SharedListBase IMPLEMENTATION */
/*********************************/

/* Resizes the vector of a list, if necessary, to accomodate
   the new size. Accepts a pointer to the list's vector, which
   can be NULL if unknown. Returns a pointer to the list's vector,
   which may be reallocated.
   Returns NULL if resized to 0 or if out of memory.

   This over-allocates by a factor of 50% to amortize reallocation
   costs over time when growing the list. */
static SharedMemHandle *
list_resize(SharedListBaseObject *self, int newsize, SharedMemHandle *vector)
{
  size_t bytes;
  int newcapacity;
  SharedMemHandle *newvector;
  PyObject *self_ = (PyObject *) self;

  if(vector == NULL)
	vector = (SharedMemHandle *) SharedMemHandle_AsVoidPtr(self->vectorh);

  /* XXX: Never downsize for now */
  if(newsize > 0 && newsize <= self->capacity) {
	self->ob_size = newsize;
	return vector;
  }

  if(newsize <= 0) {
	/* Free the vector */
	if(vector != NULL)
	  SharedFree(self_, vector);
	self->capacity = 0;
	self->ob_size = 0;
	self->vectorh = SharedMemHandle_NULL;
	return NULL;
  }

  /* XXX: Round up this in some way */
  newcapacity = (newsize*3)/2;

  /* Allocate more memory for the vector */
  bytes = newcapacity * sizeof(SharedMemHandle);
  newvector = (SharedMemHandle *) SharedRealloc(self_, vector, &bytes);
  if(newvector == NULL)
	return NULL;

  /* SharedRealloc() may actually have allocated more bytes than requested */
  self->capacity = bytes / sizeof(SharedMemHandle);
  self->ob_size = newsize;
  self->vectorh = SharedMemHandle_FromVoidPtr(newvector);
  return newvector;
}

/* Creates an empty shared list */
static PyObject *
list_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  SharedListBaseObject *self;

  if(type == &SharedListBase_Type) {
	PyErr_Format(PyExc_TypeError, "cannot create '%.100s' instances",
			     type->tp_name);
	return NULL;
  }
  self = (SharedListBaseObject *) type->tp_alloc(type, 0);
  if(self != NULL) {
	/* Set the list to be empty (a consistent state) */
	assert(self->ob_size == 0);
	assert(self->capacity == 0);
	self->vectorh = SharedMemHandle_NULL;
  }
  return (PyObject *) self;
}

/* Initializes a shared list from a sequence */
static int 
list_tp_init(PyObject *self_, PyObject *args, PyObject *kwds)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  PyObject *seq;
  int size;
  SharedMemHandle *vector;

  /* Parse arguments */
  if(arg_sequence(args, "SharedListBase.__init__", &seq, &size))
	return -1;

  /* Resize the list */
  vector = list_resize(self, size, NULL);
  if(vector == NULL && size > 0)
	return -1;
  /* Initialize the list's vector */
  if(vector_init(vector, seq, size)) {
	list_resize(self, 0, vector);
	return -1;
  }
  return 0;
}

static void
list_tp_dealloc(PyObject *self_)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  SharedMemHandle *vector;

  vector = (SharedMemHandle *) SharedMemHandle_AsVoidPtr(self->vectorh);
  if(vector != NULL) {
	vector_deinit(vector, self->ob_size);
	SharedFree(self_, vector);
  }
  self->ob_type->tp_free(self_);
}

static long
list_tp_nohash(PyObject *self)
{
  PyErr_Format(PyExc_TypeError, "%.100s objects are unhashable",
			   self->ob_type->tp_name);
  return -1;
}

static PyObject *
list_tp_repr(PyObject *self_)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  SharedMemHandle vectorh = SharedMemHandle_NULL;
  SharedMemHandle *vector = NULL;
  PyObject *s, *temp;
  PyObject *pieces = NULL, *result = NULL;
  int i;

  i = Py_ReprEnter(self_);
  if (i != 0) {
	/* Recursive data structure */
	return i > 0 ? PyString_FromString("[...]") : NULL;
  }

  if (self->ob_size == 0) {
	/* Empty list */
	result = PyString_FromString("[]");
	goto Done;
  }

  pieces = PyList_New(0);
  if (pieces == NULL)
	goto Done;

  /* Do repr() on each element.  Note that this may mutate the list,
	 so we must refetch the list size on each iteration. */
  for (i = 0; i < self->ob_size; i++) {
	int status;
	SharedObject *item;

	/* Check if the vector handle has changed */
	if(!SharedMemHandle_EQUAL(vectorh, self->vectorh)) {
	  vectorh = self->vectorh;
	  vector = (SharedMemHandle *) SharedMemHandle_AsVoidPtr(vectorh);
	  assert(vector != NULL);
	}

	/* pieces.append(repr(self[i])) */
	item = (SharedObject *) SharedMemHandle_AsVoidPtr(vector[i]);
	assert(item != NULL);
	s = SharedObject_Repr(item);
	if (s == NULL)
	  goto Done;
	status = PyList_Append(pieces, s);
	Py_DECREF(s);  /* append created a new ref */
	if (status < 0)
	  goto Done;
  }

  /* Add "[]" decorations to the first and last items. */
  assert(PyList_GET_SIZE(pieces) > 0);
  s = PyString_FromString("[");
  if (s == NULL)
	goto Done;
  temp = PyList_GET_ITEM(pieces, 0);
  PyString_ConcatAndDel(&s, temp);
  PyList_SET_ITEM(pieces, 0, s);
  if (s == NULL)
	goto Done;

  s = PyString_FromString("]");
  if (s == NULL)
	goto Done;
  temp = PyList_GET_ITEM(pieces, PyList_GET_SIZE(pieces) - 1);
  PyString_ConcatAndDel(&temp, s);
  PyList_SET_ITEM(pieces, PyList_GET_SIZE(pieces) - 1, temp);
  if (temp == NULL)
	goto Done;

  /* Paste them all together with ", " between. */
  s = PyString_FromString(", ");
  if (s == NULL)
	goto Done;
  result = _PyString_Join(s, pieces);
  Py_DECREF(s);	

 Done:
  Py_XDECREF(pieces);
  Py_ReprLeave(self_);
  return result;  
}

static PyObject *
list_sq_item(PyObject *self_, int index)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  SharedMemHandle *vector;

  vector = (SharedMemHandle *) SharedMemHandle_AsVoidPtr(self->vectorh);
  assert(vector != NULL);
  return vector_item(vector, self->ob_size, index);
}

static int
list_sq_ass_item(PyObject *self_, int index, PyObject *value)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  SharedMemHandle *vector;

  vector = (SharedMemHandle *) SharedMemHandle_AsVoidPtr(self->vectorh);
  assert(vector != NULL);
  return vector_ass_item(vector, self->ob_size, index, value);
}

static int
list_sq_ass_slice(PyObject *self_, int ilow, int ihigh, PyObject *v)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  return -1;
}

static PyObject *
list_append(PyObject *self_, PyObject *value)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  SharedMemHandle *vector;
  int last = self->ob_size;

  vector = list_resize(self, last+1, NULL);
  if(vector == NULL)
	return NULL;
  if(vector_ass_item(vector, last+1, last, value)) {
	list_resize(self, last, vector);
	return NULL;
  }
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
list_pop(PyObject *self_, PyObject *args)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  int index = -1;

  if(!PyArg_ParseTuple(args, "|i:pop", &index))
	return NULL;
  return NULL;
}

static PyObject *
list_insert(PyObject *self_, PyObject *args)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  int index;
  PyObject *item;

  if(!PyArg_ParseTuple(args, "iO", &index, &item))
	return NULL;
  return NULL;
}

static PyObject *
list_remove(PyObject *self_, PyObject *value)
{
  SharedListBaseObject *self = (SharedListBaseObject *) self_;
  return NULL;
}

static char list_append_doc[] =
"L.append(object) -- append object to end";
static char list_pop_doc[] =
"L.pop([index]) -> item -- remove and return item at index (default last)";
static char list_insert_doc[] =
"L.insert(index, object) -- insert object before index";
static char list_remove_doc[] =
"L.remove(value) -- remove first occurrence of value";

static PyMethodDef list_tp_methods[] = {
  {"append", list_append, METH_O, list_append_doc},
  {"pop", list_pop, METH_VARARGS, list_pop_doc},
  {"insert", list_insert, METH_VARARGS, list_insert_doc},
  {"remove", list_remove, METH_O, list_remove_doc},
  {NULL, NULL} /* sentinel */
};

static PySequenceMethods list_tp_as_sequence = {
  common_sq_length,  /* sq_length */
  0,                 /* sq_concat */
  0,                 /* sq_repeat */
  list_sq_item,      /* sq_item */
  0,                 /* sq_slice */
  list_sq_ass_item,  /* sq_ass_item */
  list_sq_ass_slice, /* sq_ass_slice */
  0,                 /* sq_contains */
  0,                 /* sq_inplace_concat */
  0,                 /* sq_inplace_repeat */
};

static char list_tp_doc[] =
"Abstract base class for shared lists";

PyTypeObject SharedListBase_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.SharedListBase",
	sizeof(SharedListBaseObject),
	0,
	list_tp_dealloc,    /* tp_dealloc */
	0,      			/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	list_tp_repr,       /* tp_repr */
	0,					/* tp_as_number */
	&list_tp_as_sequence, /* tp_as_sequence */
	0,					/* tp_as_mapping */
	list_tp_nohash,     /* tp_hash */
	0,					/* tp_call */
	list_tp_repr,       /* tp_str */
	0,              	/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	list_tp_doc,        /* tp_doc */
 	0,           		/* tp_traverse */
 	0,      			/* tp_clear */
	0,                  /* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	list_tp_methods,    /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	list_tp_init,       /* tp_init */
	0,      			/* tp_alloc */
	list_tp_new,        /* tp_new */
	0,      			/* tp_free */
};

/**********************************/
/* SharedTupleBase IMPLEMENTATION */
/**********************************/

/* Creates a shared tuple */
static PyObject *
tuple_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  SharedTupleBaseObject *self;
  PyObject *seq;
  int size;

  if(type == &SharedTupleBase_Type) {
	PyErr_Format(PyExc_TypeError, "cannot create '%.100s' instances",
			     type->tp_name);
	return NULL;
  }
  if(arg_sequence(args, "SharedTupleBase.__new__", &seq, &size))
	return NULL;

  self = (SharedTupleBaseObject *) type->tp_alloc(type, size);
  if(self != NULL) {
      if(vector_init(self->vector, seq, size))
	  return NULL;
  }
  return (PyObject *) self;
}


static void
tuple_tp_dealloc(PyObject *self_)
{
  SharedTupleBaseObject *self = (SharedTupleBaseObject *) self_;

  vector_deinit(self->vector, self->ob_size);
  self->ob_type->tp_free(self_);
}


static PyObject *
tuple_sq_item(PyObject *self_, int index)
{
  SharedTupleBaseObject *self = (SharedTupleBaseObject *) self_;

  return vector_item(self->vector, self->ob_size, index);
}


/* Hash function for tuples, directly adapted from Objects/tupleobject.c */
static long
tuple_tp_hash(PyObject *self_)
{
  SharedTupleBaseObject *self = (SharedTupleBaseObject *) self_;
  long x, y;
  int len = self->ob_size;
  SharedMemHandle *p;
  SharedObject *item;  

  x = 0x345678L;
  for(p = self->vector; --len >= 0; p++) {
	item = (SharedObject *) SharedMemHandle_AsVoidPtr(*p);
	assert(item != NULL);
	y = SharedObject_Hash(item);
	if (y == -1)
	  return -1;
	x = (1000003*x) ^ y;
  }
  x ^= self->ob_size;
  if (x == -1)
	x = -2;
  return x;
}

static PyObject *
tuple_tp_richcompare(PyObject *self_, PyObject *other, int op)
{
  SharedTupleBaseObject *self = (SharedTupleBaseObject *) self_;
  int i, k, selflen, otherlen;
  int other_is_shared;
  SharedObject *a = NULL;
  PyObject *b = NULL;
  
  /* For 'other', we accept either a plain tuple or a shared tuple */
  other_is_shared = SharedTupleBase_Check(other);
  if (!other_is_shared && !PyTuple_Check(other)) {
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
  }
  
  selflen = self->ob_size;
  otherlen = ((PyVarObject *) other)->ob_size;
  
  /* Search for the first index where items are different.
   * Note that because tuples are immutable, it's safe to reuse
   * selflen and otherlen across the comparison calls.
   */
  for (i = 0; i < selflen && i < otherlen; i++) {
	/* a = self[i] */
	a = (SharedObject *) SharedMemHandle_AsVoidPtr(self->vector[i]);
	if (a == NULL)
	  return NULL;

	/* b = other[i] */
	if (other_is_shared) {
	  SharedTupleBaseObject *o = (SharedTupleBaseObject *) other;
	  SharedObject *shb = (SharedObject *)
		SharedMemHandle_AsVoidPtr(o->vector[i]);
	  if (shb == NULL)
		return NULL;
	  b = SharedObject_AS_PYOBJECT(shb);
	}
	else
	  b = PyTuple_GET_ITEM(other, i);

	/* Compare a and b */	
	k = SharedObject_RichCompareBool(a, b, Py_EQ);
	if (k < 0)
	  return NULL;
	if (!k)
	  break;
  }
  
  if (i >= selflen || i >= otherlen) {
	/* No more items to compare -- compare sizes */
	int cmp;
	PyObject *res;
	switch (op) {
	case Py_LT: cmp = selflen <  otherlen; break;
	case Py_LE: cmp = selflen <= otherlen; break;
	case Py_EQ: cmp = selflen == otherlen; break;
	case Py_NE: cmp = selflen != otherlen; break;
	case Py_GT: cmp = selflen >  otherlen; break;
	case Py_GE: cmp = selflen >= otherlen; break;
	default: return NULL; /* cannot happen */
	}
	if (cmp)
	  res = Py_True;
	else
	  res = Py_False;
	Py_INCREF(res);
	return res;
  }
  
  /* We have an item that differs -- shortcuts for EQ/NE */
  if (op == Py_EQ) {
	Py_INCREF(Py_False);
	return Py_False;
  }
  if (op == Py_NE) {
	Py_INCREF(Py_True);
	return Py_True;
  }
  
  /* Compare the final item again using the proper operator */
  return SharedObject_RichCompare(a, b, op);
}


static PySequenceMethods tuple_tp_as_sequence = {
	common_sq_length, /* sq_length */
	0,           /* sq_concat */
	0,           /* sq_repeat */
	tuple_sq_item, /* sq_item */
	0,           /* sq_slice */
	0,           /* sq_ass_item */
	0,           /* sq_ass_slice */
	0,           /* sq_contains */
	0,           /* sq_inplace_concat */
	0,           /* sq_inplace_repeat */
};

static char tuple_tp_doc[] =
"Abstract base class for shared tuples";

PyTypeObject SharedTupleBase_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.SharedTupleBase",
	sizeof(SharedTupleBaseObject) - sizeof(SharedMemHandle),
	sizeof(SharedMemHandle),
	tuple_tp_dealloc,   /* tp_dealloc */
	0,      			/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	0,                  /* tp_repr */
	0,					/* tp_as_number */
	&tuple_tp_as_sequence, /* tp_as_sequence */
	0,					/* tp_as_mapping */
	tuple_tp_hash,      /* tp_hash */
	0,					/* tp_call */
	0,                  /* tp_str */
	0,              	/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	tuple_tp_doc,       /* tp_doc */
 	0,           		/* tp_traverse */
 	0,      			/* tp_clear */
	tuple_tp_richcompare, /* tp_richcompare */
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
	0,                  /* tp_init */
	0,      			/* tp_alloc */
	tuple_tp_new,       /* tp_new */
	0,      			/* tp_free */
};
