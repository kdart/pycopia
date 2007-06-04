/* Lock.h */

#ifndef LOCK_H_INCLUDED
#define LOCK_H_INCLUDED

#include "_core.h"
#include "Process.h"
#include "Spinlock.h"

typedef struct {
  Spinlock spinlock;
  int owner_pid;
  int nest_count;
  ProcessBitmap waiting;
} Lock;

/* Initializes the lock. Always succeeds. */
void Lock_Init(Lock *lock);

/* Destroys the lock. Always succeeds. */
void Lock_Destroy(Lock *lock);

/* Acquires the lock, blocking if necessary. 
   Returns -1 on failure, 0 on success. */
int Lock_Acquire(Lock *lock);

/* Tries to acquire the lock without blocking.
   Returns -1 on failure, 0 on success. */
int Lock_TryAcquire(Lock *lock);

/* Releases the lock. Returns -1 on failure, 0 on success. */
int Lock_Release(Lock *lock);

/* Returns 1 if the lock is owned by the given process. */
int Lock_OwnedBy(int pid);

#endif
