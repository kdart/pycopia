/* SharedHeap.c */

#include "SharedHeap.h"
#include "Address.h"
#include "Globals.h"
#include "Handle.h"
#include "Lock.h"

typedef unsigned int word_t;
#define WORD_SIZE sizeof(word_t)

#define MIN_ALLOC_SIZE (WORD_SIZE*16)
#define NOF_ALLOC_SIZES 10
#define MAX_ALLOC_SIZE ((MIN_ALLOC_SIZE << (NOF_ALLOC_SIZES-1)))

#define PAGE_SIZE (MAX_ALLOC_SIZE * 16)

/* Macro for setting a memory word at base+offset */
#define SET_WORD(base, offset, value) \
  *((word_t *) (((void *) base) + (offset))) = value

/* Macro for getting a memory word at base+offset */
#define GET_WORD(base, offset) \
   *((word_t *) (((void *) base) + (offset)))

/* "Root" data structure for a shared heap */
typedef struct
{
  /* Handle to the first page in each of the NOF_ALLOC_SIZES page lists */
  SharedMemHandle head[NOF_ALLOC_SIZES];
  /* One lock per page list, to protect the integrity of the links in
     the list.  Note that each page also has a separate lock to protect
     its list of allocation units. */
  Lock lock[NOF_ALLOC_SIZES];
} root_t;

/* C representation of a SharedHeap object */
typedef struct
{
  PyObject_HEAD
  /* Pointer to the (shared) root data structure. We can refer
	 to this data structure by a pointer, because a fork() will
	 ensure that the region is attached to the same address in
	 the child process. */
  root_t *root;
} SharedHeapObject;

/* Page data structure */
typedef struct
{
  /* Handle for the next page */
  SharedMemHandle next;
  /* Lock to protect the integrity of the linked list of allocation units */
  Lock lock;
  /* The number of allocation units in this page */
  word_t nof_units;
  /* The number of free allocation units in this page */
  word_t nof_free_units;
  /* Allocation unit size, and mask, which is ~(size-1) */
  word_t unit_size;
  word_t unit_mask;
  /* Offset in bytes, from the start of the page, of the first free unit */
  word_t head;
  /* Actual data of the page */
  unsigned char data[1];
} page_t;


/* Allocates and initializes a new root data structure */
static root_t *
new_root(void)
{
  SharedMemHandle rh;
  root_t *root;
  size_t size = sizeof(root_t);
  int i;

  rh = SharedRegion_New(&size);
  root = (root_t *) SharedMemHandle_AsVoidPtr(rh);
  if(root == NULL)
    return NULL;
  for(i = 0; i < NOF_ALLOC_SIZES; i++) {
    root->head[i] = SharedMemHandle_NULL;
    Lock_Init(&root->lock[i]);
  }
  return root;
}

/* Allocates and initializes a page data structure */
static SharedMemHandle
new_page(size_t size, word_t unit_size)
{
  word_t offset, nextoffset;
  SharedMemHandle rh;
  page_t *page;

  rh = SharedRegion_New(&size);
  if(SharedMemHandle_IS_NULL(rh))
    return rh;
  page = (page_t *) SharedMemHandle_AsVoidPtr(rh);
  if(page == NULL)
    return SharedMemHandle_NULL;

  /* Initialize fields */
  page->next = SharedMemHandle_NULL;
  Lock_Init(&page->lock);
  page->unit_size = unit_size;
  page->unit_mask = ~(unit_size-1);
  /* Initialize head, which is the offset of the first free chunk */
  page->head = (offsetof(page_t, data)+unit_size-1) & page->unit_mask;
  /* Initalize the unit counts */
  page->nof_units = (size - page->head)/unit_size;
  page->nof_free_units = page->nof_units;

  /* Create linked list of free blocks */
  offset = page->head;
  nextoffset = offset+unit_size;
  while(nextoffset < size) {
    SET_WORD(page, offset, nextoffset);
    offset = nextoffset;
    nextoffset += unit_size;
  }
  /* Terminate the list with a 0 */
  SET_WORD(page, offset, 0);

  return rh;
}

/* Allocates an allocation unit from the given page.
   Returns NULL on error. */
static void *
alloc_unit(page_t *page)
{
  word_t free;

  /* Unlink the first free unit from the free list */
  Lock_Acquire(&page->lock);
  free = page->head;
  if(free == 0) {
    Lock_Release(&page->lock);
    return NULL;
  }
  page->head = GET_WORD(page, free);
  page->nof_free_units--;
  Lock_Release(&page->lock);

  /* Return a pointer to the unit */
  return ((void *) page) + free;
}

/* Allocates a chunk of memory from the given root structure. */
static void *
alloc_chunk(root_t *root, long *size_arg)
{
  unsigned int ndx;
  page_t *page, *prev_page;
  long size = *size_arg;

  /* Calculate ndx such that 2^(ndx) < size <= 2^(ndx+1) */
  for (ndx = 0; size > MIN_ALLOC_SIZE; ndx++)
    size >>= 1;
  if (ndx >= NOF_ALLOC_SIZES) {
    /* Allocate very big chunks in shared memory regions of their own. */
    size_t *sz = (size_t *) size_arg;
    return SharedMemHandle_AsVoidPtr(SharedRegion_New(sz));
  }

  /* Find a non-empty page on the root->head[ndx] list */
  prev_page = NULL;
  Lock_Acquire(&root->lock[ndx]);
  page = (page_t *) SharedMemHandle_AsVoidPtr(root->head[ndx]);
  while (page != NULL && page->nof_free_units == 0) {
    prev_page = page;
    page = (page_t *) SharedMemHandle_AsVoidPtr(page->next);    
  }
  /* Create and link in a new page if necessary */
  if (page == NULL) {
    SharedMemHandle pageh = new_page(PAGE_SIZE, MIN_ALLOC_SIZE << ndx);
    if (SharedMemHandle_IS_NULL(pageh)) {
      Lock_Release(&root->lock[ndx]);
      return NULL;
    }
    if (prev_page == NULL)
      root->head[ndx] = pageh;
    else
      prev_page->next = pageh;
    page = SharedMemHandle_AsVoidPtr(pageh);
  }
  Lock_Release(&root->lock[ndx]);
  
  /* Allocate a unit from the page, and return the actual size
     of the allocated chunk, along with the pointer */
  *size_arg = page->unit_size;
  return alloc_unit(page);
}

/* Frees a chunk of memory allocated by alloc_chunk(). */
static void 
free_chunk(void *ptr)
{
  page_t *page;

  /* Map the pointer to a handle, so we can find the beginning of
     the shared memory region, which is also the beginning of the page. */
  SharedMemHandle h = SharedMemHandle_FromVoidPtr(ptr);
  if (SharedMemHandle_IS_NULL(h)) {
    /* XXX: This is an (unexpected) error, which is swallowed. */
    return;
  }
  if (h.offset == 0) {
    /* The only chunks allocated at offset 0 in a shared memory region
       are big chunks.  Small chunks always have a positive offset due
       to the page header. */
    SharedRegion_Destroy(h);
    return;
  }
  page = (page_t *) (ptr - h.offset);

  /* Link the chunk into the front of the page's free list */
  Lock_Acquire(&page->lock);
  SET_WORD(ptr, 0, page->head);
  page->head = h.offset;
  page->nof_free_units++;
  Lock_Release(&page->lock);
}

/* Reallocates a chunk of memory in the given root structure.
   On error, this returns NULL, and ptr will still point to a
   valid chunk. */
static void *
realloc_chunk(root_t *root, void *ptr, long *size_arg)
{
  page_t *page;
  void *newptr;
  long cur_size;

  /* Map the pointer to a handle, so we can find the beginning of
     the shared memory region, which is also the beginning of the page. */
  SharedMemHandle h = SharedMemHandle_FromVoidPtr(ptr);
  if (SharedMemHandle_IS_NULL(h))
    return NULL;
  page = (page_t *) (ptr - h.offset);

  /* Get the capacity of the existing allocation unit */
  cur_size = page->unit_size;

  /* Keep the existing unit if it is big enough, and not more
     than twice the size needed. */
  if (cur_size >= *size_arg) {
	/* The existing unit is big enough */
    if (cur_size/4 < MIN_ALLOC_SIZE || cur_size/4 < *size_arg) {
      /* The existing unit is not too big */
      *size_arg = cur_size;
      return ptr;
    }
  }

  /* Allocate a new chunk, copy the contents over, and
	 free the old chunk */
  newptr = alloc_chunk(root, size_arg);
  if (newptr == NULL)
	return NULL;
  if (cur_size > *size_arg)
    cur_size = *size_arg;
  memcpy(newptr, ptr, cur_size);
  free_chunk(ptr);
  return newptr;
}

/**********************/
/* SharedHeap objects */
/**********************/

/* SharedHeap.__init__() method */
static int
heap_init(PyObject *self_, PyObject *args, PyObject *kwargs)
{
  SharedHeapObject *self = (SharedHeapObject *) self_;
  static char *kwlist[] = {NULL};

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "", kwlist))
	return -1;
  self->root = new_root();
  if (self->root == NULL) {
	PyErr_SetString(ErrorObject, "couldn't allocate root data structure");
	return -1;
  }
  return 0;
}

/* SharedHeap.alloc() method */
static PyObject *
heap_alloc(PyObject *self_, PyObject *args)
{
  SharedHeapObject *self = (SharedHeapObject *) self_;
  long size;
  void *ptr;

  if(!PyArg_ParseTuple(args, "l:alloc", &size))
	return NULL;
  ptr = alloc_chunk(self->root, &size);
  return Py_BuildValue("(Nl)", Address_FromVoidPtr(ptr), size);
}

/* SharedHeap.free() method */
static PyObject *
heap_free(PyObject *self, PyObject *args)
{
  PyObject *addr;
  void *ptr;

  if(!PyArg_ParseTuple(args, "O!:free", &Address_Type, &addr))
	return NULL;
  ptr = Address_AsVoidPtr(addr);
  if(ptr != NULL)
	free_chunk(ptr);
  Py_INCREF(Py_None);
  return Py_None;
}

/* SharedHeap.realloc() method */
static PyObject *
heap_realloc(PyObject *self_, PyObject *args)
{
  SharedHeapObject *self = (SharedHeapObject *) self_;
  PyObject *addr;
  long size;
  void *ptr;

  if(!PyArg_ParseTuple(args, "O!l:realloc", &Address_Type, &addr, &size))
	return NULL;
  ptr = Address_AsVoidPtr(addr);
  ptr = realloc_chunk(self->root, ptr, &size);
  return Py_BuildValue("(Nl)", Address_FromVoidPtr(ptr), size);
}

static char heap_alloc_doc[] =
"heap.alloc(size) -> address, size -- allocate a block of memory";
static char heap_free_doc[] =
"heap.free(address) -- free an allocated block";
static char heap_realloc_doc[] =
"heap.realloc(address, size) -> address, size -- reallocate a block of memory";

static PyMethodDef heap_methods[] = {
	{"alloc", heap_alloc, METH_VARARGS, heap_alloc_doc},
	{"free", heap_free, METH_VARARGS, heap_free_doc},
	{"realloc", heap_realloc, METH_VARARGS, heap_realloc_doc},
	{NULL, NULL} /* sentinel */
};

static char heap_doc[] =
"SharedHeap() -> new shared heap";

PyTypeObject SharedHeap_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.SharedHeap",
	sizeof(SharedHeapObject),
	0,
	0,           		/* tp_dealloc */
	0,      			/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	0,       			/* tp_repr */
	0,					/* tp_as_number */
	0,       			/* tp_as_sequence */
	0,					/* tp_as_mapping */
	0,    				/* tp_hash */
	0,					/* tp_call */
	0,					/* tp_str */
	0,                  /* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	heap_doc,           /* tp_doc */
 	0,                  /* tp_traverse */
 	0,                  /* tp_clear */
	0,                  /* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	heap_methods,       /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	heap_init,			/* tp_init */
	0,                  /* tp_alloc */
	PyType_GenericNew,  /* tp_new */
	0,                  /* tp_free */
};
