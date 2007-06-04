/* SharedAlloc.c */

#include "SharedAlloc.h"
#include "SharedHeap.h"
#include "SharedObject.h"
#include "Address.h"

/* (Re)allocates shared memory using the (re)alloc() method of
   one of the heaps of the given type. */
static void *
shared_alloc(PyTypeObject *type, char *heap_name,
			 void *ptr, size_t *size_arg)
{
  /* New references */
  PyObject *tuple = NULL, *heap = NULL;
  /* Borrowed references */
  PyObject *addr;
  /* Return value */
  void *rv = NULL;
  /* Size as a long */
  long size = (long) *size_arg;

  /* Get the heap object from the meta-type */
  heap = PyObject_GetAttrString((PyObject *) type, heap_name);
  if(heap == NULL)
	goto Error;

  if(ptr == NULL) {
	/* Call the alloc() method of the heap */
	tuple = PyObject_CallMethod(heap, S_ALLOC, "l", size);
  }
  else {
	/* Call the realloc() method of the heap */
	tuple = PyObject_CallMethod(heap, S_REALLOC, "(Nl)",
								Address_FromVoidPtr(ptr), size);
  }
  if(tuple == NULL)
	goto Error;
  /* The call should return an (address, size) tuple */
  if(!PyArg_Parse(tuple, 
				  "(O!l);(re)alloc() should return an (address, size) tuple",
				  &Address_Type, &addr, &size))
	goto Error;
  /* Extract the allocated address from the object */
  rv = Address_AsVoidPtr(addr);
  if(rv == NULL)
	PyErr_NoMemory();
  /* Return the actual number of bytes allocated */
  *size_arg = (size_t) size;

 Error:
  Py_XDECREF(heap);
  Py_XDECREF(tuple);
  return rv;
}

static void
shared_free(PyTypeObject *type, char *heap_name, void *ptr)
{
  PyObject *heap;

  heap = PyObject_GetAttrString((PyObject *) type, heap_name);
  if(heap == NULL) {
	/* This sucks, but it really shouldn't happen.
	   XXX Swallow it with PyErr_Clear() ?? */
  }
  else {
	PyObject *result;
	result = PyObject_CallMethod(heap, S_FREE, "N", Address_FromVoidPtr(ptr));
	/* We have to DECREF the return value, even if we don't care about it. */
	Py_XDECREF(result);
  }
}

void *
SharedAlloc(PyObject *self, size_t *size)
{
  return shared_alloc(self->ob_type, S_DHEAP, NULL, size);
}

void 
SharedFree(PyObject *self, void *ptr)
{
  shared_free(self->ob_type, S_DHEAP, ptr);
}

void *
SharedRealloc(PyObject *self, void *ptr, size_t *size)
{
  return shared_alloc(self->ob_type, S_DHEAP, ptr, size);
}


PyObject *
SharedObject_Alloc(PyTypeObject *type, int nitems)
{
  /* The number of bytes required for the new object */
  const size_t req_size = SharedObject_VAR_SIZE(type, nitems);
  /* The number of bytes actually allocated */
  size_t size = req_size;
  /* The new object */
  SharedObject *new_obj;

  /* Allocate memory for the new object */
  new_obj = (SharedObject *) shared_alloc(type, S_IHEAP, NULL, &size);
  if (new_obj == NULL)
	return NULL;

  /* Zero out everything */
  memset(new_obj, '\0', req_size);

  /* Initialize the object */
  SharedObject_Init(new_obj, type, nitems);

  /* Return the new object as a PyObject */
  return SharedObject_AS_PYOBJECT(new_obj);
}


void
SharedObject_Free(PyObject *obj)
{
  shared_free(obj->ob_type, S_IHEAP, SharedObject_FROM_PYOBJECT(obj));
}



