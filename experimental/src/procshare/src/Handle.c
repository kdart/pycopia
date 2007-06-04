/* Handle.c */

#include "Handle.h"
#include "Globals.h"
#include "SharedRegion.h"
#include "SharedObject.h"

/* Table that maps shared memory regions to the addresses at which
   they're attached. The index of a shared memory region is the same
   here as in globals->regtable. The left and right fields are used
   along with the root variable to view the table as a binary search 
   tree when performing a reverse mapping.
   On a fork(), the entire data structure will be duplicated, which is
   correct, since the child process will inherit the attachments of its
   parent. */

static int root = -1;

typedef struct {
  void *start; /* First byte in the region */
  void *end; /* Last byte in the region */
  int left, right; /* These are indexes in the table */
} AttachedRegion;

static AttachedRegion at_map[MAX_REGIONS] = {
  {NULL, NULL, 0, 0},
  /* The entire table is zero-filled */
};

/* Recursively builds an optimal search tree of the entries in
   at_map specified by the given indexes. (The indexes must be
   sorted according to where the regions are attached.)
   Returns the index of the root of the tree. */
static int
optimal_tree(int *indexes, int first, int last)
{
  if (last < first)
	return -1;
  else {
	/* The root should be the median of the sorted indexes */
	int mid = (last+first)/2;
	int r = indexes[mid];
	/* Apply this rule recursively */
	at_map[r].left = optimal_tree(indexes, first, mid-1);
	at_map[r].right = optimal_tree(indexes, mid+1, last);
	/* Return the root */
	return r;
  }
}

/* Comparison function used for sorting in build_tree(). */
static int
compare_indexes(const void *aa, const void *bb)
{
  const int a = *((const int *) aa);
  const int b = *((const int *) bb);

  if (at_map[a].start < at_map[b].start)
	return -1;
  if (at_map[a].start > at_map[b].start)
	return 1;
  if (at_map[a].end < at_map[b].end)
	return -1;
  if (at_map[a].end > at_map[b].end)
	return 1;
  return 0;
}

/* Rebuilds the binary search tree in an optimal way. */
static void
build_tree(void)
{
  int regndx[MAX_REGIONS];
  int i, regcount;

  /* Gather the indexes of all attached regions */
  for (i = regcount = 0; i < MAX_REGIONS; i++)
	if (at_map[i].start != NULL)
	  regndx[regcount++] = i;
  /* Sort the indexes according to where the regions are attached */
  qsort(regndx, regcount, sizeof(int), compare_indexes);
  /* Build the optimal search tree from the sorted indexes */
  root = optimal_tree(regndx, 0, regcount-1);
}


/********************/
/* PUBLIC INTERFACE */
/********************/

/* NULL value for a shared memory handle */
SharedMemHandle _shared_mem_handle_null = SharedMemHandle_INIT_NULL;

void *
SharedMemHandle_AsVoidPtr(SharedMemHandle handle)
{
  AttachedRegion *at;

  if (SharedMemHandle_IS_NULL(handle)) {
	/* No error here; SharedMemHandle_NULL maps to NULL */
	return NULL;
  }

  at = &at_map[handle.regndx];
  if (at->start == NULL) {
	/* Attach the region */
	assert(globals != NULL);
	at->start = _SharedRegion_Attach(globals->regtable.regh[handle.regndx]);
	if (at->start == NULL) {
      /* This is an error */
	  return NULL;
    }
	at->end = at->start + globals->regtable.regsize[handle.regndx] - 1;
	build_tree();
  }
  return at->start + handle.offset;
}

SharedMemHandle
SharedMemHandle_FromVoidPtr(void *ptr)
{
  SharedMemHandle result;
  int i;

  if (ptr == NULL) {
	/* No error here; NULL maps to SharedMemHandle_NULL */
    return SharedMemHandle_NULL;
  }

  /* Search at_map viewed as a binary search tree for an attached region which
	 contains the address. */
  i = root;
  while (i != -1) {
	if (ptr < at_map[i].start)
	  i = at_map[i].left;
	else if (ptr > at_map[i].end)
	  i = at_map[i].right;
	else
	  break;
  }
  if (i == -1) {
	/* No matching attached region.  This is an error. */
	PyErr_SetString(PyExc_RuntimeError, 
                    "reverse memory handle mapping failed");
	return SharedMemHandle_NULL;
  }

  /* We've found an attached region that contains the address. 
	 Construct and return a handle relative to the region. */
  result.regndx = i;
  result.offset = ptr-at_map[i].start;

  return result;  
}

