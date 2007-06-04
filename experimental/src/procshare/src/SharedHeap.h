/* SharedHeap.h */

#ifndef SHAREDHEAP_H_INCLUDED
#define SHAREDHEAP_H_INCLUDED

#include "_core.h"
#include "SharedRegion.h"

/* The type object for SharedHeap objects */
extern PyTypeObject SharedHeap_Type;

/* SharedHeap instances have the following interface:

   alloc(size) -> address, size
   realloc(address, size) -> address, size
   free(address) -> None

   The allocation routines alloc() and realloc() may allocate more bytes
   than requested. The actual size of the allocated block should be returned.

   The addresses are passed as Address objects encapsulating a (void *).
   Out of memory should be signalled by returning an Address object that
   encapsulates NULL. Exceptions raised by the methods will be propagated
   in the normal way.
*/

#endif
