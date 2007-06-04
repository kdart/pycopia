%module libsmi

%{

#include <stdlib.h>
#include <stdio.h>
#include <smi.h>
#include "Python.h"


/* libsmi module exception */
static PyObject *SmiError = NULL;
static PyObject *ErrorHandler = NULL;


/* custom Init. Converts None argument to NULL, and raises an exception on failure. */
static PyObject *
libsmi_Init(PyObject *self, PyObject *args)
{
	PyObject *tag = NULL;
	char	*stag = NULL;
	register int rv = 0;
	
	if (PyTuple_Size(args) == 0)
		rv = smiInit(NULL);
	else {
		if (!PyArg_ParseTuple(args, "O:smiInit", &tag))
			return NULL;
		if(PyObject_IsTrue(tag)) {
			stag = PyString_AsString(tag);
			rv = smiInit(stag);
		} else {
			rv = smiInit(NULL);
		}
	}
	if (rv) {
		PyErr_SetString(SmiError, "smiInit: Failed to initialize libsmi!");
		return NULL;
	} else {
		Py_INCREF(Py_None);
		return Py_None;
	}
}


/*
typedef void (SmiErrorHandler) (char *path, int line, int severity, char *msg, char *tag);
*/
void libsmi_ErrorHandler(char *path, int line, int severity, char *msg, char *tag)
{
	PyObject *arglist, *result;

	if (ErrorHandler) {
		arglist = Py_BuildValue("(siiss)", path, line, severity, msg, tag);
		result = PyEval_CallObject(ErrorHandler, arglist);
		Py_DECREF(arglist);
		if (result == NULL) {
			PyErr_Clear();
		} else {
			Py_DECREF(result);
		}
	}

}

static PyObject *
libsmi_SetErrorHandler(PyObject *self, PyObject *args)
{
	PyObject *pycb;

	if (!PyArg_ParseTuple(args, "O:SetErrorHandler", &pycb))
		return NULL;
	if (!PyCallable_Check(pycb)) {
		PyErr_SetString(PyExc_TypeError, "SetErrorHandler: parameter must be callable.");
		return NULL;
	}
	Py_XINCREF(pycb);
	Py_XDECREF(ErrorHandler);
	ErrorHandler = pycb;
	smiSetErrorHandler(libsmi_ErrorHandler);
	Py_INCREF(Py_None);
	return Py_None;
}


/* Convert a Python list to an array of ints
 *
 */

/*
static PyObject *
SmiSubid_FromList(PyObject *self, PyObject *args) {
	PyObject *thelist;
	PyObject *swigptr;
	int len, i;

	if(!PyArg_ParseTuple(args,"O:SmiSubid_FromList",&thelist)) return NULL;
	if(!PySequence_Check(thelist)) {
		PyErr_SetString(PyExc_TypeError, 
			"SmiSubid_FromList: parameter must be a sequence object.");
		return NULL;
	}
	len = PyObject_Length(thelist);
	swigptr = ptrcreate("int", 0, len);

	for (i = 0; i < len; i++) {
		ptrset(swigptr, PySequence_GetItem(thelist, i), i, "int");
	}
	return swigptr;
}
*/

/* List_FromSmiSubid(SmiSubidPtr, oidlen)
 */
static PyObject *
List_FromSmiSubid(PyObject *self, PyObject *args)
{
	int size, i;
	PyObject *oidptr, *list;
	SmiSubid *oid;

	if(!PyArg_ParseTuple(args,"Oi:List_FromSmiSubid",&oidptr, &size)) return NULL;
	if ((SWIG_ConvertPtr(oidptr,(void **) &oid,SWIGTYPE_p_SmiSubid,1)) == -1) return NULL;
	if (!(list = PyList_New(0))) return NULL;
	for (i = 0; i < size; i++) {
		PyList_Append(list, PyInt_FromLong((long) *(oid+i)));
	}
	Py_INCREF(list);
	return list;
}

/* libsmi_GetNodeByOID is a custom wrapper that takes a Python list of ints as
 * a parameter.
 */
static PyObject *
libsmi_GetNodeByOID(PyObject *self, PyObject *args)
{
	PyObject *list;
	PyObject *resultobj;
	SmiSubid *oid;
	SmiNode *result ;
	unsigned int len, i;

	if(!PyArg_ParseTuple(args,"O:GetNodeByOID",&list)) return NULL;
	if(!PyList_Check(list)) {
		PyErr_SetString(PyExc_TypeError, 
			"GetNodeByOID: parameter must be a list object.");
		return NULL;
	}
	len = PyObject_Length(list);
	if (!(oid = (SmiSubid *) malloc(len*sizeof(SmiSubid)))) {
		PyErr_SetString(PyExc_TypeError, "GetNodeByOID: Could not alloc memory.");
		return NULL;
	}
	for (i = 0; i < len; i++) {
		oid[i] = (SmiSubid) PyInt_AsLong(PyList_GetItem(list, i));
	}
	if (PyErr_Occurred()) {
		return NULL;
	}
	result = (SmiNode *) smiGetNodeByOID(len, oid);
	free(oid);
	if (result) {
		resultobj = SWIG_NewPointerObj((void *) result, SWIGTYPE_p_SmiNode, 0);
		return resultobj;
	} else {
		Py_INCREF(Py_None);
		return Py_None;
	}

}

// ---------------------------------------------------------------

%}

%init %{
SmiError = PyErr_NewException("_libsmi.SmiError", NULL, NULL);
PyDict_SetItemString(d, "SmiError", SmiError);
%}

%native (Init) libsmi_Init;
%native (SetErrorHandler) libsmi_SetErrorHandler;
// %native (SmiSubid_FromList) SmiSubid_FromList;
%native (List_FromSmiSubid) List_FromSmiSubid;
%native (GetNodeByOID) libsmi_GetNodeByOID;


//%include typemaps.i


%immutable;

#define SMI_LIBRARY_VERSION "2:22:0"
#define SMI_VERSION_MAJOR 0
#define SMI_VERSION_MINOR 4
#define SMI_VERSION_PATCHLEVEL 2
#define SMI_VERSION_STRING "0.4.2"

#define SMI_FLAG_NODESCR   0x0800 /* do not load descriptions/references.    */
#define SMI_FLAG_VIEWALL   0x1000 /* all modules are `known', need no views. */
#define SMI_FLAG_ERRORS    0x2000 /* print parser errors.                    */
#define SMI_FLAG_RECURSIVE 0x4000 /* recursively parse imported modules.     */
#define SMI_FLAG_STATS     0x8000 /* print statistics after parsing module.  */
#define SMI_FLAG_MASK      (SMI_FLAG_NODESCR|SMI_FLAG_VIEWALL|SMI_FLAG_STATS|SMI_FLAG_RECURSIVE|SMI_FLAG_ERRORS)

#define SMI_RENDER_NUMERIC   0x01 /* render as numeric values */
#define SMI_RENDER_NAME      0x02 /* render as names */
#define SMI_RENDER_QUALIFIED 0x04 /* render names with module prefix */
#define SMI_RENDER_FORMAT    0x08 /* render by applying the type's format if
				     type is given and format is present */
#define SMI_RENDER_PRINTABLE 0x10 /* render string values as a printable
				     string if all octets are isprint() */
#define SMI_RENDER_UNKNOWN   0x20 /* render even unknown items as strings
  				     ("<unknown>") so that we never get NULL */
#define SMI_RENDER_ALL       0xff /* render as `human friendly' as possible */
#define SMI_UNKNOWN_LABEL "<unknown>"


typedef char                    *SmiIdentifier;
typedef unsigned long           SmiUnsigned32;
typedef long                    SmiInteger32;

typedef unsigned long long	SmiUnsigned64;
typedef long long		SmiInteger64;

typedef unsigned int            SmiSubid;
typedef float                   SmiFloat32;
typedef double                  SmiFloat64;
//typedef long double             SmiFloat128;


//%pragma make_default
 
typedef enum SmiLanguage {
    SMI_LANGUAGE_UNKNOWN                = 0,   
    SMI_LANGUAGE_SMIV1                  = 1,
    SMI_LANGUAGE_SMIV2                  = 2,
    SMI_LANGUAGE_SMING                  = 3,
    SMI_LANGUAGE_SPPI                   = 4
} SmiLanguage;

 
typedef enum SmiBasetype {
    SMI_BASETYPE_UNKNOWN                = 0,   
    SMI_BASETYPE_INTEGER32              = 1,   
    SMI_BASETYPE_OCTETSTRING            = 2,
    SMI_BASETYPE_OBJECTIDENTIFIER       = 3,
    SMI_BASETYPE_UNSIGNED32             = 4,
    SMI_BASETYPE_INTEGER64              = 5,   
    SMI_BASETYPE_UNSIGNED64             = 6,   
    SMI_BASETYPE_FLOAT32                = 7,   
    SMI_BASETYPE_FLOAT64                = 8,   
    SMI_BASETYPE_FLOAT128               = 9,   
    SMI_BASETYPE_ENUM                   = 10,
    SMI_BASETYPE_BITS                   = 11   
} SmiBasetype;

 
typedef enum SmiStatus {
    SMI_STATUS_UNKNOWN          = 0,  
    SMI_STATUS_CURRENT          = 1,  
    SMI_STATUS_DEPRECATED       = 2,  
    SMI_STATUS_MANDATORY        = 3,  
    SMI_STATUS_OPTIONAL         = 4,  
    SMI_STATUS_OBSOLETE         = 5   
} SmiStatus;

 
typedef enum SmiAccess {
    SMI_ACCESS_UNKNOWN          = 0,  
    SMI_ACCESS_NOT_IMPLEMENTED  = 1,  
    SMI_ACCESS_NOT_ACCESSIBLE   = 2,  
    SMI_ACCESS_NOTIFY           = 3,  
    SMI_ACCESS_READ_ONLY        = 4,
    SMI_ACCESS_READ_WRITE       = 5,
    SMI_ACCESS_INSTALL          = 6,
    SMI_ACCESS_INSTALL_NOTIFY   = 7,
    SMI_ACCESS_REPORT_ONLY      = 8
} SmiAccess;

 
typedef unsigned int SmiNodekind;
#define SMI_NODEKIND_UNKNOWN      0x0000     /* should not occur             */
#define SMI_NODEKIND_NODE         0x0001
#define SMI_NODEKIND_SCALAR       0x0002
#define SMI_NODEKIND_TABLE        0x0004
#define SMI_NODEKIND_ROW          0x0008
#define SMI_NODEKIND_COLUMN       0x0010
#define SMI_NODEKIND_NOTIFICATION 0x0020
#define SMI_NODEKIND_GROUP        0x0040
#define SMI_NODEKIND_COMPLIANCE   0x0080
#define SMI_NODEKIND_CAPABILITIES 0x0100
#define SMI_NODEKIND_ANY          0xffff



typedef enum SmiDecl {
    SMI_DECL_UNKNOWN            = 0,   
    SMI_DECL_IMPLICIT_TYPE      = 1,
    SMI_DECL_TYPEASSIGNMENT     = 2,
    SMI_DECL_IMPL_SEQUENCEOF    = 4,	 
    SMI_DECL_VALUEASSIGNMENT    = 5,
    SMI_DECL_OBJECTTYPE         = 6,     
    SMI_DECL_OBJECTIDENTITY     = 7,     
    SMI_DECL_MODULEIDENTITY     = 8,
    SMI_DECL_NOTIFICATIONTYPE   = 9,
    SMI_DECL_TRAPTYPE           = 10,
    SMI_DECL_OBJECTGROUP        = 11, 
    SMI_DECL_NOTIFICATIONGROUP  = 12,
    SMI_DECL_MODULECOMPLIANCE   = 13,
    SMI_DECL_AGENTCAPABILITIES  = 14,
    SMI_DECL_TEXTUALCONVENTION  = 15,
    SMI_DECL_MACRO	        = 16,
    SMI_DECL_COMPL_GROUP        = 17,
    SMI_DECL_COMPL_OBJECT       = 18,
     
    SMI_DECL_MODULE             = 33,
    SMI_DECL_EXTENSION          = 34,
    SMI_DECL_TYPEDEF            = 35,
    SMI_DECL_NODE               = 36,
    SMI_DECL_SCALAR             = 37,
    SMI_DECL_TABLE              = 38,
    SMI_DECL_ROW                = 39,
    SMI_DECL_COLUMN             = 40,
    SMI_DECL_NOTIFICATION       = 41,
    SMI_DECL_GROUP              = 42,
    SMI_DECL_COMPLIANCE         = 43
} SmiDecl;

 
typedef enum SmiIndexkind {
    SMI_INDEX_UNKNOWN           = 0, 
    SMI_INDEX_INDEX             = 1,
    SMI_INDEX_AUGMENT           = 2,
    SMI_INDEX_REORDER           = 3,
    SMI_INDEX_SPARSE            = 4,
    SMI_INDEX_EXPAND            = 5
} SmiIndexkind;

 
typedef struct SmiValue {
    SmiBasetype             basetype;
    unsigned int	    len;          
    union {
        SmiUnsigned64       unsigned64;
        SmiInteger64        integer64;
        SmiUnsigned32       unsigned32;
        SmiInteger32        integer32;
        SmiFloat32          float32;
        SmiFloat64          float64;
//        SmiFloat128         float128;
        SmiSubid	    *oid;
        unsigned char       *ptr;	  
    } value;
} SmiValue;
 
typedef struct SmiNamedNumber {
    SmiIdentifier       name;
    SmiValue            value;
} SmiNamedNumber;

 
typedef struct SmiRange {
    SmiValue            minValue;
    SmiValue            maxValue;
} SmiRange;

 
typedef struct SmiModule {
    SmiIdentifier       name;
    char                *path;
    char                *organization;
    char                *contactinfo;
    char                *description;
    char                *reference;
    SmiLanguage		language;
    int                 conformance;
} SmiModule;

 
typedef struct SmiRevision {
    time_t              date;
    char                *description;
} SmiRevision;

 
typedef struct SmiImport {
    SmiIdentifier       module;
    SmiIdentifier       name;
} SmiImport;

 
typedef struct SmiMacro {
    SmiIdentifier       name;
    SmiDecl             decl;
    SmiStatus           status;
    char                *description;
    char                *reference;
} SmiMacro;

 
typedef struct SmiType {
    SmiIdentifier       name;
    SmiBasetype         basetype;
    SmiDecl             decl;
    char                *format;
    SmiValue            value;
    char                *units;
    SmiStatus           status;
    char                *description;
    char                *reference;
} SmiType;

 
typedef struct SmiNode {
    SmiIdentifier       name;
    unsigned int	oidlen;
    SmiSubid		*oid;          
    SmiDecl             decl;
    SmiAccess           access;
    SmiStatus           status;
    char                *format;
    SmiValue            value;
    char                *units;
    char                *description;
    char                *reference;
    SmiIndexkind        indexkind;     
    int                 implied;       
    int                 create;        
    SmiNodekind         nodekind;
} SmiNode;

 
typedef struct SmiElement {
} SmiElement;

 
typedef struct SmiOption {
    char                *description;
} SmiOption;

 
typedef struct SmiRefinement {
    SmiAccess           access;
    char                *description;
} SmiRefinement;


%mutable;
//%pragma no_default
//%pragma(python) include="libsmi_patch.py"


//int smiInit(char *tag);
void smiExit();
void smiSetErrorLevel(int level);
int smiGetFlags();
void smiSetFlags(int userflags);
char *smiGetPath();
int smiSetPath(char *path);
void smiSetSeverity(char *pattern, int severity);
int smiReadConfig(char *filename, char *tag);
char *smiLoadModule(char *module);
int smiIsLoaded(char *module);


SmiModule *smiGetModule(char *module);
SmiModule *smiGetFirstModule();
SmiModule *smiGetNextModule(SmiModule *smiModulePtr);
SmiNode *smiGetModuleIdentityNode(SmiModule *smiModulePtr);
SmiImport *smiGetFirstImport(SmiModule *smiModulePtr);
SmiImport *smiGetNextImport(SmiImport *smiImportPtr);
int smiIsImported(SmiModule *smiModulePtr, SmiModule *importedModulePtr, char *importedName);
SmiRevision *smiGetFirstRevision(SmiModule *smiModulePtr);
SmiRevision *smiGetNextRevision(SmiRevision *smiRevisionPtr);

SmiType *smiGetType(SmiModule *smiModulePtr, char *type);
SmiType *smiGetFirstType(SmiModule *smiModulePtr);
SmiType *smiGetNextType(SmiType *smiTypePtr);
SmiType *smiGetParentType(SmiType *smiTypePtr);
SmiModule *smiGetTypeModule(SmiType *smiTypePtr);
int smiGetTypeLine(SmiType *smiTypePtr);
SmiRange *smiGetFirstRange(SmiType *smiTypePtr);
SmiRange *smiGetNextRange(SmiRange *smiRangePtr);
SmiNamedNumber *smiGetFirstNamedNumber(SmiType *smiTypePtr);
SmiNamedNumber *smiGetNextNamedNumber(SmiNamedNumber *smiNamedNumberPtr);

SmiMacro *smiGetMacro(SmiModule *smiModulePtr, char *macro);
SmiMacro *smiGetFirstMacro(SmiModule *smiModulePtr);
SmiMacro *smiGetNextMacro(SmiMacro *smiMacroPtr);
SmiModule *smiGetMacroModule(SmiMacro *smiMacroPtr);


SmiNode *smiGetNode(SmiModule *smiModulePtr, char *name);
//SmiNode *smiGetNodeByOID(unsigned int oidlen, SmiSubid oid[]);
SmiNode *smiGetFirstNode(SmiModule *smiModulePtr, SmiNodekind nodekind);
SmiNode *smiGetNextNode(SmiNode *smiNodePtr, SmiNodekind nodekind);
SmiNode *smiGetParentNode(SmiNode *smiNodePtr);
SmiNode *smiGetRelatedNode(SmiNode *smiNodePtr);
SmiNode *smiGetFirstChildNode(SmiNode *smiNodePtr);
SmiNode *smiGetNextChildNode(SmiNode *smiNodePtr);
SmiModule *smiGetNodeModule(SmiNode *smiNodePtr);
SmiType *smiGetNodeType(SmiNode *smiNodePtr);
int smiGetNodeLine(SmiNode *smiNodePtr);


SmiElement *smiGetFirstElement(SmiNode *smiNodePtr);
SmiElement *smiGetNextElement(SmiElement *smiElementPtr);
SmiNode *smiGetElementNode(SmiElement *smiElementPtr);

SmiOption *smiGetFirstOption(SmiNode *smiComplianceNodePtr);
SmiOption *smiGetNextOption(SmiOption *smiOptionPtr);
SmiNode *smiGetOptionNode(SmiOption *smiOptionPtr);

SmiRefinement *smiGetFirstRefinement(SmiNode *smiComplianceNodePtr);
SmiRefinement *smiGetNextRefinement(SmiRefinement *smiRefinementPtr);
SmiNode *smiGetRefinementNode(SmiRefinement *smiRefinementPtr);
SmiType *smiGetRefinementType(SmiRefinement *smiRefinementPtr);
SmiType *smiGetRefinementWriteType(SmiRefinement *smiRefinementPtr);
int smiGetRefinementLine(SmiRefinement *smiRefinementPtr);
SmiElement *smiGetFirstUniquenessElement(SmiNode *smiNodePtr);

char *smiRenderOID(unsigned int oidlen, SmiSubid *oid, int flags);
char *smiRenderValue(SmiValue *smiValuePtr, SmiType *smiTypePtr, int flags);
char *smiRenderNode(SmiNode *smiNodePtr, int flags);
char *smiRenderType(SmiType *smiTypePtr, int flags);

