/* _core.h */
/* Common header file for the _procshare_core module. */

#ifndef _CORE_H_INCLUDED
#define _CORE_H_INCLUDED

#include <Python.h>
#include <structmember.h>

#ifdef DEBUG
#define LOGF(fmt, args...) printf("*** %s:%d (%s) " fmt "\n", \
                                  __FILE__, __LINE__, __FUNCTION__, args)
#define LOGS(s) LOGF("%s", s)
#define LOG() LOGF("%s", "")
#else
#define LOGF(fmt, args...)
#define LOGS(s)
#define LOG()
#endif

/* String constants */
#define S_IHEAP "__instanceheap__"
#define S_DHEAP "__dataheap__"
#define S_SYNCH "__synch__"
#define S_ENTER "enter"
#define S_LEAVE "leave"
#define S_ALLOC "alloc"
#define S_REALLOC "realloc"
#define S_FREE "free"

extern PyObject *ErrorObject;
extern PyObject *TypeMap;

/* These are updated by Process_Init() each time a new process is forked */
extern int my_pid;
extern int my_pindex;

#endif
