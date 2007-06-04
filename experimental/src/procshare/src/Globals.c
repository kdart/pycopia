/* Globals.c */

#include "Globals.h"
#include "SharedRegion.h"
#include "Handle.h"

Globals *globals = NULL;

int 
Globals_Init(void)
{
  SharedRegionHandle h;
  size_t size = sizeof(Globals);
  int i;

  LOG();
  assert(globals == NULL);
  /* Allocate the Globals struct in shared memory */
  h = _SharedRegion_New(&size);
  if (SharedRegionHandle_IS_NULL(h))
	return -1;
  globals = (Globals *) _SharedRegion_Attach(h);
  if (globals == NULL) {
	_SharedRegion_Destroy(h);
	return -1;
  }
  globals->my_handle = h;

  /* Initialize the process table. */
  Spinlock_Init(&globals->proctable.spinlock);
  for (i = 0; i < MAX_PROCESSES; i++)
	globals->proctable.pid[i] = -1;

  /* Initialize the region table */
  Lock_Init(&globals->regtable.lock);
  for (i = 0; i < MAX_REGIONS; i++)
	globals->regtable.regh[i] = SharedRegionHandle_NULL;
  globals->regtable.count = 0;
  globals->regtable.freepos = 0;

  /* Initialize the sleep table */
  for (i = 0; i < MAX_PROCESSES; i++)
	globals->sleeptable.addr[i] = SharedMemHandle_NULL;
  if (SemSet_Init(&globals->sleeptable.semset, MAX_PROCESSES)) {
	Globals_Cleanup();
	return -1;
  }

  return 0;
}


void 
Globals_Cleanup(void)
{
  int i;

  LOG();
  Spinlock_Destroy(&globals->proctable.spinlock);
  Lock_Destroy(&globals->regtable.lock);
  SemSet_Destroy(&globals->sleeptable.semset);
  for (i = 0; i < MAX_REGIONS; i++)
	if (!SharedRegionHandle_IS_NULL(globals->regtable.regh[i]))
	  _SharedRegion_Destroy(globals->regtable.regh[i]);
  _SharedRegion_Destroy(globals->my_handle);
  globals = NULL;
}


SharedMemHandle
SharedRegion_New(size_t *size)
{
  SharedRegionHandle regh;
  SharedMemHandle result = SharedMemHandle_NULL;
  int free;

  assert(globals != NULL);
  Lock_Acquire(&globals->regtable.lock);
  if (globals->regtable.count < MAX_REGIONS) {
	/* Find a free index in the table */
	for (free = globals->regtable.freepos;
		 !SharedRegionHandle_IS_NULL(globals->regtable.regh[free]);
		 free = (free+1) % MAX_REGIONS)
	  ;
	regh = _SharedRegion_New(size);
	if (!SharedRegionHandle_IS_NULL(regh)) {
	  globals->regtable.count++;
	  globals->regtable.regh[free] = regh;
	  globals->regtable.regsize[free] = *size;
	  globals->regtable.freepos = (free+1) % MAX_REGIONS;
	  result.regndx = free;
	  result.offset = 0;
	}
  }
  Lock_Release(&globals->regtable.lock);

  return result;
}


void
SharedRegion_Destroy(SharedMemHandle h)
{
  SharedRegionHandle regh;
  void *reg_addr = SharedMemHandle_AsVoidPtr(h);

  assert(globals != NULL);
  Lock_Acquire(&globals->regtable.lock);
  regh = globals->regtable.regh[h.regndx];
  globals->regtable.regh[h.regndx] = SharedRegionHandle_NULL;
  Lock_Release(&globals->regtable.lock);

  _SharedRegion_Detach(reg_addr);
  _SharedRegion_Destroy(regh);
}
