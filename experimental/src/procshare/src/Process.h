/* Process.h */

#ifndef PROCESS_H_INCLUDED
#define PROCESS_H_INCLUDED

#include "_core.h"

/* We allow 4 ints for a process bitmap - this limits
   how many processes there can be. */
#define PROCESS_BITMAP_INTS 4
#define INT_BITS (sizeof(int)*8)
#define MAX_PROCESSES (INT_BITS*PROCESS_BITMAP_INTS)

/* A bitmap of processes, and macros for operations on it */
typedef struct {
  int i[PROCESS_BITMAP_INTS];
} ProcessBitmap;

#define ProcessBitmap_SET(bmp, ndx) \
  (bmp).i[(ndx)/INT_BITS] |= (1 << (ndx)%INT_BITS)

#define ProcessBitmap_IS_SET(bmp, ndx) \
  (((bmp).i[(ndx)/INT_BITS] & (1 << (ndx)%INT_BITS)) != 0)

#define ProcessBitmap_CLEAR(bmp, ndx) \
  (bmp).i[(ndx)/INT_BITS] &= ~(1 << (ndx)%INT_BITS)

/* Update these macros in accordance with PROCESS_BITMAP_INTS */
#define ProcessBitmap_IS_ZERO(bmp) \
  ((bmp).i[0] == 0 && (bmp).i[1] == 0 && (bmp).i[2] == 0 && (bmp).i[3] == 0)

#define ProcessBitmap_CLEAR_ALL(bmp) \
  {(bmp).i[0] = 0; (bmp).i[1] = 0; (bmp).i[2] = 0; (bmp).i[3] = 0; }

#define ProcessBitmap_IS_ALL_SET(bmp) \
  ((bmp).i[0] == (~0) && (bmp).i[1] == (~0) \
    && (bmp).i[2] == (~0) && (bmp).i[3] == (~0))

/* Initializes this process. Should be called on startup and after a fork(). */
int Process_Init(void);

/* Called by a process when it terminates (normally). */
void Process_Cleanup(void);

/* Cleans up after a child process that has terminated abnormally. */
void Process_CleanupChild(int pid);

#endif
