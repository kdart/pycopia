
/* Unsigned Integer object interface */

/*
PyIntObject represents a (long) integer.  This is an immutable object;
an integer cannot change its value after creation.

There are functions to create new integer objects, to test an object
for integer-ness, and to get the integer value.  The latter functions
returns -1 and sets errno to EBADF if the object is not an PyIntObject.
None of the functions should be applied to nil objects.

The type PyIntObject is (unfortunately) exposed here so we can declare
_Py_TrueStruct and _Py_ZeroStruct in boolobject.h; don't use this.
*/

#ifndef Py_INTOBJECT_H
#define Py_INTOBJECT_H
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    PyObject_HEAD
    unsigned long ob_ival;
} PyUnsignedIntObject;

PyAPI_DATA(PyTypeObject) PyUnsignedInt_Type;

#define PyUnsignedInt_Check(op) PyObject_TypeCheck(op, &PyUnsignedInt_Type)
#define PyUnsignedInt_CheckExact(op) ((op)->ob_type == &PyUnsignedInt_Type)

PyAPI_FUNC(PyObject *) PyUnsignedInt_FromString(char*, char**, int);
#ifdef Py_USING_UNICODE
PyAPI_FUNC(PyObject *) PyUnsignedInt_FromUnicode(Py_UNICODE*, int, int);
#endif
PyAPI_FUNC(PyObject *) PyUnsignedInt_FromLong(long);
PyAPI_FUNC(long) PyUnsignedInt_AsLong(PyObject *);
PyAPI_FUNC(unsigned long) PyUnsignedInt_AsUnsignedLongMask(PyObject *);
#ifdef HAVE_LONG_LONG
PyAPI_FUNC(unsigned PY_LONG_LONG) PyUnsignedInt_AsUnsignedLongLongMask(PyObject *);
#endif

PyAPI_FUNC(long) PyUnsignedInt_GetMax(void);

/* Macro, trading safety for speed */
#define PyUnsignedInt_AS_LONG(op) (((PyUnsignedIntObject *)(op))->ob_ival)

/* These aren't really part of the Int object, but they're handy; the protos
 * are necessary for systems that need the magic of PyAPI_FUNC and that want
 * to have stropmodule as a dynamically loaded module instead of building it
 * into the main Python shared library/DLL.  Guido thinks I'm weird for
 * building it this way.  :-)  [cjh]
 */
PyAPI_FUNC(unsigned long) PyOS_strtoul(char *, char **, int);

PyAPI_FUNC(PyObject *) PyLong_FromUnsignedLong(unsigned long);

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTOBJECT_H */
