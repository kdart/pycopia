/* Globals.h */

/* Global data structures shared between all processes. */

#ifndef GLOBALS_H_INCLUDED
#define GLOBALS_H_INCLUDED

#include "_core.h"
#include "Lock.h"
#include "Process.h"
#include "SharedRegion.h"
#include "Handle.h"
#include "SemSet.h"

/* Preferred size of the lock table - one lock per process
   should be enough to avoid contention */
#define LOCK_TABLE_SIZE 5 /*MAX_PROCESSES*/

/* Maximum number of shared memory regions (this limit may of course
   be lower in reality, depending on how _SharedRegion_New() is implemented */
#define MAX_REGIONS 500

typedef struct {
  /* The handle for the region this structure is allocated in */
  SharedRegionHandle my_handle;

  /* Table of process ids used to enumerate processes */
  struct {
	Spinlock spinlock;
	int pid[MAX_PROCESSES];
  } proctable;

  /* Table of region handles for all shared memory regions 
	 that have been created. */
  struct {
	Lock lock;
	int count; /* The current number of regions. */
	int freepos; /* Some position in the table thought to be free, to speed
					up searching for a free posititon. */
	SharedRegionHandle regh[MAX_REGIONS];
	size_t regsize[MAX_REGIONS];
  } regtable;

  struct {
	/* The semaphore set contains one semaphore per process, for letting
	   the process sleep when needed. There is one handle per process too,
	   indicating which address the process is waiting for. */
	SemSet semset;
	SharedMemHandle addr[MAX_PROCESSES];
  } sleeptable;
} Globals;

/* The globals struct is allocated in a shared memory region by the
   first process, prior to any forks. This means that all descendants will
   have this region attached at the same address, so the structure can
   be referenced by a plain pointer. */
extern Globals *globals;

/* Initializes the globals pointer */
int Globals_Init(void);

/* Cleans up the global variables */
void Globals_Cleanup(void);

/* Calls _SharedRegion_New() to create a new shared memory region of
   the given size, and stores the handle in the region table, so that
   the region can be destroyed (by Globals_Cleanup()) when the last process
   exits. Returns a SharedMemHandle for the start of the region. */
SharedMemHandle SharedRegion_New(size_t *size);

/* Calls _SharedRegion_Destroy() to destroy the given shared memory region,
   and also removes it from the region table. */
void SharedRegion_Destroy(SharedMemHandle h);

#endif
