/* SemSet.c */

#include "SemSet.h"
#include <sys/sem.h>

#define SETS_NEEDED(size) \
  (((size) + SYSV_SETS_PER_SEMSET - 1) / (SYSV_SETS_PER_SEMSET))
#define SET_NO(x) ((x) / SYSV_SETS_PER_SEMSET)
#define SEM_NO(x) ((x) % SYSV_SETS_PER_SEMSET)

int
SemSet_Init(SemSet *semset, int size)
{
  int sets = SETS_NEEDED(size);
  int i;

  if (sets > SYSV_SETS_PER_SEMSET) {
      PyErr_SetString(PyExc_RuntimeError,
		      "semaphore set creation failed");
      return -1;
  }
  for (i = 0; i < sets; i++) {
	int id = semget(IPC_PRIVATE, MAX_SYSV_SET_SIZE, IPC_CREAT 
			| S_IREAD | S_IWRITE); //SEM_R | SEM_A);
	if (id == -1) {
	  /* Destroy the sets that have been created so far */
	  int j;
	  for (j = 0; j < i; j++)
		semctl(semset->setid[j], 0, IPC_RMID);
	  semset->size = 0;
	  PyErr_SetString(PyExc_RuntimeError,
			  "semaphore set creation failed");
	  return -1;
	}
	semset->setid[i] = id;
  }
  semset->size = size;
  return 0;
}

void
SemSet_Destroy(SemSet *semset)
{
  int sets = SETS_NEEDED(semset->size);
  int i;

  for (i = 0; i < sets; i++)
	semctl(semset->setid[i], 0, IPC_RMID);
}

int
SemSet_Up(SemSet *semset, int n)
{
  static struct sembuf op;
  int setno, status;

  if (n < 0 || n >= semset->size) {
	PyErr_SetString(PyExc_RuntimeError,
			"semaphore set index out of range");
	return -1;
  }
  setno = SET_NO(n);
  do {
      LOGF("%d [%d] SemSet_Up", my_pindex, my_pid);
      op.sem_num = SEM_NO(n);
      op.sem_op = 1;
      op.sem_flg = 0;
      status = semop(semset->setid[setno], &op, 1);
  } while(status == -1 && errno == EINTR);
  if (status == -1) {
      PyErr_SetFromErrno(PyExc_RuntimeError);
      //"semaphore set UP operation failed");
      return -1;
  }
  return 0;
}

int
SemSet_Down(SemSet *semset, int n)
{
  static struct sembuf op;
  int setno, status;

  if (n < 0 || n >= semset->size) {
	PyErr_SetString(PyExc_RuntimeError,
			"semaphore set index out of range");
	return -1;
  }
  setno = SET_NO(n);
  do {
      LOGF("%d [%d] SemSet_Down", my_pindex, my_pid);
      op.sem_num = SEM_NO(n);
      op.sem_op = -1;
      op.sem_flg = 0;
      status = semop(semset->setid[setno], &op, 1);
  } while(status == -1 && errno == EINTR);
  if (status == -1) {
      PyErr_SetFromErrno(PyExc_RuntimeError);
      //"semaphore set DOWN operation failed");
      return -1;
  }
  return 0;
}
