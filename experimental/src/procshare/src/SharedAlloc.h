/* SharedAlloc.h */

#ifndef SHAREDALLOC_H_INCLUDED
#define SHAREDALLOC_H_INCLUDED

#include "_core.h"
#include "SharedObject.h"

/* C interface for allocation of shared memory by objects.
  
   SharedAlloc(), SharedFree() and SharedRealloc() are used by shared 
   objects to allocate their auxilliary data structures.
  
   SharedObject_Alloc() and SharedObject_Free() are exclusively for use
   in the tp_alloc and tp_free slots of shared objects' types.
*/

/* Allocates shared memory on the data heap of the given object's
   meta-type. May allocate more bytes than requested - on return,
   *size is the number of bytes actually allocated. On error, this
   sets an exception and returns NULL. */
void *SharedAlloc(PyObject *self, size_t *size);

/* Frees shared memory on the data heap of the given object's meta-type.
   If it fails, it fails badly (dumps core). */
void SharedFree(PyObject *self, void *ptr);

/* Rellocates shared memory on the data heap of the given object's
   meta-type. May allocate more bytes than requested - on return,
   *size is the number of bytes actually allocated. On error, this
   sets an exception and returns NULL. */
void *SharedRealloc(PyObject *self, void *ptr, size_t *size);

/* Allocator function for the tp_alloc slot of shared objects' types. */
PyObject *SharedObject_Alloc(PyTypeObject *type, int nitems);

/* Deallocator function for the tp_free slot of shared objects' types. */
void SharedObject_Free(PyObject *obj);

#endif
