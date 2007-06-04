/* SharedListAndTuple.h */

#ifndef SHAREDLISTANDTUPLE_H_INCLUDED
#define SHAREDLISTANDTUPLE_H_INCLUDED

#include "_core.h"

extern PyTypeObject SharedListBase_Type;
extern PyTypeObject SharedTupleBase_Type;

#define SharedListBase_Check(ob) PyObject_TypeCheck(ob, &SharedListBase_Type)
#define SharedTupleBase_Check(ob) PyObject_TypeCheck(ob, &SharedTupleBase_Type)

#endif
