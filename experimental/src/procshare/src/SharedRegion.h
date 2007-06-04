/* SharedRegion.h */
/* Interface for creation and attachment of shared memory regions. */

#ifndef SHAREDREGION_H_INCLUDED
#define SHAREDREGION_H_INCLUDED

#include "_core.h"

/* Handle for a shared memory region. */
typedef int SharedRegionHandle;

/* NULL value for a shared memory region handle */
#define SharedRegionHandle_NULL (-1)

/* Macro to test for NULL-ness of shared memory region handles */
#define SharedRegionHandle_IS_NULL(h) (h == SharedRegionHandle_NULL)

/* Creates a new shared memory region of the given size.
   Returns a handle for the region, or SharedRegionHandle_NULL on error.
   This function should normally not be called directly - use
   SharedRegion_New() instead (defined in Globals.h), which stores
   the handle in a global table for cleanup purposes. */
SharedRegionHandle _SharedRegion_New(size_t *size);

/* Destroys a shared memory region. */
void _SharedRegion_Destroy(SharedRegionHandle h);

/* Attaches a shared memory region. */
void *_SharedRegion_Attach(SharedRegionHandle h);

/* Detaches a shared memory region that is attached at the given address. */
int _SharedRegion_Detach(void *addr);

#endif
