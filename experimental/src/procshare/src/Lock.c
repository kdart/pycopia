/* Lock.c */

#include "Lock.h"
#include "Globals.h"

void
Lock_Init(Lock *lock)
{
  Spinlock_Init(&lock->spinlock);
  lock->owner_pid = -1;
  lock->nest_count = 0;
  ProcessBitmap_CLEAR_ALL(lock->waiting);
}

void
Lock_Destroy(Lock *lock)
{
  Spinlock_Destroy(&lock->spinlock);
  lock->owner_pid = -1;
  lock->nest_count = 0;
  assert(ProcessBitmap_IS_ZERO(lock->waiting));
}

/* Selects which process to wake up when releasing a lock */
static int
select_wakeup(Lock *lock)
{
  static int j = -1;

  if (ProcessBitmap_IS_ZERO(lock->waiting))
    return -1;

  for(;;) {
    /* This loop must terminate, since at least one bit is set */
	j = (j+1) % MAX_PROCESSES;
	if (ProcessBitmap_IS_SET(lock->waiting, j))
	  return j;
  }
}

int
Lock_TryAcquire(Lock *lock)
{
  int result = -1;

  Spinlock_Acquire(&lock->spinlock);
  if (lock->owner_pid == -1 || lock->owner_pid == my_pid) {
	/* The lock is free, so grab it. */
	lock->owner_pid = my_pid;
	lock->nest_count++;
	result = 0;
  }
  Spinlock_Release(&lock->spinlock);
  return result;
}

int
Lock_Acquire(Lock *lock)
{
  for (;;) {
	Spinlock_Acquire(&lock->spinlock);
	if (lock->owner_pid == -1 || lock->owner_pid == my_pid) {
	  /* The lock is free, so grab it. */
	  lock->owner_pid = my_pid;
	  lock->nest_count++;
	  /* LOGF("%d [%d] acquired lock at %p to level %d",
	     my_pindex, my_pid, lock, lock->nest_count); */
	  Spinlock_Release(&lock->spinlock);
	  return 0;
	}
	else {
	  /* We must wait. Sleep on this process's semaphore in the
	     sleep table, and retry when woken up. */
	  globals->sleeptable.addr[my_pindex] = SharedMemHandle_FromVoidPtr(lock);
	  ProcessBitmap_SET(lock->waiting, my_pindex);
	  /* LOGF("%d [%d] waiting for lock at %p", 
	     my_pindex, my_pid, lock); */
	  Spinlock_Release(&lock->spinlock);
	  if (SemSet_Down(&globals->sleeptable.semset, my_pindex))
		return -1;
	}
  }
}

int
Lock_Release(Lock *lock)
{
    Spinlock_Acquire(&lock->spinlock);
    if (lock->owner_pid != my_pid) {
	Spinlock_Release(&lock->spinlock);
	PyErr_SetString(PyExc_RuntimeError, 
			"lock release attempted by non-owner");
	return -1;
    }
    if (--lock->nest_count == 0) {
	int wakeup = select_wakeup(lock);
	lock->owner_pid = -1;
	if (wakeup != -1) {
	    LOGF("%d woken by %d [%d]", wakeup, my_pindex, my_pid);
	    globals->sleeptable.addr[wakeup] = SharedMemHandle_NULL;
	    ProcessBitmap_CLEAR(lock->waiting, wakeup);
	    Spinlock_Release(&lock->spinlock);
	    return SemSet_Up(&globals->sleeptable.semset, wakeup);
	}
    }
    /* LOGF("%d [%d] released lock at %p to level %d",
       my_pindex, my_pid, lock, lock->nest_count); */
    Spinlock_Release(&lock->spinlock);
    return 0;
}
