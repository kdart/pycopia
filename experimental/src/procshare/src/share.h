/* share.h */

#ifndef SHARE_H_INCLUDED
#define SHARE_H_INCLUDED

#include "_core.h"
#include "SharedObject.h"

/* Instantiates a shared object from the given object. */
SharedObject *ShareObject(PyObject *obj);

/* Encapsulates a shared object in a proxy object. */
PyObject *MakeProxy(SharedObject *obj);

#endif
