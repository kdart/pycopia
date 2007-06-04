/* Spinlock.c */

#include "Spinlock.h"

static inline void acquire(int *mutex)
{
    __asm__ volatile ("   movl  %0,%%eax		\n"
                      "1: lock				\n"
		      "   btsl $0, 0(%%eax)	       	\n"
		      "   jc  1b			\n"
		      :
		      :"m"(mutex)
                      :"eax");
}


static inline void release(int *mutex)
{
    __asm__ volatile ("   movl  %0,%%eax		\n"
                      "1: lock				\n"
		      "   andl $0, 0(%%eax)	       	\n"
		      :
		      :"m"(mutex)
                      :"eax");
}


void 
Spinlock_Init(Spinlock *spinlock)
{
  *spinlock = 0;
}

void
Spinlock_Destroy(Spinlock *spinlock)
{
  *spinlock = 0;
}

void
Spinlock_Acquire(Spinlock *spinlock)
{
    acquire(spinlock);
}

void
Spinlock_Release(Spinlock *spinlock)
{
    release(spinlock);
}

