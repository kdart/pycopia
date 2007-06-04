/* SemSet.h */

#ifndef SEMSET_H_INCLUDED
#define SEMSET_H_INCLUDED

#include "_core.h"

#define MAX_SYSV_SET_SIZE 60
#define SYSV_SETS_PER_SEMSET 16

#define MAX_SEMSET_SIZE MAX_SYSV_SET_SIZE * SYSV_SETS_PER_SEMSET

/* A SemSet semaphore set is implemented by up to SYSV_SETS_PER_SEMSET
   system V semaphore sets. */
typedef struct {
  int size;
  int setid[SYSV_SETS_PER_SEMSET];
} SemSet;

/* Initializes a semaphore set with 'size' semaphores initially set to 0. */
int SemSet_Init(SemSet *semset, int size);

/* Destroys a semaphore set. */
void SemSet_Destroy(SemSet *semset);

/* Does an 'Up' operation on the specified semaphore in the semaphore set. */
int SemSet_Up(SemSet *semset, int n);

/* Does a 'Down' operation on the specified semaphore in the semaphore set. */
int SemSet_Down(SemSet *semset, int n);

#endif
