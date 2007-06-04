#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
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
This is a hand-edited libsmi shadow module. 

SMI module for python. This is merely a wrapper for the libsmi library (written
in C).  This is the primary Python programmer interface to the libsmi
wrapper.  This module replaces the SWIG generated shadow classes.
It also provides iterator objects for efficient node iteration. 

Keith Dart <kdart@kdart.com>
"""

import sys

import _libsmi

from pycopia.aid import Enum

SmiError = _libsmi.SmiError

# copy libsmi constants and enums into this modules namespace
for name, value in vars(_libsmi).items():
    if name.startswith("SMI_"):
        if type(value) is int:
            setattr(sys.modules[__name__], name, Enum(value,name))
        else:
            setattr(sys.modules[__name__], name, value)

class IndexObjects(list):
    def __init__(self, init=None, implied=False):
        super(IndexObjects, self).__init__(init or [])
        self.implied = bool(implied)
    def __repr__(self):
        cl = self.__class__
        lv = super(IndexObjects, self).__repr__()
        return "%s.%s(%s, %r)" % (cl.__module__, cl.__name__, lv, self.implied)

class OID(list):
    # the __module__ is omitted for a reason. This class mirrors that found in SMI.Basetypes
    def __str__(self):
        return ".".join(map(lambda x: '%lu' % x, self))
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(OID, self).__repr__())

# abstract base class of all Python SMI objects.
class SMIobject(object):
    def __init__(self, this):
        self.this = this

    def __repr__(self):
        return "<C %s instance at %s>" % (self.__class__.__name__, self.this)

    def __str__(self):
        s = [self.__class__.__name__+":"]
        for key in self.get_attributes():
            s.append("   %20s = %s" % (key, getattr(self, key)))
        return "\n".join(s)

    def get_attributes(self):
        for name, obj in vars(self.__class__).items():
            if type(obj) is property:
                yield name


###########################################################################
# basic object (structure) classes. These map to libsmi structures, but the
# prefixe 'Smi' has been removed.

class Module(SMIobject):
    name = property(_libsmi.SmiModule_name_get)
    path = property(_libsmi.SmiModule_path_get)
    organization = property(_libsmi.SmiModule_organization_get)
    contactinfo = property(_libsmi.SmiModule_contactinfo_get)
    description = property(_libsmi.SmiModule_description_get)
    reference = property(_libsmi.SmiModule_reference_get)
    language = property(_libsmi.SmiModule_language_get)
    conformance = property(_libsmi.SmiModule_conformance_get)
    def get_identityNode(self):
        return _libsmi.smiGetModuleIdentityNode(self)
    identityNode = property(get_identityNode)
    def get_imports(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstImport, _libsmi.smiGetNextImport, statusfilt)
    def is_imported(self, module, name):
        return _libsmi.smiIsImported(self, module, str(name))
    def get_type(self, name):
        return _libsmi.smiGetType(self, name)
    def get_types(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstType, _libsmi.smiGetNextType, statusfilt)
    def get_revisions(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstRevision, _libsmi.smiGetNextRevision, statusfilt)
    def get_macro(self, name):
        return _libsmi.smiGetMacro(self, name)
    def get_macros(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstMacro, _libsmi.smiGetNextMacro, statusfilt)
    def get_node(self, name):
        return _libsmi.smiGetNode(self, str(name))
    def get_nodes(self, kind=SMI_NODEKIND_ANY, statusfilt=None):
        next = _libsmi.smiGetFirstNode(self, kind)
        if not next:
            return
        yield next
        while 1:
            next = _libsmi.smiGetNextNode(next, kind)
            if not next:
                break
            if statusfilt:
                if next.status == statusfilt:
                    yield next
            else:
                yield next
    def get_scalars(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_SCALAR, statusfilt)
    def get_tables(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_TABLE, statusfilt)
    def get_rows(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_ROW, statusfilt)
    def get_columns(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_COLUMN, statusfilt)
    def get_notifications(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_NOTIFICATION, statusfilt)
    def get_groups(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_GROUP, statusfilt)
    def get_compliances(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_COMPLIANCE, statusfilt)
    def get_capabilities(self, statusfilt=None):
        return self.get_nodes(SMI_NODEKIND_CAPABILITIES, statusfilt)
_libsmi.SmiModule_swigregister(Module)

class Revision(SMIobject):
    date = property(_libsmi.SmiRevision_date_get)
    description = property(_libsmi.SmiRevision_description_get)
_libsmi.SmiRevision_swigregister(Revision)

class Import(SMIobject):
    module = property(_libsmi.SmiImport_module_get)
    name = property(_libsmi.SmiImport_name_get)
_libsmi.SmiImport_swigregister(Import)

class Macro(SMIobject):
    name = property(_libsmi.SmiMacro_name_get)
    decl = property(_libsmi.SmiMacro_decl_get)
    status = property(_libsmi.SmiMacro_status_get)
    description = property(_libsmi.SmiMacro_description_get)
    reference = property(_libsmi.SmiMacro_reference_get)
    def get_module(self):
        return _libsmi.smiGetMacroModule(self)
_libsmi.SmiMacro_swigregister(Macro)

class Type(SMIobject):
    # The following maps are used by the get_snmptype method.  Maps libsmi
    # basetype to SNMP Object names. These names must match the class names in
    # the SNMP.Basetypes module. SNMPv1 types are also included here.
    BASETYPELIST = ["Counter", "Counter32", "TimeTicks", "Opaque", "Unsigned32",
                            "Gauge32", "Gauge", "Counter64", "IpAddress"]
    BASETYPEMAP = {
        SMI_BASETYPE_INTEGER32: "Integer32",
        SMI_BASETYPE_ENUM: "Enumeration",
        SMI_BASETYPE_UNSIGNED32: "Unsigned32",
        SMI_BASETYPE_UNSIGNED64: "Counter64",
        SMI_BASETYPE_OCTETSTRING: "OctetString",
        SMI_BASETYPE_BITS: "Bits",
        SMI_BASETYPE_OBJECTIDENTIFIER: "ObjectIdentifier"
    }
    name = property(_libsmi.SmiType_name_get)
    basetype = property(_libsmi.SmiType_basetype_get)
    decl = property(_libsmi.SmiType_decl_get)
    format = property(_libsmi.SmiType_format_get)
    value = property(_libsmi.SmiType_value_get)
    units = property(_libsmi.SmiType_units_get)
    status = property(_libsmi.SmiType_status_get)
    description = property(_libsmi.SmiType_description_get)
    reference = property(_libsmi.SmiType_reference_get)
    def get_parent(self):
        return _libsmi.smiGetParentType(self)
    def get_line(self):
        return _libsmi.smiGetTypeLine(self)
    def get_ranges(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstRange, _libsmi.smiGetNextRange, statusfilt)
    def range_list(self, statusfilt=None):
        return Ranges(*tuple(self.get_ranges(statusfilt)))
    ranges = property(range_list)
    def get_NamedNumbers(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstNamedNumber, _libsmi.smiGetNextNamedNumber, statusfilt)
    get_named_numbers = get_NamedNumbers # alias, can't decide...
    def get_enumerations(self, statusfilt=None):
        rv = []
        for nn in self.get_NamedNumbers():
            enum = Enum(int(nn), nn.name)
            rv.append(enum)
        return rv
    enumerations = property(get_enumerations)
    def get_module(self):
        return _libsmi.smiGetTypeModule(self)
    def render(self, flag=SMI_RENDER_ALL):
        return _libsmi.smiRenderType(self, flag)
    def render_value(self, flag=SMI_RENDER_ALL): # ?
        return _libsmi.smiRenderValue(self.value, self, flag)
    def get_snmptype(self):
        if self.name in Type.BASETYPELIST:
            return self.name
        p = self.get_parent()
        while p:
            if p.name in Type.BASETYPELIST:
                return p.name
            p = p.get_parent()
        # libsmi provides no name if the type is a real base type
        return Type.BASETYPEMAP.get(self.basetype, None)
    snmptype = property(get_snmptype)


_libsmi.SmiType_swigregister(Type)

class Node(SMIobject):
    name = property(_libsmi.SmiNode_name_get)
    oidlen = property(_libsmi.SmiNode_oidlen_get)
    oid = property(_libsmi.SmiNode_oid_get)  # 'raw' oid pointer, don't use
    decl = property(_libsmi.SmiNode_decl_get)
    access = property(_libsmi.SmiNode_access_get)
    status = property(_libsmi.SmiNode_status_get)
    format = property(_libsmi.SmiNode_format_get)
    value = property(_libsmi.SmiNode_value_get)
    units = property(_libsmi.SmiNode_units_get)
    description = property(_libsmi.SmiNode_description_get)
    reference = property(_libsmi.SmiNode_reference_get)
    indexkind = property(_libsmi.SmiNode_indexkind_get)
    implied = property(_libsmi.SmiNode_implied_get)
    create = property(_libsmi.SmiNode_create_get)
    nodekind = property(_libsmi.SmiNode_nodekind_get)
    def get_OID(self):
        return OID(_libsmi.List_FromSmiSubid(
            _libsmi.SmiNode_oid_get(self), _libsmi.SmiNode_oidlen_get(self)))
    OID = property(get_OID) # use this converted OID value
    def get_parent(self):
        return _libsmi.smiGetParentNode(self)
    def get_related(self): # gets AUGMENTS node
        return _libsmi.smiGetRelatedNode(self)
    def get_children(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstChildNode, _libsmi.smiGetNextChildNode, statusfilt)
    def get_module(self):
        return _libsmi.smiGetNodeModule(self)
    def get_type(self):
        return _libsmi.smiGetNodeType(self)
    syntax = property(get_type)
    def get_line(self):
        return _libsmi.smiGetNodeLine(self)
    def get_elements(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstElement, _libsmi.smiGetNextElement, statusfilt)
    def get_uniqueness_elements(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstUniquenessElement, _libsmi.smiGetNextElement, statusfilt)
    def render(self, flag=SMI_RENDER_ALL):
        return _libsmi.smiRenderNode(self, flag)
    # for compliance nodes - Node is a bit overloaded
    def get_refinements(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstRefinement, _libsmi.smiGetNextRefinement, statusfilt)
    def get_options(self, statusfilt=None):
        return _list_generator(self, _libsmi.smiGetFirstOption, _libsmi.smiGetNextOption, statusfilt)
    def get_index(self):
        if self.nodekind == SMI_NODEKIND_ROW:
            if self.indexkind == SMI_INDEX_INDEX:
                indexes = IndexObjects(implied=self.implied)
                for el in self.get_elements():
                    n = el.get_node()
                    indexes.append(n)
                return indexes
            elif self.indexkind == SMI_INDEX_AUGMENT:
                augnode = self.get_related()
                return augnode.get_index()
            else:
                return None
        else:
            return None
    index = property(get_index)
    def get_rowstatus(self):
        if self.nodekind == SMI_NODEKIND_ROW:
            for col in self.get_children():
                if col.syntax.name == "RowStatus":
                    return col
        else:
            return None
    rowstatus = property(get_rowstatus)
_libsmi.SmiNode_swigregister(Node)

class Element(SMIobject):
    def get_node(self):
        return _libsmi.smiGetElementNode(self)
    get_parent = get_node
_libsmi.SmiElement_swigregister(Element)

class Option(SMIobject):
    description = property(_libsmi.SmiOption_description_get)
    def get_node(self):
        return _libsmi.smiGetOptionNode(self)
    get_parent = get_node
_libsmi.SmiOption_swigregister(Option)

class Refinement(SMIobject):
    access = property(_libsmi.SmiRefinement_access_get)
    syntax = property(_libsmi.smiGetRefinementType)
    description = property(_libsmi.SmiRefinement_description_get)
    write_type = property(_libsmi.smiGetRefinementWriteType)
    def get_node(self):
        return _libsmi.smiGetRefinementNode(self)
    get_parent = get_node
    def get_type(self):
        return _libsmi.smiGetRefinementType(self)
    def get_write_type(self):
        return _libsmi.smiGetRefinementWriteType(self)
_libsmi.SmiRefinement_swigregister(Refinement)

# this is a C union. only one will be valid, determined by the Value.basetype
class Value_value(SMIobject):
    unsigned64 = property(_libsmi.SmiValue_value_unsigned64_get)
    integer64 = property(_libsmi.SmiValue_value_integer64_get)
    unsigned32 = property(_libsmi.SmiValue_value_unsigned32_get)
    integer32 = property(_libsmi.SmiValue_value_integer32_get)
    float32 = property(_libsmi.SmiValue_value_float32_get)
    float64 = property(_libsmi.SmiValue_value_float64_get)
    oid = property(_libsmi.SmiValue_value_oid_get)
    ptr = property(_libsmi.SmiValue_value_ptr_get) # OctetString, Bits
_libsmi.SmiValue_value_swigregister(Value_value)

class Value(SMIobject):
    # the value of this mapping gets called with a Value_value object
    _BASIC = {
        SMI_BASETYPE_UNKNOWN: lambda vv: None,
        SMI_BASETYPE_INTEGER32: _libsmi.SmiValue_value_integer32_get,  #  also SMIv1/v2 INTEGER
        SMI_BASETYPE_UNSIGNED32: _libsmi.SmiValue_value_unsigned32_get,
        SMI_BASETYPE_INTEGER64: _libsmi.SmiValue_value_integer64_get,  #  SMIng and SPPI
        SMI_BASETYPE_UNSIGNED64: _libsmi.SmiValue_value_unsigned64_get, # SMIv2, SMIng and SPPI
        SMI_BASETYPE_FLOAT32: _libsmi.SmiValue_value_float32_get,    # only SMIng
        SMI_BASETYPE_FLOAT64: _libsmi.SmiValue_value_float64_get,    # only SMIng
        SMI_BASETYPE_FLOAT128: lambda vv: NotImplemented,   # only SMIng
        SMI_BASETYPE_ENUM: _libsmi.SmiValue_value_integer32_get, # ?
    }
    # these get called with a Value_value and a length
    _SPECIAL = {
        SMI_BASETYPE_OBJECTIDENTIFIER: lambda vv, l: OID(List_FromSmiSubid(_libsmi.SmiValue_value_oid_get(vv), l)),
        SMI_BASETYPE_OCTETSTRING: lambda vv, l: _libsmi.SmiValue_value_ptr_get(vv), # XXX
        SMI_BASETYPE_BITS: lambda vv, l: _libsmi.SmiValue_value_ptr_get(vv), # SMIv2, SMIng and SPPI
    }
    basetype = property(_libsmi.SmiValue_basetype_get)
    len = property(_libsmi.SmiValue_len_get) # OID, OctetString, Bits
    def __str__(self):
        return "Value(basetype=%r, len=%r, value=%r)" % \
                (self.basetype, self.len, self.get_value())
    def get_value(self):
        basetype = _libsmi.SmiValue_basetype_get(self)
        rawval = _libsmi.SmiValue_value_get(self)
        try:
            return Value._BASIC[basetype](rawval)
        except KeyError:
            return Value._SPECIAL[basetype](rawval, _libsmi.SmiValue_len_get(self))
    value = property(get_value)
    def render(self, typeobj, flag=SMI_RENDER_ALL):
        return _libsmi.smiRenderValue(self, typeobj, flag)
_libsmi.SmiValue_swigregister(Value)

class NamedNumber(SMIobject):
    name = property(_libsmi.SmiNamedNumber_name_get)
    value = property(_libsmi.SmiNamedNumber_value_get)
    def __str__(self):
        return "%s(%d)" % (self.name, self.value.value)
    def __cmp__(self, other):
        return cmp(self.value.value, other.value.value)
    def __int__(self):
        return self.value.value
    def __long__(self):
        return long(self.value.value)
_libsmi.SmiNamedNumber_swigregister(NamedNumber)

# The SNMP.Basetyes.Range class mirrors this one.
class Range(SMIobject):
    minValue = property(_libsmi.SmiRange_minValue_get)
    maxValue = property(_libsmi.SmiRange_maxValue_get)
    def __str__(self):
        return "(%d..%d)" % (_libsmi.SmiRange_minValue_get(self).value, _libsmi.SmiRange_maxValue_get(self).value)
    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, _libsmi.SmiRange_minValue_get(self).value, _libsmi.SmiRange_maxValue_get(self).value)
_libsmi.SmiRange_swigregister(Range)

class Ranges(list):
    def __init__(self, *args):
        super(Ranges, self).__init__(list(args))
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join(map(repr, self)))


# The Flags class is used as a namespace to encapsulate libsmi flag
# manipulation. You don't need to instantiate it. Just use "Flags.get_flags()",
# etc.
class Flags(object):
    stringmap = {
        SMI_FLAG_ERRORS: 'SMI_FLAG_ERRORS',
        SMI_FLAG_NODESCR: 'SMI_FLAG_NODESCR',
        SMI_FLAG_RECURSIVE: 'SMI_FLAG_RECURSIVE',
        SMI_FLAG_STATS: 'SMI_FLAG_STATS',
        SMI_FLAG_VIEWALL: 'SMI_FLAG_VIEWALL',
    }

    def set_flags(*flags):
        newflag = 0
        for flag in flags:
            newflag |= (flag & SMI_FLAG_MASK)
        _libsmi.smiSetFlags(newflag)
    set_flags = staticmethod(set_flags)
    
    def get_flags():
        flags = _libsmi.smiGetFlags()
        return flags
    get_flags = staticmethod(get_flags)

    def set(flag):
        flags = _libsmi.smiGetFlags()
        flags |= (flag & SMI_FLAG_MASK)
        _libsmi.smiSetFlags(flags)
    set = staticmethod(set)

    def clear(flag):
        flags = _libsmi.smiGetFlags()
        flags &= ~(flag & SMI_FLAG_MASK)
        _libsmi.smiSetFlags(flags)
    clear = staticmethod(clear)

    def test(flag):
        flags = _libsmi.smiGetFlags()
        return flags & flag & SMI_FLAG_MASK
    test = staticmethod(test)

    def toString(cls):
        s = []
        flags = _libsmi.smiGetFlags()
        for flag, name in cls.stringmap.items():
            if flags & flag:
                s.append(name)
        if s:
            return ", ".join(s)
        else:
            return ""
    toString = classmethod(toString)

    def __str__(self): # XXX does this work?
        return self.toString()
    __str__ = classmethod(__str__)

    def _change(cls, _flag, onoff):
        if onoff:
            cls.set(_flag)
        else:
            cls.clear(_flag)
    _change = classmethod(_change)

    def show_errors(cls, onoff=1):
        """If SMI_FLAG_ERRORS is not set, no error messages are printed at all
        to keep the SMI library totally quiet, which might be mandatory for
        some applications."""
        cls._change(SMI_FLAG_ERRORS, onoff)
    show_errors = classmethod(show_errors)

    def no_descriptions(cls, onoff=1):
        """If SMI_FLAG_NODESCR is set, no description and references strings
        are stored in memory. This may save a huge amount of memory in case of
        applications that do not need this information."""
        cls._change(SMI_FLAG_NODESCR, onoff)
    no_descriptions = classmethod(no_descriptions)

    def recursive(cls, onoff=1):
        """If SMI_FLAG_RECURSIVE is set, the library also complains about
        errors in modules that are read due to import statements."""
        cls._change(SMI_FLAG_RECURSIVE, onoff)
    recursive = classmethod(recursive)

    def statistics(cls, onoff=1):
        """If SMI_FLAG_STATS is set, the library prints some module
        statistics."""
        cls._change(SMI_FLAG_STATS, onoff)
    statistics = classmethod(statistics)

    def view_all(cls, onoff=1):
        """If SMI_FLAG_VIEWALL is set, ...""" # XXX
        cls._change(SMI_FLAG_VIEWALL, onoff)
    view_all = classmethod(view_all)


# generator helper - factored out for libsmi iterators
def _list_generator(inst, firstgetter, nextgetter, statusfilt=None):
    if inst:
        next = firstgetter(inst)
    else:
        next = firstgetter()
    if not next:
        return
    yield next
    while 1:
        next = nextgetter(next)
        if not next:
            break
        if statusfilt:
            if next.status == statusfilt:
                yield next
        else:
            yield next


############################################################
### factory functions below
############################################################

# straight function mappings
#
# The is_loaded(module) function returns a positive value if the module named
# module is already loaded, or zero  otherwise.
is_loaded = _libsmi.smiIsLoaded
# set an alternate error handler.
set_error_handler = _libsmi.SetErrorHandler
# get or set the MIB search path.
get_path = _libsmi.smiGetPath
set_path = _libsmi.smiSetPath

def get_node_by_OID(oid):
    """Retrieves a Node that matches the longest prefix of the node that is
       specified. If no such node is not  found, return None.  """
    if type(oid) is str:
        oid = map(int, oid.split("."))
    assert isinstance(oid, list)
    return _libsmi.GetNodeByOID(oid)

def get_node(nodespec):
    """The get_node() function retrieves a Node that represents a
    node of any kind. Nodespec may be  either  a fully  qualified descriptor, a
    simple node name, or a numerical OID.  Nodes are also found, if node
    contains an instance identifier suffix.  """
    return _libsmi.smiGetNode(None, str(nodespec))

def set_error_level(level=0):
    """Sets the pedantic level (0-9) of the SMI parsers of the SMI
    library, """
    assert level >= 0 and level <= 9, "set_error_level: level must be 0..9"
    _libsmi.smiSetErrorLevel(level)

def set_severity(pattern, severity):
    """The set_severity() function allows you to set the severity of  all
error that have name prefixed by pattern to the value severity."""
    _libsmi.smiSetSeverity(pattern, severity)

def get_module(modulename):
    return _libsmi.smiGetModule(modulename)

def load_module(modulename):
    return _libsmi.smiLoadModule(modulename)

def load_modules(*args):
    """
load_modules(modname|modnamelist, ...)
Takes multiple string arguments, or lists of strings, which should be
module names, and loads them.

    """
    for arg in args:
        if type(arg) is type([]):
            for argl in arg:
                _libsmi.smiLoadModule(argl)
        else:
            _libsmi.smiLoadModule(arg)

def get_modules(statusfilt=None):
    """returns generator that iterates over all loaded modules."""
    return _list_generator(None, _libsmi.smiGetFirstModule, _libsmi.smiGetNextModule, statusfilt)

def default_error_handler(path, line, severity, msg, tag):
    print >>sys.stderr, "libsmi error: %s:%d" % (path, line)
    print >>sys.stderr, " * severity: %d\n %s %s" % (severity, msg, tag)

def init(key="python", error_handler=default_error_handler):
    _libsmi.Init(key)
    set_error_handler(error_handler)
    load_modules("SNMPv2-SMI", "SNMPv2-TC", "SNMPv2-CONF")
    # filter out pibs from path
    set_path(":".join(filter(lambda pe: pe.find("pib") == -1, get_path().split(":"))))

#   NB if you call this while you still hold references to objects you will get
#   segfaults when you access the ojects.
def clear():
    _libsmi.smiExit()


####################################################
### MAIN initialisation

init()

if __name__ == "__main__":
    Flags.view_all()
    #m = get_module("TCP-MIB")
    m = get_module("SNMPv2-MIB")
    #m = get_module("TUBS-IBR-TEST-MIB")
    print m.name
    print "Has scalars:"
    for scalar in m.get_scalars():
        print scalar.name, scalar.OID, scalar.value
    print
    print "---"
    print scalar
    print "---"
    print get_node_by_OID(scalar.OID)
    uptime = m.get_node("sysUpTime")
    sysname = m.get_node("sysName")
