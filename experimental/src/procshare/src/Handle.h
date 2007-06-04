/* Handle.h */

#ifndef HANDLE_H_INCLUDED
#define HANDLE_H_INCLUDED

#include "_core.h"

/* The concept of handles for memory chunks is a way to enable
   referring to the same memory location across different
   processes. Since shared memory regions may be attached at
   different addresses in different processes, a pointer does
   not have the same meaning for all processes. A handle
   _does_ have the same meaning for all processes. */

/* Handle for a location in shared memory. */
typedef struct
{
  int regndx; /* This is the region's index in globals->regtable */
  unsigned int offset; /* This is the offset within the region */
} SharedMemHandle;

/* NULL handle value */
#define SharedMemHandle_NULL _shared_mem_handle_null

/* NULL handle value for use in initializers */
#define SharedMemHandle_INIT_NULL { -1, 0 }

/* Macro to test a handle for NULL-ness */
#define SharedMemHandle_IS_NULL(h) (h.regndx == -1)

extern SharedMemHandle _shared_mem_handle_null;

/* Macro to compare two handles for equality */
#define SharedMemHandle_EQUAL(a, b) \
  ((a).regndx == (b).regndx && (a).offset == (b).offset)

/* Maps a handle for a memory location to a pointer to the location.
   This will attach the shared memory region if necessary. */
void *SharedMemHandle_AsVoidPtr(SharedMemHandle handle);

/* Maps a pointer to a memory location to a handle for the location */
SharedMemHandle SharedMemHandle_FromVoidPtr(void *ptr);

#endif
