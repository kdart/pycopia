#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Basic SMI objects that are not BER base types. SMI base types are here.
Various support objects go here as well.
"""

import sys

from pycopia.aid import unsigned
from pycopia.table import GenericTable

from pycopia.SMI.SMICONSTANTS import SMI_ACCESS_READ_WRITE
from pycopia.SMI import Basetypes

class Index(list):
    def __init__(self, init=None, implied=False):
        super(Index, self).__init__(init or [])
        # only the last index node can be IMPLIED, so the IMPLIED flag
        # applies only to the last element (Index[-1]).
        self.implied = bool(implied)
    def __repr__(self):
        lv = super(Index, self).__repr__()
        return "%s.%s(%s, %r)" % (self.__class__.__module__, self.__class__.__name__, lv, self.implied)
    def _oid_(self):
        new = Basetypes.ObjectIdentifier()
        self[-1].implied = self.implied
        for obj in self:
            new.extend(oid(obj))
        return new

# SMI module uses this to create index object reference list
class IndexObjects(list):
    def __init__(self, init=None, implied=False):
        super(IndexObjects, self).__init__(init or [])
        self.implied = bool(implied)
    def __repr__(self):
        cl = self.__class__
        lv = super(IndexObjects, self).__repr__()
        return "%s.%s(%s, %r)" % (cl.__module__, cl.__name__, lv, self.implied)


### SMI Object bases ###

class _Generic(object):
    def __init__(self, *args, **kwargs):
        for attr, value in kwargs.items():
            self.__dict__[attr] = value
        self.args = args

    def __repr__(self):
        s = ["%s(" % self.__class__.__name__]
        s2 = map(repr, self.args)
        for key, val in self.__dict__.items():
            if key[0] != "_":
                if val:
                    s2.append("%s=%s" % (key, repr(val)))
        s.append(", ".join(s2))
        s.append(")")
        return "".join(s)

class Compliance(_Generic):
    pass

class Capability(_Generic):
    pass

class NodeObject(_Generic):
    status = None
    access = None
    OID = None
    name = None
    syntaxobject = None
    enumerations = None
    def __repr__(self):
        return "%s()" % (self.__class__.__name__)


class ModuleObject(_Generic):
    name = None
    path = None
    conformance = None
    language = None
    description = None
    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

# this class is overloaded a bit. It can perform operations on entire
# tables, but also represent a single row, or object instance. 
class RowObject(object):
    index = None
    rowstatus = None
    create = 0

    def __init__(self, indexoid=None):
        # set __dict__ directly because this class uses __setattr__
        self.__dict__["indexoid"] = indexoid
        self.__dict__["state"] = None
        self.__dict__["session"] = None
        self.__dict__["COLUMNS"] = {} # cache for bulk gets (getall method)

    def set_session(self, snmp_session):
        self.__dict__["session"] = snmp_session

    def set_indexoid(self, oid):
        self.__dict__["indexoid"] = oid

    def _make_index_oid(self, indexargs):
        assert len(indexargs) == len(self.index)
        indexoid = Basetypes.ObjectIdentifier()
        i = 0
        for idx in indexargs[:-1]:
            indexoid.extend(oid(self.index[i].syntaxobject(idx)))
            i += 1
        end = self.index[i].syntaxobject(indexargs[-1])
        end.implied = self.index.implied
        indexoid.extend(oid(end))
        return indexoid

    def __cmp__(self, other):
        return cmp(self.__class__.OID+self.indexoid, other.__class__.OID+other.indexoid)

    def _decode_index_oid(self, oid):
        indexinst = map(lambda o: o.syntaxobject(), self.index)
        map (lambda o, oid=oid: o.oid_decode(oid, 0), indexinst[:-1])
        indexinst[-1].oid_decode(oid, self.index.implied)
        return tuple(indexinst)

    def __getattr__(self, key):
        if self.session and self.indexoid:
            try:
                col = self.columns[key](indexoid=self.indexoid)
                return col.get(self.session)
            except:
                ex, err, tb = sys.exc_info()
                raise AttributeError, err, tb
        else: # return cached value 
            col = self.COLUMNS.get(key, None)
            if col:
                return col.value
            else:
                raise AttributeError, "no attribute or cached column named %s" % (key)

    def __setattr__(self, key, value):
        if self.session and self.indexoid:
            try:
                col = self.columns[key](indexoid=self.indexoid)
                col.set(value, self.session)
            except:
                ex, err, tb = sys.exc_info()
                raise AttributeError, err, tb
        else:
            if __debug__:
                print "warning: setting attribute in RowObject instance."
            self.__dict__[key] = value

    def __str__(self):
        s = ["%s (%s):" % (self.__class__.__name__, self.indexoid)]
        for colname, col in self.COLUMNS.items():
            s.append("%45s = %s" % (colname, col.value))
        return "\n".join(s)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.indexoid)

    def get_indexvalue(self):
        return self._decode_index_oid(self.indexoid[:])[0]
    def get_indexvalues(self):
        return self._decode_index_oid(self.indexoid[:])
    
    def add_column(self, colobj):
        self.COLUMNS[colobj.__class__.__name__] = colobj

    def get_attributes(self):
        return self.columns.keys()

    def get(self, session, indexoid=None):
        sess = session or self.session
        if indexoid:
            self.__dict__["indexoid"] = self._make_index_oid(indexoid)
        self.__dict__["COLUMNS"] = {} # clear cache with new dict
        vbl = Basetypes.VarBindList()
        VB = Basetypes.VarBind
        map(lambda o: vbl.append(VB(o.OID+self.indexoid)), self.columns.values())
        return_vbl = sess.get_varbindlist(vbl)
        # insert in COLUMNS
        for vb in return_vbl:
            vbo = vb.Object
            colobj = vbo(vb.value, vb.name[len(vbo.OID)+1:])
            self.add_column(colobj)
        return self

    # gets a subset of columns
    def get_values(self, *args):
        sess = self.session
        if sess and self.indexoid:
            rv = []
            vbl = Basetypes.VarBindList()
            cols = map(lambda n: self.columns.get(n), args)
            map(lambda o: vbl.append(Basetypes.VarBind(o.OID+self.indexoid)), cols)
            return_vbl = sess.get_varbindlist(vbl)
            return tuple(map(lambda vb: vb.value, return_vbl))

    def get_cache_value(self, name):
        return self.COLUMNS.get(name, None)

    def refresh(self, session=None):
        if (session or self.session) and self.indexoid:
            sess = session or self.session
            vbl = Basetypes.VarBindList()
            map(lambda co: vbl.append(co.varbind.clear()), self.COLUMNS.values())
            return_vbl = sess.get_varbindlist(vbl)
            for vb in return_vbl:
                self.COLUMNS[vb.Object.__name__].set_value(vb.value)

    def set(self, session=None, **attribs):
        sess = session or self.session
        vbl = Basetypes.VarBindList()
        for colname, value in attribs.items():
            col = self.columns[colname]
            value = col.syntaxobject(value)
            vbl.append(Basetypes.VarBind(col.OID+self.indexoid, value))
        sess.set(vbl)

    ### RowStatus methods
    def _rowstatus_action(self, session, value):
        if not session:
            raise ValueError, "no session specified"
        if self.rowstatus and self.indexoid:
            vbl = Basetypes.VarBindList()
            vbl.append(Basetypes.VarBind(self.rowstatus.OID+self.indexoid, self.rowstatus.syntaxobject(value)))
            session.set(vbl)

    def activate(self, session=None):
        sess = session or self.session
        self._rowstatus_action(sess, 1)

    def notInService(self, session=None):
        sess = session or self.session
        self._rowstatus_action(sess, 2)
    deactivate = notInService

    def destroy(self, session=None):
        sess = session or self.session
        self._rowstatus_action(sess, 6)
        self.__dict__["indexoid"] = None
        self.__dict__["COLUMNS"] = {}

    def get_status(self, session):
        if self.rowstatus and self.indexoid:
            vbl = session.get(self.OID+self.indexoid)
            #return self.rowstatus.syntaxobject(vbl[0].value)
            return vbl[0].value

    def _create_vbl(self, *indexargs, **attribs):
        if not self.create:
            raise ValueError, "Cannot create object of type "+self.__class__.__name__
        self.__dict__["indexoid"] = self._make_index_oid(indexargs)
        vbl = Basetypes.VarBindList()
        for key, value in attribs.items():
            colclass = self.columns[key]
            value = colclass.syntaxobject(value)
            vbl.append(Basetypes.VarBind(colclass.OID+self.indexoid, value))
        return vbl

    def createAndGo(self, session, *indexargs, **attribs):
        vbl = self._create_vbl(*indexargs, **attribs)
        vbl.append(Basetypes.VarBind(Basetypes.ObjectIdentifier(self.rowstatus.OID+self.indexoid), self.rowstatus.syntaxobject(4))) # create and go
        session.set(vbl)
        return self

    def createAndWait(self, session, *indexargs, **attribs):
        vbl = self._create_vbl(*indexargs, **attribs)
        vbl.append(Basetypes.VarBind(Basetypes.ObjectIdentifier(self.rowstatus.OID+self.indexoid), self.rowstatus.syntaxobject(4))) # create and go
        session.set(vbl)
        return self



class ScalarObject(object):
    status = None
    access = None
    OID = None
    syntaxobject = None
    enumerations = None
    def __init__(self, value=None):
        if value is not None:
            self.value = self.syntaxobject(value)
            if self.enumerations:
                self.value.enumerations = self.enumerations
        else:
            self.value = None
        self.session = None
        self.OID = self.__class__.OID+[0] # cache instance for small speed gain

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

    def varbind(self):
        return Basetypes.VarBind(self.OID, self.value, self.__class__)
    varbind = property(varbind)

    def set_session(self, snmp_session=None):
        self.session = snmp_session

    def set(self, val, session=None):
        sess = session or self.session
        if self.access != SMI_ACCESS_READ_WRITE:
            raise RuntimeError, "Scalar is not writeable"
        val = self.syntaxobject(val)
        try:
            sess.set_varbind(Basetypes.VarBind(self.OID, val))
        except:
            self.value = None
            raise 
        else:
            self.value = val

    def get(self, session=None, indexoid=None):
        sess = session or self.session
        rv = sess.get(self.OID)[0].value
        self.value = rv
        return rv

    def get_ratecounter(self, N=5):
        assert self.session is not None, "need session to update counters"
        return RateCounter(self, N=N)


class ColumnObject(object):
    status = None
    access = None
    OID = None
    syntaxobject = None
    enumerations = None
    def __init__(self, value=None, indexoid=None):
        if value is not None:
            self.set_value(value)
        else:
            self.value = None
        self.indexoid = indexoid
        if indexoid is not None:
            self.OID = self.__class__.OID+indexoid
        self.session = None
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)
    def __str__(self):
        return str(self.value)

    def set_value(self, value):
        self.value = self.syntaxobject(value)
        if self.enumerations:
            self.value.enumerations = self.enumerations

    def set_index(self, indexoid):
        self.indexoid = indexoid
        self.OID = self.__class__.OID+indexoid

    def varbind(self):
        return Basetypes.VarBind(self.OID, self.value, self.__class__)
    varbind = property(varbind)

    def set_session(self, snmp_session=None):
        self.session = snmp_session

    def get(self, session=None, indexoid=None):
        if indexoid:
            self.set_index(indexoid)
        sess = session or self.session
        if self.access >= 4: # XXX
            rv = sess.get(self.OID)[0].value
            self.value = rv
            return rv

    def set(self, value, session=None, indexoid=None):
        if indexoid:
            self.set_index(indexoid)
        sess = session or self.session
        vb = Basetypes.VarBind(self.OID, self.syntaxobject(value))
        return sess.set_varbind(vb)

    def get_ratecounter(self, N=5):
        assert self.session is not None, "need session to update counters"
        return RateCounter(self, N=N)


class MacroObject(object):
    def __repr__(self):
        return "%s()" % (self.__class__.__name__,)


class NotificationObject(object):
    def __repr__(self):
        return "%s()" % (self.__class__.__name__,)

class GroupObject(object):
    status = None
    OID = None
    name = None
    group = None
    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

#class Groups(list):
#   def __repr__(self):
#       cl = self.__class__
#       return "%s.%s(%s)" % (cl.__module__, cl.__name__, super(Groups, self).__repr__())


###############################


class RawTable(GenericTable):
    """
The SNMPTable class is a convenience class to make it easier to use MIB tables.
    """
    def __init__(self, rowobj, tabletitle=''):
        GenericTable.__init__(self)
        self.rowobj = rowobj
        self.prefixlen = len(rowobj.OID)
        self.tabletitle = tabletitle

    def _add_vb(self, vb):
        prefixlen = self.prefixlen
        col_name = str(vb.oid[prefixlen:prefixlen+1])
        row_name = str(vb.oid[prefixlen+1:])
        self.set(col_name, row_name, vb.value)

    def fetch(self, session):
        session.get_table(self.rowobj, self._add_vb)


class PlainTable(RawTable):
    def _add_vb(self, vb):
        prefixlen = len(self.OID)
        col = Basetypes.OID(vb.oid[prefixlen:prefixlen+1])
        row = Basetypes.OID(vb.oid[prefixlen+1:])
        self.add_by_name(col, row, vb.value)


class ObjectTable(dict):
    def __init__(self, rowclass):
        super(ObjectTable, self).__init__()
        self.rowclass = rowclass

    def fetch(self, session):
        session.get_table(self.rowclass, self._insert_varbind)

    def _insert_varbind(self, vb):
        rowindex = vb.name[len(self.rowclass.OID)+1:]
        indexstr = str(rowindex)
        colobj = vb.Object(vb.value, vb.name[len(vb.Object.OID):])
        rowobj = self.get(indexstr, None)
        if rowobj is None:
            rowobj = self[indexstr] = self.rowclass(rowindex)
        rowobj.add_column(colobj)
    
    def __iter__(self):
        return self.itervalues()

class RowIterator(object):
    def __init__(self, session, rowclass, startindex=None, count=0):
        self.session = session
        self.rowclass = rowclass
        self.columns = rowclass.columns.values()
        self.count = count
        self.current_row = None
        if startindex is None:
            prefixlen = len(self.rowclass.OID)
            vbl = self.session.getnext(self.rowclass.OID)
            self.current_index = vbl[0].name[prefixlen+1:]
        else:
            self.current_index = startindex

    def __str__(self):
        return "RowIterator(startindex=%s, count=%d)" % (self.current_index, self.count)

    def _insert_varbind(self, vb):
        prefixlen = len(self.rowclass.OID)
        colobj = vb.Object(vb.value)
        self.current_row.add_column(colobj)


class RunningRate(object):
    """Computes rates based on counter input. Also maintains exponentially
    weighted running average. Update the object by calling the update() method
    with a Counter object and a time interval. Extract the instantaneous rate
    with the 'rate' attribute, a running average with the RA attribute, and an
    exponentially weighted running average with the EWRA attribute."""
    def __init__(self, type=unsigned, N=5):
        self._C = float(type.ceiling)
        self._X = [None]
        self._lastcount = None
        self._lasttime = None
        self._ewra = None
        n = self._N = float(N)
        self._alpha = n/(n+1.0)
        self._alphap = 1.0/(n+1.0)

    def update(self, counter, timestamp):
        timestamp = float(timestamp)
        counter = float(counter)
        try:
            if counter >= self._lastcount:
                R = (counter - self._lastcount) / (timestamp - self._lasttime)
            else:
                R = ((self._C - (self._lastcount - counter))+1.0) / (timestamp - self._lasttime)
        except TypeError: # from initial None value - just starting out
            self._lastcount = counter
            self._lasttime = timestamp
            return
        self._lastcount = counter
        self._lasttime = timestamp
        self._X.insert(0, R)
        del self._X[-1]
        self._ewra = self._ExponentialWeightedRunningAverage(R)

    append = update

    def _get_rate(self):
        return self._X[0]
    rate = property(_get_rate)

    def _RunningAverage(self):
        try:
            return sum(self._X)/(self._N)
        except TypeError:
            return None
    RunningAverage = property(_RunningAverage)
    RA = RunningAverage

    def _ExponentialWeightedRunningAverage(self, R=None):
        try:
            pwr = pow
            a = self._alpha
            ap = self._alphap
            X = self._X
            s = ap*X[0]
            for i in range(1, len(X)):
                s += pwr(a, i)*ap*X[i]
            s += pwr(a, len(X))*self._ewra
            return s
        except TypeError: # from None initial value
            self._X = [R]*int(self._N)
            return R

    def _get_ewra(self):
        return self._ewra
    ExponentialWeightedRunningAverage = property(_get_ewra)
    EWRA = ExponentialWeightedRunningAverage 


class RateCounter(object):
    """Wrapper for a MIB object that has a Counter syntax. Used to update a rate."""
    def __init__(self, obj, N=5):
        self._obj = obj
        self._rate = RunningRate(obj.syntaxobject, N=N)
    def update(self, time):
        v = self._obj.get()
        self._rate.update(v, time)
    rate = property(lambda s: s._rate.rate)
    RA = property(lambda s: s._rate.RA)
    EWRA = property(lambda s: s._rate.EWRA)

# factory functions

def create(session, rowobj, *indexargs, **kwargs):
    newobj = rowobj()
    args = (session,) + indexargs
    return apply(newobj.createAndGo, args, kwargs)

def create_wait(session, rowobj, *indexargs, **kwargs):
    newobj = rowobj()
    args = (session,) + indexargs
    return apply(newobj.createAndWait, args, kwargs)

def get_table(session, rowclass):
    t = ObjectTable(rowclass)
    t.fetch(session)
    return t

def get_plaintable(session, rowclass):
    t = PlainTable(rowclass.OID, str(rowclass))
    t.fetch(session)
    return t

def get_object(session, rowclass, *indexargs):
    newobj = rowclass()
    newobj.get(session, indexargs)
    return newobj

def get_scalar(session, scalarclass):
    newobj = scalarclass()
    newobj.get(session)
    return newobj

