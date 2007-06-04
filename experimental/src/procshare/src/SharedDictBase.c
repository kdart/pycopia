/* SharedDictBase.c */

#include "SharedDictBase.h"
#include "SharedAlloc.h"
#include "SharedHeap.h"
#include "share.h"

/* The implementation of SharedDictBase mirrors that of normal dicts,
   found in Objects/dictobject.c. For further explanations of the
   algorithms used, look there. */

/* Constant related to collision resolution in lookup(). See dictobject.c */
#define PERTURB_SHIFT 5

/* Minimum size of the hash table */
#define MIN_SIZE 8

/* Macro to determine whether it is time to resize a dictionary */
#define TIME_TO_RESIZE(d) ((d)->fill*3 >= ((d)->mask+1)*2)

/* SharedDictBase object */
typedef struct {
  PyObject_HEAD
  int fill; /* # Active + # Deleted */
  int used; /* # Active */
  int mask; /* # Slots -1 */
  SharedMemHandle tableh; /* Handle to table of entries */
} SharedDictBaseObject;

/* States for hash table entries */
#define ES_FREE 0
#define ES_INUSE 1
#define ES_DELETED 2
#define ES_ERROR 3

/* Hash table entry */
typedef struct {
  int state;
  long hash;
  SharedMemHandle keyh;
  SharedMemHandle valueh;
} Entry;


/* Entry returned on error */
static Entry error_entry = {
  ES_ERROR, /* state */
  0, /* hash */
  SharedMemHandle_INIT_NULL, /* keyh */ 
  SharedMemHandle_INIT_NULL, /* valueh */
};


/* The basic lookup function used by all operations.

   This function must never return NULL; failures are indicated by returning
   an Entry * for which the state field is ES_ERROR.
   Exceptions are never reported by this function, and outstanding
   exceptions are maintained.
*/ 
static Entry *
dict_lookup(SharedDictBaseObject *d, PyObject *key, long hash) 
{
  int i, cmp;
  unsigned int perturb;
  unsigned int mask;
  Entry *freeslot, *ep, *table;
  SharedMemHandle orig_tableh, orig_keyh;
  PyObject *epkey;
  int restore_error;
  PyObject *err_type, *err_value, *err_tb;

  table = (Entry *) SharedMemHandle_AsVoidPtr(d->tableh);
  if(table == NULL)
	return &error_entry;

  /* Compute the initial table index */
  mask = d->mask;
  i = hash & mask;
  ep = &table[i];
  if (ep->state == ES_FREE)
	return ep;

  /* Save any pending exception */
  restore_error = (PyErr_Occurred() != NULL);
  if (restore_error)
	PyErr_Fetch(&err_type, &err_value, &err_tb);

  /* From here on, all exits should be via 'goto Done' */

  orig_tableh = d->tableh;
  freeslot = NULL;
  perturb = hash;

  while (1) {
	if (ep->state == ES_FREE) {
	  /* When we hit a free entry, it means that the key isn't present.
		 If we encountered a deleted entry earlier, that is also a correct
		 position for insertion, and a more optimal one. */
	  if (freeslot != NULL)
		ep = freeslot;
	  goto Done;
	}
	if (ep->hash == hash && ep->state == ES_INUSE) {
	  /* When the hash codes match, the keys are possibly equal. When
		 comparing them, we must be aware that the comparison may mutate
		 the dictionary. */
	  orig_keyh = ep->keyh;
	  epkey = SharedObject_AS_PYOBJECT(SharedMemHandle_AsVoidPtr(orig_keyh));
	  cmp = PyObject_RichCompareBool(epkey, key, Py_EQ);
	  if (cmp < 1)
		PyErr_Clear(); /* Swallow exceptions during comparison */
	  else {
		if (SharedMemHandle_EQUAL(orig_tableh, d->tableh)
			&& SharedMemHandle_EQUAL(orig_keyh, ep->keyh)) {
		  /* The dictionary seems to be intact */
		  if (cmp == 1)
			/* And the keys are indeed equal */
			goto Done;
		}
		else {
		  /* The compare did major nasty stuff to the dict: start over. */
		  ep = dict_lookup(d, key, hash);
		  goto Done;
		}
	  }
	}
	if (ep->state == ES_DELETED && freeslot == NULL)
	  /* This is the first deleted entry we encounter */
	  freeslot = ep;

	/* Collision - compute the next table index and try again */
	i = (i << 2) + i + perturb + 1;
	perturb >>= PERTURB_SHIFT;
	ep = &table[i & mask];
  }
    
 Done:
  /* Restore any previously pending exception */
  if (restore_error)
	PyErr_Restore(err_type, err_value, err_tb);
  return ep;
}


/* Makes the dictionary empty by allocating a new table and clearing it.
   Saves a pointer to the old table. Used by dict_tp_new(),
   dict_resize() and dict_clear(). */
static int
dict_empty(SharedDictBaseObject *self, int minused, Entry **oldtable)
{
  int newsize, actsize, twice_newsize;
  size_t bytes;
  Entry *newtable;

  /* Find the smallest table size > minused. */
  for (newsize = MIN_SIZE; newsize <= minused && newsize > 0; newsize <<= 1)
	;
  if (newsize <= 0) {
	PyErr_NoMemory();
	return -1;
  }

  if(oldtable != NULL)
	/* Get a pointer to the old table */
	*oldtable = (Entry *) SharedMemHandle_AsVoidPtr(self->tableh);

  /* Allocate the new table */
  bytes = sizeof(Entry) * newsize;
  newtable = (Entry *) SharedAlloc((PyObject *) self, &bytes);
  if (newtable == NULL) {
	PyErr_NoMemory();
	return -1;
  }
  /* SharedAlloc() may actually have allocated more bytes than requested,
     so we take advantage of that if it means we can double the table size */
  actsize = (bytes / sizeof(Entry));
  twice_newsize = newsize << 1;
  while (twice_newsize > 0 && actsize >= twice_newsize) {
	newsize = twice_newsize;
	twice_newsize <<= 1;
  }
  /* Zero out the table - this makes state == ES_FREE for all entries */
  memset(newtable, 0, sizeof(Entry) * newsize);

  /* Make the dict empty, using the new table */
  self->tableh = SharedMemHandle_FromVoidPtr(newtable);
  self->mask = newsize - 1;
  self->used = 0;
  self->fill = 0;
  return 0;
}


/* Resizes the dictionary by reallocating the table and reinserting all
   the items again. When entries have been deleted, the new table may 
   actually be smaller than the old one.
*/
static int
dict_resize(SharedDictBaseObject *self, int minused)
{
  int used = self->used; /* Make a copy of this before calling dict_empty() */
  Entry *oldtable, *oldep, *ep;
  PyObject *key;

  /* Make the dictionary empty, with a new table */
  if(dict_empty(self, minused, &oldtable))
	return -1;

  /* Copy the data over from the old table; this is refcount-neutral
	 for active entries. */
  assert(oldtable != NULL);
  for(oldep = oldtable; used > 0; oldep++) {
	if(oldep->state == ES_INUSE) {
	  /* Active entry */
	  used--;
	  key = SharedObject_AS_PYOBJECT(SharedMemHandle_AsVoidPtr(oldep->keyh));
 
	  ep = dict_lookup(self, key, oldep->hash);
	  if(ep->state == ES_FREE) {
		ep->keyh = oldep->keyh;
		ep->valueh = oldep->valueh;
		ep->hash = oldep->hash;
		ep->state = ES_INUSE;
		self->fill++;
		self->used++;
	  }
	  else
		assert(ep->state == ES_ERROR);
	}
  }

  /* Free the old table */
  SharedFree((PyObject *) self, oldtable);

  return 0;
}


/* Generic routine for updating the mapping object a with the items
   of mapping object b. b's values override those already present in a. */
static int
mapping_update(PyObject *a, PyObject *b)
{
  PyObject *keys, *iter, *key, *value;
  int status;
  
  /* Get b's keys */
  keys = PyMapping_Keys(b);
  if (keys == NULL)
	return -1;
  
  /* Get an iterator for them */	
  iter = PyObject_GetIter(keys);
  Py_DECREF(keys);
  if (iter == NULL)
	return -1;
  
  /* Iterate over the keys in b and insert the items in a */
  for (key = PyIter_Next(iter); key; key = PyIter_Next(iter)) {
	value = PyObject_GetItem(b, key);
	if (value == NULL) {
	  Py_DECREF(iter);
	  Py_DECREF(key);
	  return -1;
	}
	status = PyObject_SetItem(a, key, value);
	Py_DECREF(key);
	Py_DECREF(value);
	if (status < 0) {
	  Py_DECREF(iter);
	  return -1;
	}
  }
  Py_DECREF(iter);
  if (PyErr_Occurred())
	/* Iterator completed, via error */
	return -1;
  return 0;
}


/* Creates a new, empty shared dictionary */
static PyObject *
dict_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
  PyObject *self;

  self = type->tp_alloc(type, 0);
  if (self != NULL)
	if(dict_empty((SharedDictBaseObject *) self, 1, NULL)) {
	  self->ob_type->tp_free(self);
	  return NULL;
	}
  return self;
}


/* Initializes a shared dictionary from a dictionary */
static int
dict_tp_init(PyObject *self_, PyObject *args, PyObject *kwargs)
{
  PyObject *arg = NULL;

  if(!PyArg_ParseTuple(args, "|O:SharedDictBase.__init__", &arg))
	return -1;
  if(arg != NULL)
	return mapping_update(self_, arg);
  return -1;
}


/* DECREFs the items in a table, and frees the table itself. Used by
   dict_tp_dealloc() and dict_clear().
   CAUTION: This is only safe to use if the items in the table have
   no opportunity to mutate the table when they are destroyed. */
static void
delete_table(PyObject *self_, Entry *table, int used)
{
  Entry *ep;
  SharedObject *obj;

  if(table != NULL) {
	for (ep = table; used > 0; ep++) {
	  if (ep->state == ES_INUSE) {
		--used;
		obj = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->keyh);
		SharedObject_DecRef(obj);
		obj = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
		SharedObject_DecRef(obj);
	  }
	}
	SharedFree(self_, table);
  }
}


/* Deinitializes a shared dictionary */
static void
dict_tp_dealloc(PyObject *self_)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  Entry *table;

  table = (Entry *) SharedMemHandle_AsVoidPtr(self->tableh);
  delete_table(self_, table, self->used);
  self_->ob_type->tp_free(self_);
}


/* Clears a shared dictionary */
static PyObject *
dict_clear(PyObject *self_, PyObject *noargs)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  Entry *oldtable;
  int used = self->used;

  if(dict_empty(self, 1, &oldtable))
	return NULL;
  /* We can now safely delete the items in the old table, because
	 dict_empty() allocated a new table for the dict, and we made
	 a copy of the number of used slots. This means that the destructors
	 of the items can only mutate the new, empty dict */
  delete_table(self_, oldtable, used);
  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
dict_tp_repr(PyObject *self_)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  int i;
  PyObject *s, *temp;
  SharedObject *key, *value;
  PyObject *colon = NULL, *pieces = NULL, *result = NULL;
  Entry *table;

  i = Py_ReprEnter(self_);
  if (i != 0) {
	/* Recursive data structure */
	return i > 0 ? PyString_FromString("{...}") : NULL;
  }
  if (self->used == 0) {
	/* Empty dictionary */
	result = PyString_FromString("{}");
	goto Done;
  }

  /* Allocate an empty list and a ": " string */  
  pieces = PyList_New(0);
  if (pieces == NULL)
	goto Done;
  colon = PyString_FromString(": ");
  if (colon == NULL)
	goto Done;

  table = (Entry *) SharedMemHandle_AsVoidPtr(self->tableh);
  assert(table != NULL);

  /* Do repr() on each key+value pair, and insert ": " between them.
	 Note that repr may mutate the dict. */
  for (i = 0; i <= self->mask; i++) {
	if (table[i].state == ES_INUSE) {
	  int status;
	  
	  /* Get the key and value objects from the entry's handles */
	  key = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].keyh);
	  value = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].valueh);
	  assert(key != NULL && value != NULL);

	  /* Prevent repr from deleting value during key format. */
	  SharedObject_IncRef(value);
	  s = SharedObject_Repr(key);
	  PyString_Concat(&s, colon);
	  PyString_ConcatAndDel(&s, SharedObject_Repr(value));
	  SharedObject_DecRef(value);
	  if (s == NULL)
		goto Done;
	  status = PyList_Append(pieces, s);
	  Py_DECREF(s);  /* append created a new ref */
	  if (status < 0)
		goto Done;
	}
  }

  /* Add "{}" decorations to the first and last items. */
  assert(PyList_GET_SIZE(pieces) > 0);
  s = PyString_FromString("{");
  if (s == NULL)
	goto Done;
  temp = PyList_GET_ITEM(pieces, 0);
  PyString_ConcatAndDel(&s, temp);
  PyList_SET_ITEM(pieces, 0, s);
  if (s == NULL)
	goto Done;

  s = PyString_FromString("}");
  if (s == NULL)
	goto Done;
  temp = PyList_GET_ITEM(pieces, PyList_GET_SIZE(pieces) - 1);
  PyString_ConcatAndDel(&temp, s);
  PyList_SET_ITEM(pieces, PyList_GET_SIZE(pieces) - 1, temp);
  if (temp == NULL)
	goto Done;

  /* Paste them all together with ", " between. */
  s = PyString_FromString(", ");
  if (s == NULL)
	goto Done;
  result = _PyString_Join(s, pieces);
  Py_DECREF(s);

 Done:
  Py_XDECREF(pieces);
  Py_XDECREF(colon);
  Py_ReprLeave(self_);
  return result;
}


/* Raises an exception on attempt to hash a shared dictionary */
static long
dict_tp_nohash(PyObject *self)
{
  PyErr_Format(PyExc_TypeError, "%.100s objects are unhashable",
			   self->ob_type->tp_name);
  return -1;
}


static int
dict_mp_length(PyObject *self_)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;

  return self->used;
}


static PyObject *
dict_mp_subscript(PyObject *self_, PyObject *key)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  Entry *ep;
  long hash;

  hash = PyObject_Hash(key);
  if(hash == -1)
	return NULL;
  ep = dict_lookup(self, key, hash);
  if(ep->state == ES_INUSE) {
	SharedObject *obj = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
	assert(obj != NULL);
	return MakeProxy(obj);
  }
  PyErr_SetObject(PyExc_KeyError, key);
  return NULL;
}


/* Deletes a (key, value) pair from the dictionary. */
static int
dict_delitem(SharedDictBaseObject *self, PyObject *lookupkey, long hash)
{
  Entry *ep;
  
  ep = dict_lookup(self, lookupkey, hash);
  if(ep->state == ES_INUSE) {
	SharedObject *key, *value;

	key = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->keyh);
	value = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
	ep->state = ES_DELETED;
	self->used--;
	SharedObject_DecRef(key);
	SharedObject_DecRef(value);
	return 0;
  }
  return -1;
}


static int
dict_mp_ass_sub(PyObject *self_, PyObject *key, PyObject *value)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  SharedObject *shkey, *shvalue;
  Entry *ep;
  long hash;

  /* Hash the key (we should be able to do this before sharing it,
     since shared objects should have the same hash function as their
     non-shared counterparts) */
  hash = PyObject_Hash(key);
  if (hash == -1)
	return -1;

  if (value == NULL) {
	/* Delete an item */
	if (!dict_delitem(self, key, hash))
	  return 0;
	PyErr_SetObject(PyExc_KeyError, key);
	return -1;
  }

  /* Share the value object (sharing the key can
	 wait - that might not be necessary) */
  shvalue = ShareObject(value);
  if (shvalue == NULL)
	return -1;
  SharedObject_IncRef(shvalue);
  
  assert(self->fill <= self->mask); /* At least one empty slot */
 
  ep = dict_lookup(self, key, hash);
  if (ep->state == ES_INUSE) {
	/* Replace the value of an existing key */
	SharedObject *oldvalue;
	oldvalue = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
	ep->valueh = SharedMemHandle_FromVoidPtr(shvalue);
	SharedObject_DecRef(oldvalue);
  }
  else {
	assert(ep->state == ES_FREE);
	/* We are inserting a new key, so we must share it */
	shkey = ShareObject(key);
	if (shkey == NULL)
	  return -1;
	SharedObject_IncRef(shkey);

	if(ep->state == ES_FREE)
	  self->fill++;

	ep->keyh = SharedMemHandle_FromVoidPtr(shkey);
	ep->valueh = SharedMemHandle_FromVoidPtr(shvalue);
	ep->hash = hash;
	ep->state = ES_INUSE;
	self->used++;
	
	/* Possibly resize the dictionary */
	if (TIME_TO_RESIZE(self))
	  if (dict_resize(self, self->used*2))
		return -1;
  }
  return 0;
}


static int
dict_sq_contains(PyObject *self_, PyObject *key)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  long hash;

  hash = PyObject_Hash(key);
  if (hash == -1)
	return -1;
  return (dict_lookup(self, key, hash)->state == ES_INUSE);
}


static PyObject *
dict_has_key(PyObject *self_, PyObject *key)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  long hash;
  long ok;

  hash = PyObject_Hash(key);
  if (hash == -1)
	return NULL;
  ok = (dict_lookup(self, key, hash)->state == ES_INUSE);
  return PyInt_FromLong(ok);
}


static PyObject *
dict_get(PyObject *self_, PyObject *args)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  PyObject *key;
  PyObject *failobj = Py_None;
  Entry *ep;
  long hash;

  if (!PyArg_ParseTuple(args, "O|O:get", &key, &failobj))
	return NULL;

  hash = PyObject_Hash(key);
  if (hash == -1)
	return NULL;

  ep = dict_lookup(self, key, hash);
  if (ep->state == ES_INUSE) {
	SharedObject *obj = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
	assert(obj != NULL);
	return MakeProxy(obj);
  }
  Py_INCREF(failobj);
  return failobj;
}


static PyObject *
dict_setdefault(PyObject *self_, PyObject *args)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  PyObject *key;
  PyObject *failobj = Py_None;
  Entry *ep;
  long hash;

  if (!PyArg_ParseTuple(args, "O|O:setdefault", &key, &failobj))
	return NULL;

  hash = PyObject_Hash(key);
  if (hash == -1)
	return NULL;

  ep = dict_lookup(self, key, hash);
  if (ep->state == ES_INUSE) {
	SharedObject *obj = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
	assert(obj != NULL);
	return MakeProxy(obj);
  }
  if (dict_mp_ass_sub(self_, key, failobj))
	return NULL;
  Py_INCREF(failobj);
  return failobj;
}


static PyObject *
dict_keys_or_values(SharedDictBaseObject *self, int keys)
{
  PyObject *list, *proxy;
  SharedObject *obj;
  int i, j, used;
  Entry *table;

 again:
  /* Allocate a list to hold the keys or values */
  used = self->used;
  list = PyList_New(used);
  if (list == NULL)
	return NULL;
  if (used != self->used) {
	/* The allocation caused the dict to resize - start over. */
	Py_DECREF(list);
	goto again;
  }

  table = SharedMemHandle_AsVoidPtr(self->tableh);
  assert(table != NULL);

  for (i = 0, j = 0; i <= self->mask; i++) {
	if (table[i].state == ES_INUSE) {
	  /* Get the key/value object from the entry's handle */
	  if (keys)
		obj = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].keyh);
	  else
		obj = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].valueh);
	  assert(obj != NULL);

	  /* Encapsulate the key/value in a proxy object */
	  proxy = MakeProxy(obj);
	  if(proxy == NULL) {
		Py_DECREF(list);
		return NULL;
	  }

	  /* Insert the object in the list */
	  PyList_SET_ITEM(list, j, proxy);
	  j++;
	}
  }
  assert(j == used);
  return list;
}


static PyObject *
dict_keys(PyObject *self, PyObject *noargs)
{
  return dict_keys_or_values((SharedDictBaseObject *) self, 1);
}


static PyObject *
dict_values(PyObject *self, PyObject *noargs)
{
  return dict_keys_or_values((SharedDictBaseObject *) self, 0);
}


static PyObject *
dict_items(PyObject *self_, PyObject *noargs)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  PyObject *list;
  int i, j, used;
  PyObject *item, *key, *value;
  SharedObject *shkey, *shvalue;
  Entry *table;

  /* Preallocate the list of tuples, to avoid allocations during
   * the loop over the items, which could trigger GC, which
   * could resize the dict. :-(
   */
 again:
  used = self->used;
  list = PyList_New(used);
  if (list == NULL)
	return NULL;
  for (i = 0; i < used; i++) {
	item = PyTuple_New(2);
	if (item == NULL) {
	  Py_DECREF(list);
	  return NULL;
	}
	PyList_SET_ITEM(list, i, item);
  }
  if (used != self->used) {
	/* The allocations caused the dict to resize - start over. */
	Py_DECREF(list);
	goto again;
  }

  table = (Entry *) SharedMemHandle_AsVoidPtr(self->tableh);
  assert(table != NULL);

  for (i = 0, j = 0; i <= self->mask; i++) {
	if (table[i].state == ES_INUSE) {
	  /* Get the key and value objects from the entry's handles */
	  shkey = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].keyh);
	  shvalue = (SharedObject *) SharedMemHandle_AsVoidPtr(table[i].valueh);
	  assert(key != NULL && value != NULL);

	  /* Encapsulate the key and value in proxy objects */
	  key = MakeProxy(shkey);
	  if(key == NULL) {
		Py_DECREF(list);
		return NULL;
	  }
	  value = MakeProxy(shvalue);
	  if(value == NULL) {
		Py_DECREF(key);
		Py_DECREF(list);
		return NULL;
	  }

	  /* Insert the (key, value) tuple in the list */
	  item = PyList_GET_ITEM(list, j);
	  PyTuple_SET_ITEM(item, 0, key);
	  PyTuple_SET_ITEM(item, 1, value);
	  j++;
	}
  }
  assert(j == used);
  return list;
}


static PyObject *
dict_update(PyObject *self, PyObject *other)
{
  if(mapping_update(self, other))
	return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
dict_copy(PyObject *self, PyObject *noarg)
{
  PyObject *result = PyDict_New();

  if(result != NULL) {
	/* Here, result is a plain dict, so we use PyDict_Update(), and not
	   the generic mapping_update() */
	if(PyDict_Update(result, self)) {
	  Py_DECREF(result);
	  result = NULL;
	}
  }
  return result;
}


static PyObject *
dict_popitem(PyObject *self_, PyObject *noargs)
{
  SharedDictBaseObject *self = (SharedDictBaseObject *) self_;
  PyObject *res, *proxy;
  SharedObject *key, *value;
  Entry *table, *ep;
  int i = 0;

  /* Allocate the result tuple before checking the size. This is because
	 of the possible side effects (garbage collection) of the allocation. */
  res = PyTuple_New(2);
  if (res == NULL)
	return NULL;
  if (self->used == 0) {
	PyErr_SetString(PyExc_KeyError,	"popitem(): dictionary is empty");
	goto Error;
  }

  table = SharedMemHandle_AsVoidPtr(self->tableh);
  assert(table != NULL);

  /* We abuse the hash field of slot 0 to hold a search finger, just like
	 the implementation of normal dictionaries. */
  ep = table;
  if (ep->state == ES_INUSE)
	/* Return slot 0 */ ;
  else {
	/* Search the remaining slots for a used slot, starting at
	   the hash value of slot 0, which may or may not have been
	   stored by a previous popitem(). In any case, it works, so
	   this is just an optimization to cater to repeated popitem()
	   calls. */
	i = (int) ep->hash;

	if (i > self->mask || i < 1)
	  i = 1;	/* skip slot 0 */
	while ((ep = &table[i])->state != ES_INUSE) {
	  if (++i > self->mask)
		i = 1;
	}
  }

  /* Now put the key and value that ep points to in the result tuple,
	 wrapped in proxy objects. */
  key = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->keyh);
  value = (SharedObject *) SharedMemHandle_AsVoidPtr(ep->valueh);
  assert(key != NULL && value != NULL);

  proxy = MakeProxy(key);
  if(proxy == NULL)
	goto Error;
  PyTuple_SET_ITEM(res, 0, proxy);
  proxy = MakeProxy(value);
  if(proxy == NULL)
	goto Error; /* This does DECREF the previous proxy, since it is
				   already stored in the result tuple */
  PyTuple_SET_ITEM(res, 1, proxy);

  /* The result tuple is safely constructed - now clear the slot */
  ep->state = ES_DELETED;
  self->used--;

  table[0].hash = i + 1;  /* next place to start */

  /* Decref the removed key+value */
  SharedObject_DecRef(key);
  SharedObject_DecRef(value);
  return res;

 Error:
  Py_DECREF(res);
  return NULL;
}


static PyMappingMethods dict_tp_as_mapping = {
  dict_mp_length, /* mp_length */
  dict_mp_subscript, /* mp_subscript */
  dict_mp_ass_sub, /* mp_ass_subscript */
};


/* Hack to implement "key in dict" */
static PySequenceMethods dict_tp_as_sequence = {
	0,					/* sq_length */
	0,					/* sq_concat */
	0,					/* sq_repeat */
	0,					/* sq_item */
	0,					/* sq_slice */
	0,					/* sq_ass_item */
	0,					/* sq_ass_slice */
	dict_sq_contains,   /* sq_contains */
	0,					/* sq_inplace_concat */
	0,					/* sq_inplace_repeat */
};


static char has_key_doc[] =
"D.has_key(k) -> 1 if D has a key k, else 0";

static char get_doc[] =
"D.get(k[,d]) -> D[k] if D.has_key(k), else d.  d defaults to None.";

static char setdefault_doc[] =
"D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if not D.has_key(k)";

static char popitem_doc[] =
"D.popitem() -> (k, v), remove and return some (key, value) pair as a\n\
2-tuple; but raise KeyError if D is empty";

static char keys_doc[] =
"D.keys() -> list of D's keys";

static char items_doc[] =
"D.items() -> list of D's (key, value) pairs, as 2-tuples";

static char values_doc[] =
"D.values() -> list of D's values";

static char update_doc[] =
"D.update(E) -> None.  Update D from E: for k in E.keys(): D[k] = E[k]";

static char clear_doc[] =
"D.clear() -> None.  Remove all items from D.";

static char copy_doc[] =
"D.copy() -> a shallow copy of D";

static char iterkeys_doc[] =
"D.iterkeys() -> an iterator over the keys of D";

static char itervalues_doc[] =
"D.itervalues() -> an iterator over the values of D";

static char iteritems_doc[] =
"D.iteritems() -> an iterator over the (key, value) items of D";

static PyMethodDef dict_tp_methods[] = {
  {"has_key", dict_has_key, METH_O, has_key_doc},
  {"get", dict_get, METH_VARARGS, get_doc},
  {"setdefault", dict_setdefault, METH_VARARGS, setdefault_doc},
  {"popitem", dict_popitem, METH_NOARGS, popitem_doc},
  {"keys", dict_keys, METH_NOARGS, keys_doc},
  {"items",	dict_items, METH_NOARGS, items_doc},
  {"values", dict_values, METH_NOARGS, values_doc},
  {"update", dict_update, METH_O, update_doc},
  {"clear",	dict_clear, METH_NOARGS, clear_doc},
  {"copy", dict_copy, METH_NOARGS, copy_doc},
  /*  {"iterkeys", dict_iterkeys, METH_NOARGS, iterkeys_doc}, */
  /*  {"itervalues", dict_itervalues, METH_NOARGS, itervalues_doc}, */
  /*  {"iteritems",	dict_iteritems, METH_NOARGS, iteritems_doc}, */
  {NULL, NULL} /* sentinel */
};


static char dict_tp_doc[] =
"Abstract base class for shared dictionaries";

PyTypeObject SharedDictBase_Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"_procshare_core.SharedDictBase",
	sizeof(SharedDictBaseObject),
	0,
	dict_tp_dealloc,    /* tp_dealloc */
	0,      			/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_compare */
	dict_tp_repr,       /* tp_repr */
	0,					/* tp_as_number */
	&dict_tp_as_sequence, /* tp_as_sequence */
	&dict_tp_as_mapping, /* tp_as_mapping */
	dict_tp_nohash,     /* tp_hash */
	0,					/* tp_call */
	dict_tp_repr,       /* tp_str */
	0,              	/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
 	dict_tp_doc,        /* tp_doc */
 	0,           		/* tp_traverse */
 	0,      			/* tp_clear */
	0,      			/* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	dict_tp_methods,    /* tp_methods */
	0,					/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	dict_tp_init,       /* tp_init */
	0,      			/* tp_alloc */
	dict_tp_new,        /* tp_new */
	0,      			/* tp_free */
};
