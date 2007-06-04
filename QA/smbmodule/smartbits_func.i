%module smartbits_func
%{

#include <string.h>
#include <Python.h>
#include <et1000.h>

static PyObject *SmartlibError = NULL;


static void _Smartbits_exception(long code) {
	PyObject *ev;

	ev = PyInt_FromLong(code);
	PyErr_SetObject(SmartlibError, ev);
}

%}

%init %{
SmartlibError = PyErr_NewException("smartbits_funcc.SmartlibError", NULL, NULL);
PyDict_SetItemString(d, "SmartlibError", SmartlibError);
%}

%include typemaps.i
%include pointer.i
// functions

// What to do about these?
//typedef short (*NSErrorCallbackFunc)(int iError, char* szDescription);
//unsigned int   HTGetStructureSize(int iType1, int iHub, int iSlot, int iPort);
//unsigned int   HTGetStructSize(int iType1, int iType2, int iType3, int iType4, int iHub, int iSlot, int iPort);

//%include exception.i
%except(python) { 
	$function
	if((long)result < 0L) {
		_Smartbits_exception((long) result);
		return NULL;
	} 
}


int       HTSetStructure(int iType1,int iType2,int iType3,int iType4,void* pData,unsigned int uiLen, int iHub, int iSlot, int iPort);
int       HTGetStructure(int iType1,int iType2,int iType3,int iType4,void* pData,unsigned int uiLen, int iHub, int iSlot, int iPort);
int       HTSetCommand(  int iType1,int iType2,int iType3,int iType4,void* pData,int iHub, int iSlot, int iPort);
int       HTDefaultStructure(int iType1,void* pData,unsigned int uiLen, int iHub, int iSlot, int iPort);
int       HTRun(int iMode, int iHub, int iSlot, int iPort);
int       HTGroupStart(int iHub);
int       HTGroupStep(int iHub);
int       HTGroupStop(int iHub);

int       HGRun(int iMode);
int       HGStart(void);
int       HGStep(void);
int       HGStop(void);
int       HGStartSetGroup(void);
int       HGSetGroup(char* pszPortIdList);
int       HGClearGroup(void);
int       HGSetGroupType(int SubTypesMode, int * Data);
int       HGAddtoGroup(int iHub, int iSlot, int iPort);
int       HGRemoveFromGroup(int iHub, int iSlot, int iPort);
int       HGRemovePortIdFromGroup(int iPortId);
int       HGEndSetGroup(void);
int       HGIsPortInGroup(int iPortId);
int       HGIsHubSlotPortInGroup(int iHub, int iSlot, int iPort);
int       HGGetGroupCount(void);
int       HGClear(void);
int       HGSetStructure(int iType1,int iType2,int iType3,int iType4,void* pData,unsigned int uiLen);
int       HGSetCommand(  int iType1,int iType2,int iType3,int iType4,void* pData);

int       ETLink(int iComPort);
int       ETSocketLink(char* szIPAddr, int iTCPport);
int       ETSocketLinkRsvNone(char* szIPAddr, int iTCPPort);
int       ETDebugLink(int iComPort,unsigned long ulType,char* pszFile);
int       ETLoopback(int iPort, int iStatus);
int       ETUnLink(void);
int       ETUnLinkAll(void);

int       NSSocketLink(char* szIPAddr, int iTCPPort, int iReserve);
int       NSUnLink(void);
int       NSUnLinkAll(void);
