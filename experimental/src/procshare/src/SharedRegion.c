/* SharedRegion.c */

#include "SharedRegion.h"
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>

SharedRegionHandle
_SharedRegion_New(size_t *size)
{
  int id;
  struct shmid_ds ds;

  /* Create the region */
  id = shmget(IPC_PRIVATE, (int) *size, SHM_R | SHM_W);
  if (id == -1)
	return SharedRegionHandle_NULL;

  /* Query it for its actual size */
  if (shmctl(id, IPC_STAT, &ds) == -1) {
	/* Error - remove the region again */
	shmctl(id, IPC_RMID, NULL);
	PyErr_SetString(PyExc_RuntimeError, 
					"creation of shared memory region failed");
	return SharedRegionHandle_NULL;
  }
  *size = (size_t) ds.shm_segsz;
  
  return id;
}

void 
_SharedRegion_Destroy(SharedRegionHandle h)
{
  shmctl(h, IPC_RMID, NULL);
}

void *
_SharedRegion_Attach(SharedRegionHandle handle)
{
  void *addr = shmat(handle, 0, 0);
  if(addr == (void *) -1) {
    /* XXX: Can this really happen? */
	PyErr_SetString(PyExc_RuntimeError, 
					"attachment of shared memory region failed");
    return NULL;
  }
  return addr;
}

int
_SharedRegion_Detach(void *addr)
{
  return shmdt(addr);
}


