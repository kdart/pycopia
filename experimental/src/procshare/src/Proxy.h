/* Proxy.h */

#ifndef PROXY_H_INCLUDED
#define PROXY_H_INCLUDED

#include "_core.h"
#include "SharedObject.h"

/* C representation of a proxy object */
typedef struct {
  PyObject_HEAD
  SharedObject *referent;
  PyObject *weakreflist;
} ProxyObject;

extern PyTypeObject Proxy_Type;

#define Proxy_Check(op) PyObject_TypeCheck(op, &Proxy_Type)

/* Returns a borrowed reference to a WeakValueDictionary mapping that maps
   the addresses of shared objects to weak references to their local proxy
   objects. The mapping contains all the proxy objects in existence
   (in this process). */
PyObject *GetProxyMap(void);

#endif
