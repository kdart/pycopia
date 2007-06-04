/* SharedObject.h */

#ifndef SHAREDOBJECT_H_INCLUDED
#define SHAREDOBJECT_H_INCLUDED

#include "_core.h"
#include "Process.h"
#include "Handle.h"
#include "Spinlock.h"
#include "Lock.h"

/* This is the C representation of a shared object, which is basically a
   normal Python object with additional data prepended to it. When shared
   objects are allocated, there is made room for the additional data
   that precedes the normal object structure. */
typedef struct {
  /* Lock for synchronizing access to the object. Note that the object's
	 synchronization manager decides if and how to use this lock. */
  Lock lock;
  /* Handle to the object's shared dictionary */
  SharedMemHandle dicth;
  /* Spinlock for protecting the proxybmp and srefcnt fields. */
  Spinlock reflock;
  /* Bitmap showing which processes have a proxy object for the object. */
  ProcessBitmap proxybmp;
  /* Shared reference count; this is the number of references to this
	 object from other *shared* objects. References from proxy objects are
	 not counted here, but reflected in the proxy bitmap above. */
  unsigned int srefcnt : sizeof(int)*8 - 2;
  /* Flags */
  unsigned int is_corrupt : 1; /* True if the object may be corrupted */
  unsigned int no_synch : 1; /* True if no synch. is required on this object,
				i.e. type(self).__synch__ is None */
  /* Start of normal PyObject structure */
  PyObject pyobj;
} __attribute__((packed)) SharedObject;

/* "Casting" macros (they do some pointer arithmethics too) */

#define SharedObject_FROM_PYOBJECT(ob) \
  ((SharedObject *) (((void *) (ob)) - offsetof(SharedObject, pyobj)))

#define SharedObject_AS_PYOBJECT(shob) \
  (&(((SharedObject *) (shob))->pyobj))

#define SharedObject_AS_PYVAROBJECT(shob) \
  ((PyVarObject *) &(((SharedObject *) (shob))->pyobj))

/* Macro to calculate the number of bytes needed for a shared object */
#define SharedObject_VAR_SIZE(type, nitems) \
  (_PyObject_VAR_SIZE(type, nitems) + offsetof(SharedObject, pyobj))

/* Initializes a newly created shared object, including the PyObject part
   of it. The object should be zeroed out already. */
void SharedObject_Init(SharedObject *obj, PyTypeObject *type, int nitems);

/* Increases the shared reference count of a shared object, indicating
   a new reference from another shared object to it. */
void SharedObject_IncRef(SharedObject *obj);

/* Decreases the shared reference count of a shared object, indicating
   that a reference to it from another shared object was destroyed.
   If the shared reference count reaches 0, and the process bitmap
   indicates that there are no proxy objects for the object, it will
   be reclaimed. */
void SharedObject_DecRef(SharedObject *obj);

/* Sets the bit in the shared object that indicates that this process has
   at least 1 proxy object referring to the shared object. */
void SharedObject_SetProxyBit(SharedObject *obj);

/* Clears a bit in the shared object, indicating that this process has no
   more proxy objects referring to the shared object. If all the bits
   in the process bitmap are cleared, and the shared reference count is 0,
   the object will be reclaimed. */
void SharedObject_ClearProxyBit(SharedObject *obj);

/* Calls the enter() method on the __synch__ attribute of a shared object's
   meta-type, acquiring access to the object. */
PyObject *SharedObject_Enter(SharedObject *obj, PyObject *opname);

/* Like SharedObject_Enter(), but opname is a C string, and *opname_cache,
   if non-NULL, will be used to cache the string object from call to call. */
PyObject *SharedObject_EnterString(SharedObject *obj, char *opname, 
								   PyObject **opname_cache);

/* Calls the leave() method on the __synch__ attribute of a shared object's
   meta-type, releasing access to the object. Ignores any exceptions that
   occur. If an exception is set prior to this call, it will be set on return,
   too. The 'state' argument should be the return value from
   SharedObject_Enter(). This function always steals a reference to 'state'. */
void SharedObject_Leave(SharedObject *obj, PyObject *state);

/* Attribute getter function for shared objects that support attributes.
   This is suitable for the tp_getattro slot of shareable types. */
PyObject *SharedObject_GetAttr(PyObject *obj, PyObject *name);

/* Attribute setter function for shared objects that support attributes.
   This is suitable for the tp_setattro slot of shareable types. */
int SharedObject_SetAttr(PyObject *obj, PyObject *name, PyObject *value);

/* The following functions are utility functions that do the same as their
   PyObject_Whatever counterparts, but also call SharedObject_Enter() and
   SharedObject_Leave() for you. */

/* Like PyObject_Repr() */
PyObject *SharedObject_Repr(SharedObject *obj);

/* Like PyObject_Str() */
PyObject *SharedObject_Str(SharedObject *obj);

/* Like PyObject_Hash() */
long SharedObject_Hash(SharedObject *obj);

/* Like PyObject_Print() */
int SharedObject_Print(SharedObject *obj, FILE *fp, int flags);

/* Like PyObject_Compare() */
int SharedObject_Compare(SharedObject *a, PyObject *b);

/* Like PyObject_RichCompare() */
PyObject *SharedObject_RichCompare(SharedObject *a, PyObject *b, int op);

/* Like PyObject_RichCompareBool() */
int SharedObject_RichCompareBool(SharedObject *a, PyObject *b, int op);

#endif
