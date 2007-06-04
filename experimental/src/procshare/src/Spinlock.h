/* Spinlock.h */

#ifndef SPINLOCK_H_INCLUDED
#define SPINLOCK_H_INCLUDED

#include "_core.h"

typedef int Spinlock;

/* All these always succeed (if they return). */
void Spinlock_Init(Spinlock *spinlock);
void Spinlock_Destroy(Spinlock *spinlock);
void Spinlock_Acquire(Spinlock *spinlock);
void Spinlock_Release(Spinlock *spinlock);

#endif
