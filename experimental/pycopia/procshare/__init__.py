#!/usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# A copy of Steffen Viken Valvaag "posh" module. Modified by Keith Dart to
# work seamlessly with the pyNMS proctools module. 

# Portions Copyright (C) 2003 Steffen Viken Valvaag, but modified by Keith
# Dart.


from types import ClassType
from os import fork as _os_fork

import _procshare_core as _core
from procshare import _proxy

import scheduler

# Import some names from the _core module
share = _core.share
Error = _core.Error
Lock = _core.Lock
child_died = _core.child_died


# The default argument for allow_sharing()
MONITOR = _core.Monitor()

_has_forked = 0

# Argument to allow_sharing() that specifies no synchronization
NOSYNCH = None


class SharedType(type):
    """Meta-type for shared types.
    """
    # Shared heaps for instances and auxiliary data structures
    __instanceheap__ = _core.SharedHeap()
    __dataheap__ = _core.SharedHeap()

    # Default synchronization policy
    __synch__ = MONITOR 

    # This method gets invoked when the meta-type is called, and
    # returns a new shared type.
    def __new__(tp, name, bases, dct):
        """Creates a new shared type.
        """
        def wrap_built_in_func(func):
            """Wraps a built-in function in a function object.
            """
            # XXX: This is not quite satisfactory, since we lose the
            # __name__ and __doc__ attributes.  Built-in functions
            # really should have binding behaviour!
            return lambda *args, **kwargs: func(*args, **kwargs)

        if len(bases) > 1:
            raise ValueError, "this meta-type only supports single inheritance"

        # Override attribute access
        dct["__getattribute__"] = wrap_built_in_func(_core.shared_getattribute)
        dct["__setattr__"] = wrap_built_in_func(_core.shared_setattr)
        dct["__delattr__"] = wrap_built_in_func(_core.shared_delattr)

        # Invoke type's implementation of __new__
        newtype = type.__new__(tp, name, bases, dct)

        # Override the allocation methods of the new type
        _core.override_allocation(newtype)
        return newtype


# Simulates an attribute lookup on the given class by traversing its
# superclasses in method resolution order and returning the first class
# whose dictionary contains the attribute.  Returns None if not found.
def _type_lookup(tp, name):
    if hasattr(tp, "__mro__"):
        # Follow the MRO defined by the __mro__ attribute
        for t in tp.__mro__:
            if name in t.__dict__:
                return t
    else:
        # Use the classic left-to-right, depth-first rule
        if name in tp.__dict__:
            return tp
        for t in tp.__bases__:
            res = _type_lookup(t, name)
            if res:
                return res
    return None


def default_init(S, x):
    """default_init(S, x) -> A new instance of S that copies the state of x."""
    return S(x)


def generic_init(S, x):
    s = S()
    for name, value in x.__dict__.items():
        setattr(s, name, value)
    return s


def allow_sharing(tp, init=None, synch=MONITOR):
    """allow_sharing(tp, synch=None) -> None

    Allows sharing of objects of the given type.  This must be called prior
    to any fork() calls.  The init parameter is an initialization function
    f(S, x) that should return a new instance of the type S, initialized from
    the object x.  The synch parameter may be None for immutable types,
    indicating that no synchronization is needed on these objects, or MONITOR
    for objects that desire monitor access semantics.

    Instances of shareable types should adhere to the following rules:
    * A nonempty __slots__ is not allowed.
    * No custom __getattribute__(), __setattr__() or  __delattr__() is allowed.
    * Extension types need not make room for a dictionary in their object
      structure, but they should have a nonzero tp_dictoffset if they want to
      support attributes.
    * No references to other objects should be stored in the object structure
      itself, but rather in the object's dictionary using the generic
      PyObject_SetAttribute() and friends.
    * Extension types should not override the tp_alloc and tp_free slots.
    * References to ``self'' should not be stored in a way that makes them
      persist beyond the lifetime of the call.
    """

    global _has_forked

    if isinstance(tp, ClassType):
        raise TypeError, "allow_sharing: old-style classes are not supported"

    if not isinstance(tp, type):
        raise TypeError, "allow_sharing: 1st argument (tp) must be a type"

    # Check if we've forked
    if _has_forked:
        raise ValueError("allow_sharing: this call must be made "
              "prior to any fork calls")

    # Check if the type is already registered
    if tp in _core.type_map:
        raise ValueError("allow_sharing: %s objects may already be shared." 
                                    % tp.__name__)

    # The given type may not override attribute access
    # except to provide a __getattr__ hook.
    if _core.overrides_attributes(tp):
        raise ValueError("allow_sharing: %s overrides __getattribute__, "
           "__setattr__ or __delattr__" % tp.__name__)

    # The given type may not have a nonempty __slots__
    tpdir = dir(tp)
    if "__slots__" in tpdir and len(tp.__slots__):
        raise ValueError("allow_sharing: %s has a nonempty __slots__"
                             % tp.__name__)

    # If the given type contains no __dict__ descriptor, then the type's
    # instances has no dictionary, so neither should those of the shared
    # type.
    if not "__dict__" in tpdir:
        d = {'__slots__': []}
    else:
        d = {}

    # Make up a name for the shared type
    name = "Shared"+tp.__name__.capitalize()

    # The shared type is produced by inheriting from the shareable type
    # using the SharedType meta-type
    stp = SharedType(name, (tp,), d)
    # Assign the __synch__ attribute of the new type
    if not hasattr(stp, "__synch__"):
        stp.__synch__ = synch

    # We also need a proxy type that looks like the shared type
    ptp = _proxy.MakeProxyType(stp)

    # Register the types + the initializer with the _core module and we're done
    _core.register_type(tp, stp, ptp, init or default_init)


def init_types():
    # This function initializes the module with some basic shareable
    # types. The function is deleted after it is called.
    # Shared versions of the container types list, tuple and dictionary
    # are implemented from scratch, and are treated specially.

    # Allow the names SharedList, SharedTuple and SharedDict to persist,
    # so that users may subtype them if desired.
    global SharedList, SharedTuple, SharedDict
    global NoSynchSharedList, nslist

    def seq_add(self, other):
        return self[:]+other

    def seq_radd(self, other):
        return other+self[:]

    def seq_mul(self, count):
        return self[:]*count

    def seq_contains(self, item):
        for x in self:
            if x == item:
                return 1
        return 0

    class SharedList(_core.SharedListBase):
        """List type whose instances live in shared memory."""
        __metaclass__ = SharedType
        __slots__ = []

        __add__ = seq_add
        __radd__ = seq_radd
        __mul__ = seq_mul
        __rmul__ = seq_mul
        __contains__ = seq_contains

        def __iadd__(self, other):
            self.extend(other)
            return self

        def __imul__(self, count):
            lr = range(len(self))
            for i in range(count-1):
                for j in lr:
                    self.append(self[j])
            return self

        def __getslice__(self, i, j):
            indices = range(len(self))[i:j]
            return [self[i] for i in indices]

        def count(self, item):
            result = 0
            for x in self:
                if x == item:
                    result += 1
            return result

        def extend(self, seq):
            if seq is not self:
                # Default implementation, uses iterator
                for item in seq:
                    self.append(item)
            else:
                # Extension by self, cannot use iterator
                for i in range(len(self)):
                    self.append(self[i])

        def index(self, item):
            for i in range(len(self)):
                if self[i] == item:
                    return i
            raise ValueError, "list.index(x): x not in list"

        def reverse(self):
            l = len(self) // 2
            for i in range(l):
                j = -i-1
                # A traditional swap does less work than
                # a, b = b, a -- although it is less elegant...
                tmp = self[i]
                self[i] = self[j]
                self[j] = tmp

    class SharedTuple(_core.SharedTupleBase):
        """Tuple type whose instances live in shared memory."""
        __metaclass__ = SharedType
        __slots__ = []

        __add__ = seq_add
        __radd__ = seq_radd
        __mul__ = seq_mul
        __rmul__ = seq_mul
        __contains__ = seq_contains

        def __getslice__(self, i, j):
            indices = range(len(self))[i:j]
            return tuple([self[i] for i in indices])

        def __str__(self):
            # Tuples cannot be recursive, so this is easy
            # to implement using Python code
            items = map(repr, self)
            return "("+", ".join(items)+")"

        __repr__ = __str__

    class SharedDict(_core.SharedDictBase):
        """Dictionary type whose instances live in shared memory."""
        __metaclass__ = SharedType
        __slots__ = []

    SharedListProxy = _proxy.MakeProxyType(SharedList)
    SharedTupleProxy = _proxy.MakeProxyType(SharedTuple)
    SharedDictProxy = _proxy.MakeProxyType(SharedDict)

    # This maps list to SharedList and so on - this is special, since
    # these shared types are not subtypes of their shareable equivalents,
    # as is normally the case.
    _core.register_type(list, SharedList, SharedListProxy, default_init)
    _core.register_type(tuple, SharedTuple, SharedTupleProxy, default_init)
    _core.register_type(dict, SharedDict, SharedDictProxy, default_init)

    # Produce basic immutable shared types
    for t in int, float, long, complex, str, unicode, Lock:
        allow_sharing(t, synch=None)

    class NoSynchSharedList(SharedList):
        __slots__ = []
        __synch__ = None

    class nslist(list):
        __slots__ = []

    _core.register_type(nslist, NoSynchSharedList,
                        _proxy.MakeProxyType(NoSynchSharedList), 
                        default_init)

init_types()
del init_types


# Version of fork() that works with posh
def fork():
    """procshare's version of os.fork().

    Use this instead of os.fork() - it does the same.
    """
    global _has_forked

    pid = _os_fork()
    _has_forked = 1 # Both processes
    if not pid:
        # Child process
        _core.init_child()
    else:
        scheduler.sleep(0.5)
    return pid


