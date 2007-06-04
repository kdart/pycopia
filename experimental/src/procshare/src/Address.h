/* Address.h */

#ifndef ADDRESS_H_INCLUDED
#define ADDRESS_H_INCLUDED

#include "_core.h"

#define Address_Check(op) PyObject_TypeCheck(op, &Address_Type)

extern PyTypeObject Address_Type;

void *
Address_AsVoidPtr(PyObject *obj);

PyObject *
Address_FromVoidPtr(void *ptr);

#endif
