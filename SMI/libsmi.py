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

from pycopia import _libsmi

def _swig_setattr(self,class_type,name,value):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    self.__dict__[name] = value

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


SMI_LIBRARY_VERSION = _libsmi.SMI_LIBRARY_VERSION
SMI_VERSION_MAJOR = _libsmi.SMI_VERSION_MAJOR
SMI_VERSION_MINOR = _libsmi.SMI_VERSION_MINOR
SMI_VERSION_PATCHLEVEL = _libsmi.SMI_VERSION_PATCHLEVEL
SMI_VERSION_STRING = _libsmi.SMI_VERSION_STRING
SMI_FLAG_NODESCR = _libsmi.SMI_FLAG_NODESCR
SMI_FLAG_VIEWALL = _libsmi.SMI_FLAG_VIEWALL
SMI_FLAG_ERRORS = _libsmi.SMI_FLAG_ERRORS
SMI_FLAG_RECURSIVE = _libsmi.SMI_FLAG_RECURSIVE
SMI_FLAG_STATS = _libsmi.SMI_FLAG_STATS
SMI_FLAG_MASK = _libsmi.SMI_FLAG_MASK
SMI_RENDER_NUMERIC = _libsmi.SMI_RENDER_NUMERIC
SMI_RENDER_NAME = _libsmi.SMI_RENDER_NAME
SMI_RENDER_QUALIFIED = _libsmi.SMI_RENDER_QUALIFIED
SMI_RENDER_FORMAT = _libsmi.SMI_RENDER_FORMAT
SMI_RENDER_PRINTABLE = _libsmi.SMI_RENDER_PRINTABLE
SMI_RENDER_UNKNOWN = _libsmi.SMI_RENDER_UNKNOWN
SMI_RENDER_ALL = _libsmi.SMI_RENDER_ALL
SMI_UNKNOWN_LABEL = _libsmi.SMI_UNKNOWN_LABEL
SMI_LANGUAGE_UNKNOWN = _libsmi.SMI_LANGUAGE_UNKNOWN
SMI_LANGUAGE_SMIV1 = _libsmi.SMI_LANGUAGE_SMIV1
SMI_LANGUAGE_SMIV2 = _libsmi.SMI_LANGUAGE_SMIV2
SMI_LANGUAGE_SMING = _libsmi.SMI_LANGUAGE_SMING
SMI_LANGUAGE_SPPI = _libsmi.SMI_LANGUAGE_SPPI
SMI_BASETYPE_UNKNOWN = _libsmi.SMI_BASETYPE_UNKNOWN
SMI_BASETYPE_INTEGER32 = _libsmi.SMI_BASETYPE_INTEGER32
SMI_BASETYPE_OCTETSTRING = _libsmi.SMI_BASETYPE_OCTETSTRING
SMI_BASETYPE_OBJECTIDENTIFIER = _libsmi.SMI_BASETYPE_OBJECTIDENTIFIER
SMI_BASETYPE_UNSIGNED32 = _libsmi.SMI_BASETYPE_UNSIGNED32
SMI_BASETYPE_INTEGER64 = _libsmi.SMI_BASETYPE_INTEGER64
SMI_BASETYPE_UNSIGNED64 = _libsmi.SMI_BASETYPE_UNSIGNED64
SMI_BASETYPE_FLOAT32 = _libsmi.SMI_BASETYPE_FLOAT32
SMI_BASETYPE_FLOAT64 = _libsmi.SMI_BASETYPE_FLOAT64
SMI_BASETYPE_FLOAT128 = _libsmi.SMI_BASETYPE_FLOAT128
SMI_BASETYPE_ENUM = _libsmi.SMI_BASETYPE_ENUM
SMI_BASETYPE_BITS = _libsmi.SMI_BASETYPE_BITS
SMI_STATUS_UNKNOWN = _libsmi.SMI_STATUS_UNKNOWN
SMI_STATUS_CURRENT = _libsmi.SMI_STATUS_CURRENT
SMI_STATUS_DEPRECATED = _libsmi.SMI_STATUS_DEPRECATED
SMI_STATUS_MANDATORY = _libsmi.SMI_STATUS_MANDATORY
SMI_STATUS_OPTIONAL = _libsmi.SMI_STATUS_OPTIONAL
SMI_STATUS_OBSOLETE = _libsmi.SMI_STATUS_OBSOLETE
SMI_ACCESS_UNKNOWN = _libsmi.SMI_ACCESS_UNKNOWN
SMI_ACCESS_NOT_IMPLEMENTED = _libsmi.SMI_ACCESS_NOT_IMPLEMENTED
SMI_ACCESS_NOT_ACCESSIBLE = _libsmi.SMI_ACCESS_NOT_ACCESSIBLE
SMI_ACCESS_NOTIFY = _libsmi.SMI_ACCESS_NOTIFY
SMI_ACCESS_READ_ONLY = _libsmi.SMI_ACCESS_READ_ONLY
SMI_ACCESS_READ_WRITE = _libsmi.SMI_ACCESS_READ_WRITE
SMI_ACCESS_INSTALL = _libsmi.SMI_ACCESS_INSTALL
SMI_ACCESS_INSTALL_NOTIFY = _libsmi.SMI_ACCESS_INSTALL_NOTIFY
SMI_ACCESS_REPORT_ONLY = _libsmi.SMI_ACCESS_REPORT_ONLY
SMI_NODEKIND_UNKNOWN = _libsmi.SMI_NODEKIND_UNKNOWN
SMI_NODEKIND_NODE = _libsmi.SMI_NODEKIND_NODE
SMI_NODEKIND_SCALAR = _libsmi.SMI_NODEKIND_SCALAR
SMI_NODEKIND_TABLE = _libsmi.SMI_NODEKIND_TABLE
SMI_NODEKIND_ROW = _libsmi.SMI_NODEKIND_ROW
SMI_NODEKIND_COLUMN = _libsmi.SMI_NODEKIND_COLUMN
SMI_NODEKIND_NOTIFICATION = _libsmi.SMI_NODEKIND_NOTIFICATION
SMI_NODEKIND_GROUP = _libsmi.SMI_NODEKIND_GROUP
SMI_NODEKIND_COMPLIANCE = _libsmi.SMI_NODEKIND_COMPLIANCE
SMI_NODEKIND_CAPABILITIES = _libsmi.SMI_NODEKIND_CAPABILITIES
SMI_NODEKIND_ANY = _libsmi.SMI_NODEKIND_ANY
SMI_DECL_UNKNOWN = _libsmi.SMI_DECL_UNKNOWN
SMI_DECL_IMPLICIT_TYPE = _libsmi.SMI_DECL_IMPLICIT_TYPE
SMI_DECL_TYPEASSIGNMENT = _libsmi.SMI_DECL_TYPEASSIGNMENT
SMI_DECL_IMPL_SEQUENCEOF = _libsmi.SMI_DECL_IMPL_SEQUENCEOF
SMI_DECL_VALUEASSIGNMENT = _libsmi.SMI_DECL_VALUEASSIGNMENT
SMI_DECL_OBJECTTYPE = _libsmi.SMI_DECL_OBJECTTYPE
SMI_DECL_OBJECTIDENTITY = _libsmi.SMI_DECL_OBJECTIDENTITY
SMI_DECL_MODULEIDENTITY = _libsmi.SMI_DECL_MODULEIDENTITY
SMI_DECL_NOTIFICATIONTYPE = _libsmi.SMI_DECL_NOTIFICATIONTYPE
SMI_DECL_TRAPTYPE = _libsmi.SMI_DECL_TRAPTYPE
SMI_DECL_OBJECTGROUP = _libsmi.SMI_DECL_OBJECTGROUP
SMI_DECL_NOTIFICATIONGROUP = _libsmi.SMI_DECL_NOTIFICATIONGROUP
SMI_DECL_MODULECOMPLIANCE = _libsmi.SMI_DECL_MODULECOMPLIANCE
SMI_DECL_AGENTCAPABILITIES = _libsmi.SMI_DECL_AGENTCAPABILITIES
SMI_DECL_TEXTUALCONVENTION = _libsmi.SMI_DECL_TEXTUALCONVENTION
SMI_DECL_MACRO = _libsmi.SMI_DECL_MACRO
SMI_DECL_COMPL_GROUP = _libsmi.SMI_DECL_COMPL_GROUP
SMI_DECL_COMPL_OBJECT = _libsmi.SMI_DECL_COMPL_OBJECT
SMI_DECL_MODULE = _libsmi.SMI_DECL_MODULE
SMI_DECL_EXTENSION = _libsmi.SMI_DECL_EXTENSION
SMI_DECL_TYPEDEF = _libsmi.SMI_DECL_TYPEDEF
SMI_DECL_NODE = _libsmi.SMI_DECL_NODE
SMI_DECL_SCALAR = _libsmi.SMI_DECL_SCALAR
SMI_DECL_TABLE = _libsmi.SMI_DECL_TABLE
SMI_DECL_ROW = _libsmi.SMI_DECL_ROW
SMI_DECL_COLUMN = _libsmi.SMI_DECL_COLUMN
SMI_DECL_NOTIFICATION = _libsmi.SMI_DECL_NOTIFICATION
SMI_DECL_GROUP = _libsmi.SMI_DECL_GROUP
SMI_DECL_COMPLIANCE = _libsmi.SMI_DECL_COMPLIANCE
SMI_INDEX_UNKNOWN = _libsmi.SMI_INDEX_UNKNOWN
SMI_INDEX_INDEX = _libsmi.SMI_INDEX_INDEX
SMI_INDEX_AUGMENT = _libsmi.SMI_INDEX_AUGMENT
SMI_INDEX_REORDER = _libsmi.SMI_INDEX_REORDER
SMI_INDEX_SPARSE = _libsmi.SMI_INDEX_SPARSE
SMI_INDEX_EXPAND = _libsmi.SMI_INDEX_EXPAND
class SmiValue(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiValue, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiValue, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiValue instance at %s>" % (self.this,)
    __swig_getmethods__["basetype"] = _libsmi.SmiValue_basetype_get
    if _newclass:basetype = property(_libsmi.SmiValue_basetype_get)
    __swig_getmethods__["len"] = _libsmi.SmiValue_len_get
    if _newclass:len = property(_libsmi.SmiValue_len_get)
    __swig_getmethods__["value"] = _libsmi.SmiValue_value_get
    if _newclass:value = property(_libsmi.SmiValue_value_get)

class SmiValuePtr(SmiValue):
    def __init__(self, this):
        _swig_setattr(self, SmiValue, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiValue, 'thisown', 0)
        _swig_setattr(self, SmiValue,self.__class__,SmiValue)
_libsmi.SmiValue_swigregister(SmiValuePtr)
Init = _libsmi.Init

SetErrorHandler = _libsmi.SetErrorHandler

List_FromSmiSubid = _libsmi.List_FromSmiSubid

GetNodeByOID = _libsmi.GetNodeByOID


class SmiValue_value(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiValue_value, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiValue_value, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiValue_value instance at %s>" % (self.this,)
    __swig_getmethods__["unsigned64"] = _libsmi.SmiValue_value_unsigned64_get
    if _newclass:unsigned64 = property(_libsmi.SmiValue_value_unsigned64_get)
    __swig_getmethods__["integer64"] = _libsmi.SmiValue_value_integer64_get
    if _newclass:integer64 = property(_libsmi.SmiValue_value_integer64_get)
    __swig_getmethods__["unsigned32"] = _libsmi.SmiValue_value_unsigned32_get
    if _newclass:unsigned32 = property(_libsmi.SmiValue_value_unsigned32_get)
    __swig_getmethods__["integer32"] = _libsmi.SmiValue_value_integer32_get
    if _newclass:integer32 = property(_libsmi.SmiValue_value_integer32_get)
    __swig_getmethods__["float32"] = _libsmi.SmiValue_value_float32_get
    if _newclass:float32 = property(_libsmi.SmiValue_value_float32_get)
    __swig_getmethods__["float64"] = _libsmi.SmiValue_value_float64_get
    if _newclass:float64 = property(_libsmi.SmiValue_value_float64_get)
    __swig_getmethods__["oid"] = _libsmi.SmiValue_value_oid_get
    if _newclass:oid = property(_libsmi.SmiValue_value_oid_get)
    __swig_getmethods__["ptr"] = _libsmi.SmiValue_value_ptr_get
    if _newclass:ptr = property(_libsmi.SmiValue_value_ptr_get)

class SmiValue_valuePtr(SmiValue_value):
    def __init__(self, this):
        _swig_setattr(self, SmiValue_value, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiValue_value, 'thisown', 0)
        _swig_setattr(self, SmiValue_value,self.__class__,SmiValue_value)
_libsmi.SmiValue_value_swigregister(SmiValue_valuePtr)

class SmiNamedNumber(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiNamedNumber, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiNamedNumber, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiNamedNumber instance at %s>" % (self.this,)
    __swig_getmethods__["name"] = _libsmi.SmiNamedNumber_name_get
    if _newclass:name = property(_libsmi.SmiNamedNumber_name_get)
    __swig_getmethods__["value"] = _libsmi.SmiNamedNumber_value_get
    if _newclass:value = property(_libsmi.SmiNamedNumber_value_get)

class SmiNamedNumberPtr(SmiNamedNumber):
    def __init__(self, this):
        _swig_setattr(self, SmiNamedNumber, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiNamedNumber, 'thisown', 0)
        _swig_setattr(self, SmiNamedNumber,self.__class__,SmiNamedNumber)
_libsmi.SmiNamedNumber_swigregister(SmiNamedNumberPtr)

class SmiRange(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiRange, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiRange, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiRange instance at %s>" % (self.this,)
    __swig_getmethods__["minValue"] = _libsmi.SmiRange_minValue_get
    if _newclass:minValue = property(_libsmi.SmiRange_minValue_get)
    __swig_getmethods__["maxValue"] = _libsmi.SmiRange_maxValue_get
    if _newclass:maxValue = property(_libsmi.SmiRange_maxValue_get)

class SmiRangePtr(SmiRange):
    def __init__(self, this):
        _swig_setattr(self, SmiRange, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiRange, 'thisown', 0)
        _swig_setattr(self, SmiRange,self.__class__,SmiRange)
_libsmi.SmiRange_swigregister(SmiRangePtr)

class SmiModule(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiModule, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiModule, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiModule instance at %s>" % (self.this,)
    __swig_getmethods__["name"] = _libsmi.SmiModule_name_get
    if _newclass:name = property(_libsmi.SmiModule_name_get)
    __swig_getmethods__["path"] = _libsmi.SmiModule_path_get
    if _newclass:path = property(_libsmi.SmiModule_path_get)
    __swig_getmethods__["organization"] = _libsmi.SmiModule_organization_get
    if _newclass:organization = property(_libsmi.SmiModule_organization_get)
    __swig_getmethods__["contactinfo"] = _libsmi.SmiModule_contactinfo_get
    if _newclass:contactinfo = property(_libsmi.SmiModule_contactinfo_get)
    __swig_getmethods__["description"] = _libsmi.SmiModule_description_get
    if _newclass:description = property(_libsmi.SmiModule_description_get)
    __swig_getmethods__["reference"] = _libsmi.SmiModule_reference_get
    if _newclass:reference = property(_libsmi.SmiModule_reference_get)
    __swig_getmethods__["language"] = _libsmi.SmiModule_language_get
    if _newclass:language = property(_libsmi.SmiModule_language_get)
    __swig_getmethods__["conformance"] = _libsmi.SmiModule_conformance_get
    if _newclass:conformance = property(_libsmi.SmiModule_conformance_get)

class SmiModulePtr(SmiModule):
    def __init__(self, this):
        _swig_setattr(self, SmiModule, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiModule, 'thisown', 0)
        _swig_setattr(self, SmiModule,self.__class__,SmiModule)
_libsmi.SmiModule_swigregister(SmiModulePtr)

class SmiRevision(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiRevision, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiRevision, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiRevision instance at %s>" % (self.this,)
    __swig_getmethods__["date"] = _libsmi.SmiRevision_date_get
    if _newclass:date = property(_libsmi.SmiRevision_date_get)
    __swig_getmethods__["description"] = _libsmi.SmiRevision_description_get
    if _newclass:description = property(_libsmi.SmiRevision_description_get)

class SmiRevisionPtr(SmiRevision):
    def __init__(self, this):
        _swig_setattr(self, SmiRevision, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiRevision, 'thisown', 0)
        _swig_setattr(self, SmiRevision,self.__class__,SmiRevision)
_libsmi.SmiRevision_swigregister(SmiRevisionPtr)

class SmiImport(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiImport, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiImport, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiImport instance at %s>" % (self.this,)
    __swig_getmethods__["module"] = _libsmi.SmiImport_module_get
    if _newclass:module = property(_libsmi.SmiImport_module_get)
    __swig_getmethods__["name"] = _libsmi.SmiImport_name_get
    if _newclass:name = property(_libsmi.SmiImport_name_get)

class SmiImportPtr(SmiImport):
    def __init__(self, this):
        _swig_setattr(self, SmiImport, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiImport, 'thisown', 0)
        _swig_setattr(self, SmiImport,self.__class__,SmiImport)
_libsmi.SmiImport_swigregister(SmiImportPtr)

class SmiMacro(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiMacro, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiMacro, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiMacro instance at %s>" % (self.this,)
    __swig_getmethods__["name"] = _libsmi.SmiMacro_name_get
    if _newclass:name = property(_libsmi.SmiMacro_name_get)
    __swig_getmethods__["decl"] = _libsmi.SmiMacro_decl_get
    if _newclass:decl = property(_libsmi.SmiMacro_decl_get)
    __swig_getmethods__["status"] = _libsmi.SmiMacro_status_get
    if _newclass:status = property(_libsmi.SmiMacro_status_get)
    __swig_getmethods__["description"] = _libsmi.SmiMacro_description_get
    if _newclass:description = property(_libsmi.SmiMacro_description_get)
    __swig_getmethods__["reference"] = _libsmi.SmiMacro_reference_get
    if _newclass:reference = property(_libsmi.SmiMacro_reference_get)

class SmiMacroPtr(SmiMacro):
    def __init__(self, this):
        _swig_setattr(self, SmiMacro, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiMacro, 'thisown', 0)
        _swig_setattr(self, SmiMacro,self.__class__,SmiMacro)
_libsmi.SmiMacro_swigregister(SmiMacroPtr)

class SmiType(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiType, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiType, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiType instance at %s>" % (self.this,)
    __swig_getmethods__["name"] = _libsmi.SmiType_name_get
    if _newclass:name = property(_libsmi.SmiType_name_get)
    __swig_getmethods__["basetype"] = _libsmi.SmiType_basetype_get
    if _newclass:basetype = property(_libsmi.SmiType_basetype_get)
    __swig_getmethods__["decl"] = _libsmi.SmiType_decl_get
    if _newclass:decl = property(_libsmi.SmiType_decl_get)
    __swig_getmethods__["format"] = _libsmi.SmiType_format_get
    if _newclass:format = property(_libsmi.SmiType_format_get)
    __swig_getmethods__["value"] = _libsmi.SmiType_value_get
    if _newclass:value = property(_libsmi.SmiType_value_get)
    __swig_getmethods__["units"] = _libsmi.SmiType_units_get
    if _newclass:units = property(_libsmi.SmiType_units_get)
    __swig_getmethods__["status"] = _libsmi.SmiType_status_get
    if _newclass:status = property(_libsmi.SmiType_status_get)
    __swig_getmethods__["description"] = _libsmi.SmiType_description_get
    if _newclass:description = property(_libsmi.SmiType_description_get)
    __swig_getmethods__["reference"] = _libsmi.SmiType_reference_get
    if _newclass:reference = property(_libsmi.SmiType_reference_get)

class SmiTypePtr(SmiType):
    def __init__(self, this):
        _swig_setattr(self, SmiType, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiType, 'thisown', 0)
        _swig_setattr(self, SmiType,self.__class__,SmiType)
_libsmi.SmiType_swigregister(SmiTypePtr)

class SmiNode(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiNode, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiNode, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiNode instance at %s>" % (self.this,)
    __swig_getmethods__["name"] = _libsmi.SmiNode_name_get
    if _newclass:name = property(_libsmi.SmiNode_name_get)
    __swig_getmethods__["oidlen"] = _libsmi.SmiNode_oidlen_get
    if _newclass:oidlen = property(_libsmi.SmiNode_oidlen_get)
    __swig_getmethods__["oid"] = _libsmi.SmiNode_oid_get
    if _newclass:oid = property(_libsmi.SmiNode_oid_get)
    __swig_getmethods__["decl"] = _libsmi.SmiNode_decl_get
    if _newclass:decl = property(_libsmi.SmiNode_decl_get)
    __swig_getmethods__["access"] = _libsmi.SmiNode_access_get
    if _newclass:access = property(_libsmi.SmiNode_access_get)
    __swig_getmethods__["status"] = _libsmi.SmiNode_status_get
    if _newclass:status = property(_libsmi.SmiNode_status_get)
    __swig_getmethods__["format"] = _libsmi.SmiNode_format_get
    if _newclass:format = property(_libsmi.SmiNode_format_get)
    __swig_getmethods__["value"] = _libsmi.SmiNode_value_get
    if _newclass:value = property(_libsmi.SmiNode_value_get)
    __swig_getmethods__["units"] = _libsmi.SmiNode_units_get
    if _newclass:units = property(_libsmi.SmiNode_units_get)
    __swig_getmethods__["description"] = _libsmi.SmiNode_description_get
    if _newclass:description = property(_libsmi.SmiNode_description_get)
    __swig_getmethods__["reference"] = _libsmi.SmiNode_reference_get
    if _newclass:reference = property(_libsmi.SmiNode_reference_get)
    __swig_getmethods__["indexkind"] = _libsmi.SmiNode_indexkind_get
    if _newclass:indexkind = property(_libsmi.SmiNode_indexkind_get)
    __swig_getmethods__["implied"] = _libsmi.SmiNode_implied_get
    if _newclass:implied = property(_libsmi.SmiNode_implied_get)
    __swig_getmethods__["create"] = _libsmi.SmiNode_create_get
    if _newclass:create = property(_libsmi.SmiNode_create_get)
    __swig_getmethods__["nodekind"] = _libsmi.SmiNode_nodekind_get
    if _newclass:nodekind = property(_libsmi.SmiNode_nodekind_get)

class SmiNodePtr(SmiNode):
    def __init__(self, this):
        _swig_setattr(self, SmiNode, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiNode, 'thisown', 0)
        _swig_setattr(self, SmiNode,self.__class__,SmiNode)
_libsmi.SmiNode_swigregister(SmiNodePtr)

class SmiElement(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiElement, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiElement, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiElement instance at %s>" % (self.this,)

class SmiElementPtr(SmiElement):
    def __init__(self, this):
        _swig_setattr(self, SmiElement, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiElement, 'thisown', 0)
        _swig_setattr(self, SmiElement,self.__class__,SmiElement)
_libsmi.SmiElement_swigregister(SmiElementPtr)

class SmiOption(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiOption, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiOption, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiOption instance at %s>" % (self.this,)
    __swig_getmethods__["description"] = _libsmi.SmiOption_description_get
    if _newclass:description = property(_libsmi.SmiOption_description_get)

class SmiOptionPtr(SmiOption):
    def __init__(self, this):
        _swig_setattr(self, SmiOption, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiOption, 'thisown', 0)
        _swig_setattr(self, SmiOption,self.__class__,SmiOption)
_libsmi.SmiOption_swigregister(SmiOptionPtr)

class SmiRefinement(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SmiRefinement, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SmiRefinement, name)
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C SmiRefinement instance at %s>" % (self.this,)
    __swig_getmethods__["access"] = _libsmi.SmiRefinement_access_get
    if _newclass:access = property(_libsmi.SmiRefinement_access_get)
    __swig_getmethods__["description"] = _libsmi.SmiRefinement_description_get
    if _newclass:description = property(_libsmi.SmiRefinement_description_get)

class SmiRefinementPtr(SmiRefinement):
    def __init__(self, this):
        _swig_setattr(self, SmiRefinement, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, SmiRefinement, 'thisown', 0)
        _swig_setattr(self, SmiRefinement,self.__class__,SmiRefinement)
_libsmi.SmiRefinement_swigregister(SmiRefinementPtr)


smiExit = _libsmi.smiExit

smiSetErrorLevel = _libsmi.smiSetErrorLevel

smiGetFlags = _libsmi.smiGetFlags

smiSetFlags = _libsmi.smiSetFlags

smiGetPath = _libsmi.smiGetPath

smiSetPath = _libsmi.smiSetPath

smiSetSeverity = _libsmi.smiSetSeverity

smiReadConfig = _libsmi.smiReadConfig

smiLoadModule = _libsmi.smiLoadModule

smiIsLoaded = _libsmi.smiIsLoaded

smiGetModule = _libsmi.smiGetModule

smiGetFirstModule = _libsmi.smiGetFirstModule

smiGetNextModule = _libsmi.smiGetNextModule

smiGetModuleIdentityNode = _libsmi.smiGetModuleIdentityNode

smiGetFirstImport = _libsmi.smiGetFirstImport

smiGetNextImport = _libsmi.smiGetNextImport

smiIsImported = _libsmi.smiIsImported

smiGetFirstRevision = _libsmi.smiGetFirstRevision

smiGetNextRevision = _libsmi.smiGetNextRevision

smiGetType = _libsmi.smiGetType

smiGetFirstType = _libsmi.smiGetFirstType

smiGetNextType = _libsmi.smiGetNextType

smiGetParentType = _libsmi.smiGetParentType

smiGetTypeModule = _libsmi.smiGetTypeModule

smiGetTypeLine = _libsmi.smiGetTypeLine

smiGetFirstRange = _libsmi.smiGetFirstRange

smiGetNextRange = _libsmi.smiGetNextRange

smiGetFirstNamedNumber = _libsmi.smiGetFirstNamedNumber

smiGetNextNamedNumber = _libsmi.smiGetNextNamedNumber

smiGetMacro = _libsmi.smiGetMacro

smiGetFirstMacro = _libsmi.smiGetFirstMacro

smiGetNextMacro = _libsmi.smiGetNextMacro

smiGetMacroModule = _libsmi.smiGetMacroModule

smiGetNode = _libsmi.smiGetNode

smiGetFirstNode = _libsmi.smiGetFirstNode

smiGetNextNode = _libsmi.smiGetNextNode

smiGetParentNode = _libsmi.smiGetParentNode

smiGetRelatedNode = _libsmi.smiGetRelatedNode

smiGetFirstChildNode = _libsmi.smiGetFirstChildNode

smiGetNextChildNode = _libsmi.smiGetNextChildNode

smiGetNodeModule = _libsmi.smiGetNodeModule

smiGetNodeType = _libsmi.smiGetNodeType

smiGetNodeLine = _libsmi.smiGetNodeLine

smiGetFirstElement = _libsmi.smiGetFirstElement

smiGetNextElement = _libsmi.smiGetNextElement

smiGetElementNode = _libsmi.smiGetElementNode

smiGetFirstOption = _libsmi.smiGetFirstOption

smiGetNextOption = _libsmi.smiGetNextOption

smiGetOptionNode = _libsmi.smiGetOptionNode

smiGetFirstRefinement = _libsmi.smiGetFirstRefinement

smiGetNextRefinement = _libsmi.smiGetNextRefinement

smiGetRefinementNode = _libsmi.smiGetRefinementNode

smiGetRefinementType = _libsmi.smiGetRefinementType

smiGetRefinementWriteType = _libsmi.smiGetRefinementWriteType

smiGetRefinementLine = _libsmi.smiGetRefinementLine

smiGetFirstUniquenessElement = _libsmi.smiGetFirstUniquenessElement

smiRenderOID = _libsmi.smiRenderOID

smiRenderValue = _libsmi.smiRenderValue

smiRenderNode = _libsmi.smiRenderNode

smiRenderType = _libsmi.smiRenderType

