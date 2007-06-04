/* Process.c */

#include "Process.h"
#include "Globals.h"
#include "SharedObject.h"
#include "Proxy.h"

int my_pid = -1;
int my_pindex = -1;


/* Get a process's index in the process table. Allocates
   a new index for it if necessary. Returns -1 on error. */
static int
get_pindex(int pid)
{
  int pos, free;

  assert(globals != NULL);
  Spinlock_Acquire(&globals->proctable.spinlock);

  for (pos = 0, free = -1; pos < MAX_PROCESSES; pos++)
    if (globals->proctable.pid[pos] == pid)
      break;
    else if (globals->proctable.pid[pos] == -1)
      free = pos;
  if (pos == MAX_PROCESSES) {
    pos = free;
    if (pos > -1)
      globals->proctable.pid[pos] = pid;
  }

  Spinlock_Release(&globals->proctable.spinlock);
  return pos;
}


/* Frees a process's index in the process table.
   Returns 1 if this is the last process. */
static int
free_pindex(int pid)
{
  int i, pos, used;

  assert(globals != NULL);
  Spinlock_Acquire(&globals->proctable.spinlock);

  pos = -1; used = 0;
  for (i = 0; i < MAX_PROCESSES; i++) {
    if (globals->proctable.pid[i] == pid)
      pos = i;
    else if (globals->proctable.pid[i] != -1)
      used++;
  }
  if (pos != -1)
    globals->proctable.pid[pos] = -1;

  Spinlock_Release(&globals->proctable.spinlock);
  return (used == 0);
}


static int
update_proxy_map(void)
{
  /* New refs */
  PyObject *values = NULL;
  PyObject *fastvalues = NULL;

  /* Borrowed refs */
  PyObject *pm = NULL;
  PyObject *item = NULL;

  /* Return value, defaults to OK */
  int rv = 0;
  int i, length;
  SharedObject *shobj = 0;

  pm = GetProxyMap();
  if(!pm)
    goto error;
  values = PyMapping_Values(pm);
  if(!values)
    goto error;
  fastvalues = PySequence_Fast(values, 
			       "ProxyMap.values() should be a sequence");
  if(!fastvalues)
    goto error;
  length = PySequence_Fast_GET_SIZE(fastvalues);
  for(i = 0; i < length; i++) {
    item = PySequence_Fast_GET_ITEM(fastvalues, i);
    if(!item)
      goto error;
    assert(Proxy_Check(item));
    shobj = ((ProxyObject*) item)->referent;
    SharedObject_SetProxyBit(shobj);
  }
  LOGF("Set the proxy bit of %d shared objects", length);
  goto done;

 error:
  rv = -1;
 done:
  Py_XDECREF(fastvalues);
  Py_XDECREF(values);
  return rv;
}


int
Process_Init()
{
  static int first_call = 1;
  int was_first = 0;

  if (first_call) {
    first_call = 0;
    was_first = 1;
    /* This is the first process to be initialized. We should initialize
       the global data structures. */
    if (Globals_Init())
      return -1;
  }
  my_pid = getpid();
  my_pindex = get_pindex(my_pid);
  if (my_pindex == -1)
    return -1;
  if (Py_AtExit(Process_Cleanup))
    return -1;
  if (!was_first)
    if(update_proxy_map())
      return -1;
  LOGF("pid=%d pindex=%d", my_pid, my_pindex);
  return 0;
}


void 
Process_Cleanup()
{
  LOGF("pid=%d pindex=%d", my_pid, my_pindex);
  if (free_pindex(my_pid)) {
    /* A return value of 1 means that this is the last process. */
    Globals_Cleanup();
  }
}


void
Process_CleanupChild(int pid)
{
  free_pindex(pid);
}
