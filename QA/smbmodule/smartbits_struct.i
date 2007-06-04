%module smartbits_struct
%include pointer.i
%{

#include <string.h>
#include <stdlib.h>
#include <Python.h>
#include <et1000.h>



void intncpy(int *dst, int *src, int n) 
{
	int i;

	for (i = 0; i < n; i++) {
		*(((int *)dst)+i) = *(((int *)src)+i);
	}
}

void longncpy(long *dst, long *src, int n)
{
	int i;

	for (i = 0; i < n; i++) {
		*(((long *)dst)+i) = *(((long *)src)+i);
	}
}

void shortncpy(short *dst, short *src, int n)
{
	int i;

	for (i = 0; i < n; i++) {
		*(((short *)dst)+i) = *(((short *)src)+i);
	}
}

void charncpy(short *dst, short *src, int n)
{
	int i;

	for (i = 0; i < n; i++) {
		*(((char *)dst)+i) = *(((char *)src)+i);
	}
}

PyObject *LongArray_FromList(PyObject *self, PyObject *args) {
	PyObject *thelist;
	PyObject *swigptr;
	int len, i;

	if(!PyArg_ParseTuple(args,"O:LongArray_FromList",&thelist)) return NULL;
	if(!PySequence_Check(thelist)) return NULL;
	len = PyObject_Length(thelist);
	swigptr = ptrcreate("long", 0L, len);
	for (i = 0; i < len; i++) {
		ptrset(swigptr, PySequence_GetItem(thelist, i), i, "long");
	}
	return swigptr;
}

int list2intarray(PyObject *argo1, int *target, int dim0) 
{
    int size, i;
    PyObject *o;

    if (PyList_Check(argo1)) {
       size = PyList_Size(argo1);
       for(i=0 ; i < size || i < dim0 ; i++) {
          o = PyList_GetItem(argo1,i);
          if (PyInt_Check(o)) {
             target[i] = (int) PyInt_AsLong(o);
          }
       }
       for(i=size ; i < dim0 ; i++) target[i] = 0;
       return 0;
    }
    return -1;
}

int list2shortarray(PyObject *argo1, short *target, int dim0) 
{
    int size, i;
    PyObject *o;

    if (PyList_Check(argo1)) {
       size = PyList_Size(argo1);
       for(i=0 ; i < size || i < dim0 ; i++) {
          o = PyList_GetItem(argo1,i);
          if (PyInt_Check(o)) {
             target[i] = (short) PyInt_AsLong(o);
          }
       }
       for(i=size ; i < dim0 ; i++) target[i] = 0;
       return 0;
    }
    return -1;
}

int list2longarray(PyObject *argo1, long *target, int dim0) 
{
    int size, i;
    PyObject *o;

    if (PyList_Check(argo1)) {
       size = PyList_Size(argo1);
       for(i=0 ; i < size || i < dim0 ; i++) {
          o = PyList_GetItem(argo1,i);
          if (PyInt_Check(o)) {
             target[i] = (long) PyInt_AsLong(o);
          }
       }
       for(i=size ; i < dim0 ; i++) target[i] = 0L;
       return 0;
    }
    return -1;
}

int list2chararray(PyObject *argo1, unsigned char *target, int dim0) 
{
    int size, i;
    PyObject *o;

    if (PyList_Check(argo1)) {
       size = PyList_Size(argo1);
       for(i=0 ; i < size || i < dim0 ; i++) {
          o = PyList_GetItem(argo1,i);
          if (PyInt_Check(o)) {
             target[i] = (unsigned char) PyInt_AsLong(o);
          }
       }
       for(i=size ; i < dim0 ; i++) target[i] = 0L;
       return 0;
    }
    return -1;
}
%}

%native (LongArray_FromList) LongArray_FromList;

//%include malloc.i
%include typemaps.i


// A typemap for handling any int [] array 
// %typemap(memberin) int [ANY] { 
// 	int i, size; 
// 	PyObect *thelist;
// 
// 	if (!PyArg_ParseTuple(args, "O!" ,&PyList_Type, &thelist))
// 		return NULL;
// // XXX
// 	size = PyList_Size(thelist);
// 	for (i = 0; i < $dim0; i++) 
// 		if (i > size) {
// 			$target[i] = 0;
// 		} else {
// 			$target[i] = *($source+i); 
// 		}
// }



// XXX experimental
//%typemap(python,in) int [ANY] { 
//	// int python,in
//	// source: $source
//	// target: $target
//	// type  : $type
//	// mangle: $mangle
//	// value : $value
//	// dim0  : $dim0
//}

%typemap(memberout) int [ANY] {
	// int member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	intncpy($target,$source,$dim0); 
}

%typemap(memberin) int [ANY] { 
	// int member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2intarray(argo1, $target, $dim0) ;
}

%typemap(memberout) unsigned int [ANY] {
	// unsigned int member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	intncpy($target,$source,$dim0); 
}

%typemap(memberin) unsigned int [ANY] { 
	// unsigned int member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2intarray(argo1, $target, $dim0) ;
}

%typemap(memberout) short [ANY] { 
	// short member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
}

%typemap(memberin) short [ANY] { 
	// short member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2shortarray(argo1, $target, $dim0) ;
}

%typemap(memberout) unsigned short [ANY] { 
	// unsigned short member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
}

%typemap(memberin) unsigned short [ANY] { 
	// unsigned short member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2shortarray(argo1, $target, $dim0) ;
}

%typemap(memberin) unsigned long [ANY] { 
	// unsigned long member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2longarray(argo1, $target, $dim0) ;
}

%typemap(memberout) unsigned long [ANY] { 
	// unsigned long member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	longncpy($target,$source,$dim0); 
}

%typemap(memberin) long [ANY] { 
	// long member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2longarray(argo1, $target, $dim0) ;
}

%typemap(memberout) long [ANY] { 
	// long member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	longncpy($target,$source,$dim0); 
}

%typemap(memberout) unsigned char [ANY] { 
	// unsigned char member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	strncpy($target,$source,$dim0); 
}

%typemap(memberin) unsigned char [ANY] { 
	// unsigned char member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// value : $value
	// dim0  : $dim0
	list2chararray(argo1, $target, $dim0) ;
}

%typemap(memberout) char [ANY] { 
	// char member OUT
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// dim0  : $dim0
	strncpy($target,$source,$dim0); 
}

%typemap(memberin) char [ANY] { 
	// char member IN
	// source: $source
	// target: $target
	// type  : $type
	// mangle: $mangle
	// dim0  : $dim0
	strncpy($target,$source,$dim0); 
}


typedef int BOOL;

typedef struct tagHubSlotPort {
	int	iHub;
	int	iSlot;
	int	iPort;
	} _HubSlotPort;

typedef struct tagU64 {
	unsigned long	high;
	unsigned long	low;
	} U64;

// 9 "/usr/local/include/tcpisp.h" 2 3

// construct default accessor methods
%pragma make_default

typedef struct tagTCPTimeInfoCount
{
	unsigned long  ulTest;
	unsigned long  ulRecords;
} TCPTimeInfoCount;

typedef struct tagTCPGaps
{
	unsigned long  ulSYNGap;
	unsigned long  ulFINGap;
	unsigned long  ulInterframeGap;
	unsigned long  ulTimeInterval;
} TCPGaps;

typedef struct tagTCPConnectionStatusOnly
{
	 unsigned short  uiConnId;
	 unsigned char   ucConnected;
} TCPConnectionStatusOnly;

typedef struct tagTCPConnEventInfo
{
   unsigned long   InitiatedConnections;
   unsigned long   ConnectionReqRecv;
   unsigned long   UnexpectedConnReq;
   unsigned long   SYNACKSent;
   unsigned long   ExpectedSYNACKRecv;
   unsigned long   UnexpectedSYNACKRecv;
   unsigned long   DuplicatedSYNACKRecv;
   unsigned long   CloseFINACKSent;
   unsigned long   AckFINACKSent;
   unsigned long   ExpectedFINACK;
   unsigned long   ExpectedFinalFINACK;
   unsigned long   UnexpectedFINACK;
   unsigned long   UnexpectedFINACKWaitingForAck;
   unsigned long   UnexpectedFINACKAfterRecvFin;
   unsigned long   ACKSent;
   unsigned long   FinalFIN_ACKSent;
   unsigned long   SYNACK_ACKRecv;
   unsigned long   FINACK_ACKRecv;
   unsigned long   NoConnectUnexpectedACKRecv;
   unsigned long   RSTRecv;
   unsigned long   RSTRecvForConnection;
   unsigned long   CurrentConnections;
   unsigned long   AbandonedConnections;
   unsigned long   NoDPResources;
   unsigned long   NoMoreConnectionEntries;
   unsigned long   NoTxResources;
   unsigned long   NumberOfHTTPGetRx;
   unsigned long   NumberOfHTTPReplyRx;
} TCPConnEventInfo;

typedef struct tagTCPConnTimeInfo
{
   unsigned long  notUsed;
   unsigned long  NumbConnStarted;
   unsigned long  NumbConnCompleted;
   unsigned long  NumbConnCycleCompleted;
} TCPConnTimeInfo;

typedef struct tagTCPTransRateInfo {
    unsigned short     Version;
    unsigned short     Records;
    unsigned long      IpAddress;
    unsigned long      FirstTimeStamp;
    unsigned long      LastTimeStamp;
    unsigned long      NumberOfPackets;
    unsigned long      BitMask;
} TCPTransRateInfo;

typedef struct tagTCPStateInfo
{
	struct tagTCPInfo *link;
	unsigned long  SourceIP;
	unsigned short SourcePort;
	unsigned short DestPort;
	unsigned long  DestIP;
	unsigned char  State;
	unsigned char Spare[3];
} TCPStateInfo;

typedef struct tagTCPConnRequestTrigger
{
 unsigned char  ucEnable;
 unsigned char  ucDirection;
 unsigned char  ucCompCombo;
 unsigned char  ucReserved1;
 unsigned short uiTrig1Offset;
 unsigned short uiTrig1Range;
 unsigned char  ucTrig1Pattern[6];
 unsigned char  ucTrig1Mask[6];
 unsigned short uiTrig2Offset;
 unsigned short uiTrig2Range;
 unsigned char  ucTrig2Pattern[6];
 unsigned char  ucTrig2Mask[6];
 unsigned char  ucReserved[20];
}TCPConnRequestTrigger;

typedef struct		tagTCPConnectRequest
{
	unsigned long	ulTCPConnectRequestRate;
	unsigned long	ulBurstCnt;
	unsigned char	ucBurstMode;
	BOOL           bTearDownTCPConnection;
}TCPConnectRequest;

typedef struct tagTCPDataLogEventTx{
	 unsigned short  uiConnId;
	 unsigned short  uiDataLen;
	 unsigned short  uiWindowSize;
	 unsigned long   ulSeq;
	 unsigned long   ulAck;
	 unsigned short  uiIpSequence;
	 unsigned char   ucTcpFlag;
	 unsigned char   ucRetryCount;
} TCPDataLogEventTx;
typedef struct tagTCPDataLogEventRx{
	 unsigned long   ulSrcIpAddress;
	 unsigned short  uiSrcPort;
	 unsigned short  uiDestPort;
	 unsigned long   ulDestIpAddress;
	 unsigned long   ulTxTimeStamp;
	 unsigned long   ulRxTimeStamp;
	 unsigned short  uiDataLen;
	 unsigned short  uiWindowSize;
	 unsigned long   ulSeq;
	 unsigned long   ulAck;
	 unsigned short  uiIpSequence;
	 unsigned char   ucTtl;
	 unsigned char   ucTcpFlag;
	 unsigned char   ucFlagMask;
} TCPDataLogEventRx;
typedef struct tagTCPDataLogEventRx2{
   unsigned short   uiDestPort;
   unsigned long    ulRxTimeStamp;
   unsigned long    ulTxTimeStamp;
   unsigned long    ulSeq;
   unsigned short   uiIpSequence;
} TCPDataLogEventRx2;
typedef struct tagTCPConnectionStatus{
	unsigned short uiConnId;
	unsigned long  ulSrcIpAddress;
	unsigned short uiSrcPort;
	unsigned long  ulDestIpAddress;
	unsigned short uiDestPort;
	unsigned long  ulBeginSequence;
	unsigned long  ulLastSequence;
	unsigned long  ulDataStartTime;
	unsigned long  ulDataStopTime;
	unsigned long  ulMinLatency;
	unsigned long  ulMaxLatency;
	unsigned long  ulTotalLatency;
	unsigned long  ulPacketsTx;
	unsigned long  ulPacketsRx;
	unsigned long  ulTotalTimeouts;
	unsigned long	ulTotalDataRetransmits;
	unsigned long  ulStartTimeMS;
	unsigned long  ulStartTimeNS;
	unsigned long  ulStopTimeMS;
	unsigned long  ulStopTimeNS;
	unsigned long  ulConnectionSynNS;
	unsigned long  ulConnectionFinNS;
	unsigned long  ulNumberFragments;
	unsigned long  ulTtlChanges;
	unsigned long  ulDataOutOfOrder;
	unsigned short uiAverageTxWindowSize;
	unsigned char	ucConnStatusMask;
} TCPConnectionStatus;
typedef struct tagARPEntry{
	unsigned long	ulIpAddress;
	unsigned char	ucMacAddress[6];
	unsigned char	ucType;
} ARPEntry;
typedef struct tagTCPSetup
{
	unsigned long	ulMeAddress;
	unsigned short uiMePort;
	unsigned long  ulHisAddress;
	unsigned short uiHisPort;
	unsigned long  ulRouterAddress;
	unsigned short uiRetransmitTimeout;
	unsigned short uiSendTimeout;
	unsigned short uiMss;
	unsigned char  ucTtl;
	unsigned char  ucTos;
	unsigned short uiWindowSize;
	unsigned long  ulDataToSend;
	unsigned char  ucRetry;
	unsigned long  ulFrameGap;
   unsigned long  ulOption1;
   unsigned long  ulOption2;
   unsigned long  ulOption3;
   unsigned long  ulOption4;
}TCPSetup;
typedef struct tagTCPISPConnectionData {
	unsigned long   ulType;
   unsigned long   ulUserId;
   unsigned long   ulSourceAddress;
   unsigned long   ulVIPAddress;
   unsigned long   ulSourceTCPPort;
   unsigned long   ulDestinationAddress;
   unsigned long   ulDestinationPort;
	unsigned long   ulRouterAddress;
   unsigned long   ulIfg;
   unsigned long   ulTos;
	unsigned long   ulTtl;
   unsigned long   ulSendDataTimeout;
   unsigned long   ulKeepAliveTimer;
   unsigned long   ulWindowSize;
   unsigned long   ulMss;
   unsigned long   ulDataToSend;
   unsigned long   ulAckRatio;
   unsigned long   ulCcOptions;
   unsigned long   ulCcValue1;
   unsigned long   ulCcValue2;
   unsigned long   ulRetryCount;
   unsigned long   ulRttOptions;
   unsigned long   ulRttTimeout;
   unsigned long   ulRttAlpha;
   unsigned long   ulRttBeta;
   unsigned long   ulRttDelta;
   unsigned long   ulRttRho;
   unsigned long   ulRttEta;
   unsigned long   ulOptionBits1;
   unsigned long   ulOptionBits2;
   unsigned long   ulOptionBits3;
   unsigned long   ulOptionBits4;
   unsigned long   ulKeepAliveTime;
   unsigned long   ulDataExpected;
   unsigned char   ucURL[20];
   unsigned char   ucReserved[128];
} TCPISPConnectionData;

typedef struct tagTCPCurveTimeData
{
   unsigned long ulTime;
   unsigned long ulDataSize;
} TCPCurveTimeData;

typedef struct tagTCPCurveRecord
{
   unsigned long ulConnId;
   unsigned long ulDataPoints;
   TCPCurveTimeData CurveTimeData[64];
} TCPCurveRecord;

typedef struct tagTCPISPConnectionDataCurve
{
   unsigned long ulRecords;
   TCPCurveRecord CurveRecords[64];
} TCPISPConnectionDataCurve;

typedef struct tagTCPISPConnectionDataArray
{
   unsigned char ucData[1024];
} TCPISPConnectionDataArray;
typedef struct tagTCPISPReservedStructure
{
   unsigned long ulOption1;
   unsigned long ulOption2;
   unsigned long ulOption3;
   unsigned long ulOption4;
   unsigned long ulOption5;
   unsigned long ulOption6;
   unsigned long ulOption7;
   unsigned long ulOption8;
   unsigned long ulOption9;
   unsigned long ulOption10;
   unsigned long ulOption11;
   unsigned long ulOption12;
   unsigned long ulOption13;
   unsigned long ulOption14;
   unsigned long ulOption15;
   unsigned long ulOption16;
   unsigned long ulOption17;
   unsigned long ulOption18;
} TCPISPReservedStructure;
typedef struct tagTCPArpParams
{
	unsigned long	ulClearEntries;
	unsigned long  ulAgingTime;
	unsigned long  ulGetRetries;
	unsigned long  ulGetDelay;
}TCPArpParams;
typedef struct tagTCPArpEntry
{
	unsigned long	ulIpAddress;
	unsigned long  ulMacAddr1_4;
	unsigned short uiMacAddr56;
	unsigned char  ucType;
}TCPArpEntry;
typedef struct tagTCPICMPPing
{
	unsigned long	ulDestIP;
	unsigned long	ulRouterIP;
	unsigned long	ulSourceIP;
	unsigned short	uiTraceRouterNumb;
	unsigned long  ulTraceRouterIndex;
}TCPICMPPing;
typedef struct tagTCPInitStackMode
{
	unsigned long	ulRateThrottle;
}TCPInitStackMode;
typedef struct tagTCPConfigExt
{
	unsigned long ulVIP;
   unsigned char ucDispatchEnable;
   unsigned char ucSMACFilterEnable;
   unsigned short uiSMACFilterValue;
   unsigned short uiHTTPReplyLength;
   unsigned char  ucHTTPReplyCount;
   unsigned char ucReserved;
   unsigned long ulReserved1;
}TCPConfigExt;
typedef struct tagTCPURLOne
{
   char szURL[8 ];
}TCPURLOne;
typedef struct tagTCPURLArray
{
   unsigned short uiNumberOfURL;
   TCPURLOne URL[20 ];
}TCPURLArray;
typedef struct tagTCPURLDistribution
{
   char szURL[8 ];
   unsigned long ulCount;
} TCPURLDistribution;

// # 16 "/usr/local/include/et1000.h" 2
enum LINK_PORT_TYPE{
	INVALID_LINK_PORT = 0,
	COMM_PORT,
	SOCK_PORT
};
typedef struct
	{
	unsigned int Offset;
	unsigned int Range;
	int Filter;
	int Port;
	int BufferMode;
	int TimeTag;
	int Mode;
	} CaptureStructure;
typedef struct tagETCapturePacketInfo
	{
	unsigned long ulPacketNumber;
	unsigned long ulPacketLength;
	unsigned int uiCaptureFlag;
	unsigned char ucReserved[16];
	} ETCapturePacketInfo;
typedef struct
	{
	unsigned int Offset;
	unsigned int Duration;
	unsigned int Count;
	int Mode;
	} CollisionStructure;
typedef struct
	{
	unsigned long ERAEvent;
	unsigned long ERARate;
	unsigned long ERBEvent;
	unsigned long ERBRate;
	unsigned long TXAEvent;
	unsigned long TXARate;
	unsigned long TXBEvent;
	unsigned long TXBRate;
	unsigned long RXAEvent;
	unsigned long RXARate;
	unsigned long RXBEvent;
	unsigned long RXBRate;
	unsigned long CXAEvent;
	unsigned long CXARate;
	unsigned long CXBEvent;
	unsigned long CXBRate;
	unsigned long ALAEvent;
	unsigned long ALARate;
	unsigned long ALBEvent;
	unsigned long ALBRate;
	unsigned long UPAEvent;
	unsigned long UPARate;
	unsigned long UPBEvent;
	unsigned long UPBRate;
	unsigned long OPAEvent;
	unsigned long OPARate;
	unsigned long OPBEvent;
	unsigned long OPBRate;
	unsigned long MFAEvent;
	unsigned long MFARate;
	unsigned long MFBEvent;
	unsigned long MFBRate;
	} CountStructure;
typedef struct
	{
	unsigned long Gap;
	unsigned long Data;
	unsigned int Disp;
	unsigned int Mode;
	int Run;
	int Sel;
	} SwitchStructure;
typedef struct
	{
	unsigned int days;
	unsigned int hours;
	unsigned int minutes;
	unsigned int seconds;
	unsigned int milliseconds;
	unsigned int microseconds;
	} TimeStructure;
typedef struct
	{
	unsigned int Offset;
	int Range;
	int Pattern[12];
	} TriggerStructure;
typedef struct
	{
	unsigned int Offset;
	unsigned int Range;
	int Start[4096];
	int Increment[4096];
	} VFDStructure;
typedef struct
	{
	int Configuration;
	int Range;
	int Offset;
	int* Data;
	int DataCount;
	} HTVFDStructure;
typedef struct
	{
	BOOL AlignError;
	int AlignCount;
	BOOL DribbleError;
	int DribbleCount;
	BOOL CRCError;
	} TErrorStructure;
typedef struct
	{
	unsigned long RcvPkt;
	unsigned long TmtPkt;
	unsigned long Collision;
	unsigned long RcvTrig;
	unsigned long RcvByte;
	unsigned long CRC;
	unsigned long Align;
	unsigned long Oversize;
	unsigned long Undersize;
	unsigned long TmtPktRate;
	unsigned long RcvPktRate;
	unsigned long CRCRate;
	unsigned long OversizeRate;
	unsigned long UndersizeRate;
	unsigned long CollisionRate;
	unsigned long AlignRate;
	unsigned long RcvTrigRate;
	unsigned long RcvByteRate;
	} HTCountStructure;
typedef struct
	{
	unsigned int Offset;
	int Range;
	int Pattern[6];
	} HTTriggerStructure;
typedef struct
	{
	unsigned int Bit_Offset;
	int Bit_Range;
	int Trig_Pattern[6];
	int Bit_Mask[6];
	} TriggerMaskStructure;
typedef struct
	{
	int Range;
	int Offset;
	int iData[12];
	unsigned long ulLatency;
	} HTLatencyStructure;
typedef struct
	{
	int iMode;
	int iPortType;
	unsigned long ulMask1;
	unsigned long ulMask2;
	unsigned long ulData[64];
	} EnhancedCounterStructure;
typedef struct
   {
   int ReleaseType;
   int MajorNumber;
   int MinorNumber;
   int BuildNumber;
   int PatchNumber;
   }FirmwareVersionStructure;
typedef struct
   {
   unsigned short uiReleaseType;
   unsigned short uiMajorNumber;
   unsigned short uiMinorNumber;
   unsigned short uiBuildNumber;
   unsigned char  ucReserved[16];
   }CardFWVersionStructure;
typedef struct tagNSDetailedLibVersionStructure
{
		char szDescription[32 ];
		char szVersion[32 ];
		unsigned short	uiMajor;
		unsigned short	uiMinor;
		unsigned short	uiBuild;
		unsigned char	ucReleaseStage;
		unsigned long	ulCompleteVersion;
} NSDetailedLibVersionStructure;
typedef struct
	{
	int UseMAC;
	int Stations;
	int MACSrc[6];
	int MACDest[6];
	int FramesPerToken;
	int FrameControl;
	} TokenRingMACStructure;
typedef struct
	{
	int UseLLC;
	int DSAP;
	int SSAP;
	int LLCCommand;
	} TokenRingLLCStructure;
typedef struct
	{
	int SpeedSetting;
	int EarlyTokenRelease;
	int DuplexMode;
	int DeviceOrMAUMode;
	} TokenRingPropertyStructure;
typedef struct
	{
	int UseHoldingGap;
	int GapValue;
	int GapScale;
	int UseIntermediateFrameBits;
	int UseAC;
	int ACdata;
	int AdvancedControl1;
	int AdvancedControl2;
	unsigned long AReserved1;
	unsigned long AReserved2;
	} TokenRingAdvancedStructure;
typedef struct
	{
	int EndOrMasterMode;
	int PriorityPromotion;
	int EtherNetOrTokenRing;
	} VGCardPropertyStructure;
// # 1 "/usr/local/include/l3items.h" 1 3
// # 1 "/usr/local/include/stmitems.h" 1 3

typedef struct tagStreamSmartBits
{
	unsigned char   ucActive;
	unsigned char   ucProtocolType;
	unsigned char   ucRandomLength;
	unsigned char   ucRandomData;
	unsigned short  uiFrameLength;
	unsigned short  uiVFD1Offset;
	unsigned char   ucVFD1Range;
	unsigned char   ucVFD1Pattern;
	unsigned long   ulVFD1PatternCount;
	unsigned char   ucVFD1StartVal[6];
	unsigned short  uiVFD2Offset;
	unsigned char   ucVFD2Range;
	unsigned char   ucVFD2Pattern;
	unsigned long   ulVFD2PatternCount;
	unsigned char   ucVFD2StartVal[6];
	unsigned short  uiVFD3Offset;
	unsigned short  uiVFD3Range;
	unsigned char   ucVFD3Enable;
	unsigned char   ucTagField;
	unsigned char   ProtocolHeader[64];
} StreamSmartBits;
typedef struct tagStream8023
{
	unsigned char   ucActive;
	unsigned char   ucProtocolType;
	unsigned char   ucRandomLength;
	unsigned char   ucRandomData;
	unsigned short  uiFrameLength;
	unsigned short  uiVFD1Offset;
	unsigned char   ucVFD1Range;
	unsigned char   ucVFD1Pattern;
	unsigned long   ulVFD1PatternCount;
	unsigned char   ucVFD1StartVal[6];
	unsigned short  uiVFD2Offset;
	unsigned char   ucVFD2Range;
	unsigned char   ucVFD2Pattern;
	unsigned long   ulVFD2PatternCount;
	unsigned char   ucVFD2StartVal[6];
	unsigned short  uiVFD3Offset;
	unsigned short  uiVFD3Range;
	unsigned char   ucVFD3Enable;
	unsigned char   ucTagField;
	unsigned char   ProtocolHeader[64];
} Stream8023;
typedef struct tagStreamIP
{
	unsigned char   ucActive;
	unsigned char   ucProtocolType;
	unsigned char   ucRandomLength;
	unsigned char   ucRandomData;
	unsigned short  uiFrameLength;
	unsigned short  uiVFD1Offset;
	unsigned char   ucVFD1Range;
	unsigned char   ucVFD1Pattern;
	unsigned long   ulVFD1PatternCount;
	unsigned char   ucVFD1StartVal[6];
	unsigned short  uiVFD2Offset;
	unsigned char   ucVFD2Range;
	unsigned char   ucVFD2Pattern;
	unsigned long   ulVFD2PatternCount;
	unsigned char   ucVFD2StartVal[6];
	unsigned short  uiVFD3Offset;
	unsigned short  uiVFD3Range;
	unsigned char   ucVFD3Enable;
	unsigned char   ucTagField;
	unsigned char  DestinationMAC[6];
	unsigned char  SourceMAC[6];
	unsigned char  TypeOfService;
	unsigned char  TimeToLive;
	unsigned short InitialSequenceNumber;
	unsigned char  DestinationIP[4];
	unsigned char  SourceIP[4];
	unsigned char  Netmask[4];
	unsigned char  Gateway[4];
	unsigned char  Protocol;
	unsigned char  extra[17];
	unsigned short uiActualSequenceNumber;
	unsigned long  ulARPStart;
	unsigned long  ulARPEnd;
	unsigned long  ulARPGap;
} StreamIP;
typedef struct tagStreamIPVLAN
 {
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned char  Protocol;
 unsigned char  reserved[5];
 unsigned short VLAN_Pri;
 unsigned short VLAN_Cfi;
 unsigned short VLAN_Vid;
 unsigned char  extra[12];
 unsigned long  ulARPStart;
 unsigned long  ulARPEnd;
 unsigned long  ulARPGap;
 } StreamIPVLAN;
typedef struct tagStreamUDP
 {
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short UDPSrc;
 unsigned short UDPDest;
 unsigned short UDPLen;
 unsigned char  extra[12];
 unsigned short uiActualSequenceNumber;
 unsigned long  ulARPStart;
 unsigned long  ulARPEnd;
 unsigned long  ulARPGap;
 } StreamUDP;
typedef struct tagStreamUDPVLAN
 {
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short UDPSrc;
 unsigned short UDPDest;
 unsigned short UDPLen;
 unsigned short VLAN_Pri;
 unsigned short VLAN_Cfi;
 unsigned short VLAN_Vid;
 unsigned char  extra[12];
 unsigned long  ulARPStart;
 unsigned long  ulARPEnd;
 unsigned long  ulARPGap;
 } StreamUDPVLAN;
typedef struct tagStreamIPX
 {
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char   DestinationMAC[6];
 unsigned char   SourceMAC[6];
 unsigned short  IPXlen;
 unsigned char   IPXhop;
 unsigned char   IPXtype;
 unsigned char   IPXdst[4];
 unsigned char   IPXdstHost[6];
 unsigned short  IPXdstSocket;
 unsigned char   IPXsrc[4];
 unsigned char   IPXsrcHost[6];
 unsigned short  IPXsrcSocket;
 unsigned char   extra[24];
 } StreamIPX;
 typedef struct tagStreamTCP
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short SourcePort;
 unsigned short DestPort;
 unsigned short Window;
 unsigned char  reserved[2];
 unsigned long  TCPAck;
 unsigned long  TCPSequence;
 unsigned char  Flags;
 unsigned char  extra[3];
 unsigned long 	ulARPOut;
 unsigned long 	ulARPBack;
 unsigned long 	ulARPGap;
	} StreamTCP;
 typedef struct tagStreamTCPVLAN
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short SourcePort;
 unsigned short DestPort;
 unsigned short Window;
 unsigned short VLAN_Pri;
 unsigned short VLAN_Cfi;
 unsigned short VLAN_Vid;
 unsigned long  TCPAck;
 unsigned long  TCPSequence;
 unsigned char  Flags;
 unsigned char  Spare[3];
			unsigned long 	ulARPOut;
 unsigned long 	ulARPBack;
 unsigned long 	ulARPGap;
	} StreamTCPVLAN;
 typedef struct tagStreamSmartTCP
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short SourcePort;
 unsigned short DestPort;
 unsigned short TCPLength;
 unsigned short Sequence_acc;
 unsigned long  PartialChecksum;
 unsigned long  TCPSequence;
 unsigned short Window;
 unsigned char  Flags;
 unsigned char  Spare;
 unsigned long    ulARPOut;
 unsigned long 	ulARPBack;
 unsigned long 	ulARPGap;
	} StreamSmartTCP;
 typedef struct tagStreamICMP
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned char  ucType;
 unsigned char  ucCode;
 unsigned short uiIdentifier;
 unsigned char  extra[16];
 unsigned long  ulARPOut;
 unsigned long  ulARPBack;
 unsigned long  ulARPGap;
	} StreamICMP;
 typedef struct tagStreamRTP
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char    DestinationMAC[6];
 unsigned char	   SourceMAC[6];
 unsigned char	   TypeOfService;
 unsigned char	   TimeToLive;
 unsigned short	InitialSequenceNumber;
 unsigned char	   DestinationIP[4];
 unsigned char	   SourceIP[4];
 unsigned char	   Netmask[4];
 unsigned char	   Gateway[4];
 unsigned short	UDPSrc;
 unsigned short	UDPDest;
 unsigned short	UDPLen;
 unsigned char    extra1[2];
 unsigned long		RTPSyncSource;
 unsigned char		RTPPayloadType;
 unsigned char	   extra2[19];
 } StreamRTP;
 typedef struct tagStreamRTPVLAN
	{
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char 	DestinationMAC[6];
 unsigned char   	SourceMAC[6];
 unsigned char   	TypeOfService;
 unsigned char   	TimeToLive;
 unsigned short	InitialSequenceNumber;
 unsigned char	  	DestinationIP[4];
 unsigned char	  	SourceIP[4];
 unsigned char	  	Netmask[4];
 unsigned char	  	Gateway[4];
 unsigned short	UDPSrc;
 unsigned short	UDPDest;
 unsigned short	UDPLen;
 unsigned long		RTPSyncSource;
 unsigned char		RTPPayloadType;
 unsigned short VLAN_Pri;
 unsigned short VLAN_Cfi;
 unsigned short VLAN_Vid;
 unsigned char	  	extra[19];
 } StreamRTPVLAN;
typedef struct tagRTPCounterInfo
{
   unsigned long  ulStreamNumber;
   unsigned long  ulFrameCount;
   unsigned long  ulReserved[4];
}RTPCounterInfo;
typedef struct tagStreamUDPDHCP
 {
 unsigned char   ucActive;
 unsigned char   ucProtocolType;
 unsigned char   ucRandomLength;
 unsigned char   ucRandomData;
 unsigned short  uiFrameLength;
 unsigned short  uiVFD1Offset;
 unsigned char   ucVFD1Range;
 unsigned char   ucVFD1Pattern;
 unsigned long   ulVFD1PatternCount;
 unsigned char   ucVFD1StartVal[6];
 unsigned short  uiVFD2Offset;
 unsigned char   ucVFD2Range;
 unsigned char   ucVFD2Pattern;
 unsigned long   ulVFD2PatternCount;
 unsigned char   ucVFD2StartVal[6];
 unsigned short  uiVFD3Offset;
 unsigned short  uiVFD3Range;
 unsigned char   ucVFD3Enable;
 unsigned char   ucTagField;
 unsigned char  DestinationMAC[6];
 unsigned char  SourceMAC[6];
 unsigned char  TypeOfService;
 unsigned char  TimeToLive;
 unsigned short InitialSequenceNumber;
 unsigned char  DestinationIP[4];
 unsigned char  SourceIP[4];
 unsigned char  Netmask[4];
 unsigned char  Gateway[4];
 unsigned short UDPSrc;
 unsigned short UDPDest;
 unsigned short UDPLen;
 unsigned char  DHCPRelayIP[4];
 unsigned char  DHCPAction;
 unsigned char  DHCPState;
 unsigned char  extra[6];
 unsigned short uiActualSequenceNumber;
 unsigned long  ulARPStart;
 unsigned long  ulARPEnd;
 unsigned long  ulARPGap;
 } StreamUDPDHCP;

// # 14 "/usr/local/include/l3items.h" 2 3
typedef struct tagLayer3DHCPStatsInfo
{
   unsigned long   ulStreamNumber;
   unsigned short  uiFailure;
   unsigned short  uiTimeout;
   unsigned short  uiDiscoverSent;
   unsigned short  uiOfferRcvd;
   unsigned short  uiReqSent;
   unsigned short  uiAckRcvd;
   unsigned short  uiNakRcvd;
   unsigned short  uiReleaseSent;
   unsigned short  uiDeclineSent;
   unsigned short  uiReserved;
} Layer3DHCPStatsInfo;
typedef struct tagLayer3DHCPHostInfo
{
   unsigned long  ulStreamNumber;
   unsigned char  ucHostIP[4];
   unsigned char  ucServerIP[4];
   unsigned char  ucServerMAC[6];
   unsigned char  ucReserved[2];
   unsigned char  ucGateway[4];
   unsigned char  ucSubnet[4];
   unsigned short uiState;
   unsigned short uiReserved;
   unsigned long  ulTime;
} Layer3DHCPHostInfo;
typedef struct tagLayer3DHCPExtendedHostInfo
{
   unsigned long  ulStreamNumber;
   unsigned char  ucHostIP[4];
   unsigned char  ucServerIP[4];
   unsigned char  ucServerMAC[6];
   unsigned char  ucReserved[2];
   unsigned char  ucGateway[4];
   unsigned char  ucSubnet[4];
   unsigned short uiState;
   unsigned char  ucReserved2[2];
   unsigned long  ulTime;
   unsigned char  szServerName[64];
   unsigned char  szFileName[128];
   unsigned char  ucOption[312];
} Layer3DHCPExtendedHostInfo;
typedef struct tagLayer3DHCPConfig
{
   unsigned long ulRate;
   unsigned long ulReserved[6];
} Layer3DHCPConfig;
typedef struct tagUSBInfo
 {
 unsigned char szUSBMAC[6];
 } USBInfo;
typedef struct tagUSBProtocolPower
{
 unsigned char ucProtocol;
 unsigned char ucPower;
}USBProtocolPower;
typedef struct tagLayer3GroupInfo
{
	unsigned long  ulReserved;
	unsigned char  ucGroupId;
	unsigned long  ulFrameLength;
	unsigned long  ulFrameGap;
	unsigned short uiNumberOfStreams;
   unsigned short uiNumberOfFrames;
	unsigned short uiMembers[100 ];
} Layer3GroupInfo;
typedef struct tagLayer3StreamGroup
{
	unsigned long  ulFrameLength;
	unsigned long  ulFrameGap;
	unsigned short uiNumberOfStreams;
	unsigned short uiMembers[100 ];
} Layer3StreamGroup;
typedef struct tagLayer3StreamTransmitMode
{
	unsigned long  ulMode;
	unsigned long  ulReserved[3];
} Layer3StreamTransmitMode;
typedef struct tagLayer3ModifyStreamDelta
 {
 unsigned long ulIndex;
 unsigned long ulCount;
 unsigned long ulField;
 unsigned long ulFieldRepeat;
 unsigned long ulDelta;
 } Layer3ModifyStreamDelta;
typedef struct tagLayer3ModifyStreamArray
 {
 unsigned long ulIndex;
 unsigned long ulCount;
 unsigned long ulField;
 unsigned long ulFieldCount;
 unsigned long ulFieldRepeat;
 unsigned long ulData[8192 ];
 } Layer3ModifyStreamArray;
typedef struct tagLayer3Address
 {
 unsigned char szMACAddress[6];
 unsigned char IP[4];
 unsigned char Netmask[4];
 unsigned char Gateway[4];
 unsigned char PingTargetAddress[4];
 int iControl;
 int iPingTime;
 int iSNMPTime;
 int iRIPTime;
 int iGeneralIPResponse;
 } Layer3Address;
typedef struct tagLayer3CaptureCountInfo
 {
 unsigned long ulCount;
 } Layer3CaptureCountInfo;
typedef struct tagLayer3CaptureData
	{
	unsigned short uiLength;
	char cData[2048];
	} Layer3CaptureData;
typedef struct tagLayer3CaptureDetailInfo
   {
   unsigned long   ulStatus;
   unsigned long   ulPacketLength;
   unsigned long   ulRxTimestamp;
   unsigned long   ulTxTimestamp;
   unsigned long   ulSequenceNumber;
   unsigned long   ulStreamNumber;
   unsigned char   reserved[96];
 } Layer3CaptureDetailInfo;
typedef struct tagLayer3CaptureSetup
{
   unsigned long  ulCaptureMode;
   unsigned long  ulCaptureLength;
   unsigned long  ulCaptureEvents;
   unsigned char  ucReserved[12];
} Layer3CaptureSetup;
typedef struct tagLayer3SequenceInfo
 {
 unsigned long ulStream;
 unsigned long ulFrames;
 unsigned long ulSequenced;
 unsigned long ulDuplicate;
 unsigned long ulLost;
 } Layer3SequenceInfo;
typedef struct tagLayer3LatencyInfo
 {
 unsigned short uiMinimum;
 unsigned short uiMaximum;
 unsigned long  ulTotal;
 unsigned long  ulFrames;
 } Layer3LatencyInfo;
typedef struct tagLayer3LongLatencyInfo
 {
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 U64           u64Total;
 unsigned long ulFrames;
 } Layer3LongLatencyInfo;
typedef struct tagLayer3StreamLatencyInfo
 {
 unsigned long  ulStream;
 unsigned short uiAverage;
 unsigned short uiMinimum;
 unsigned short uiMaximum;
 unsigned long  ulFrames;
 } Layer3StreamLatencyInfo;
typedef struct tagLayer3StreamLatencyInfo32
 {
 unsigned long  ulStream;
 unsigned long  ulFrames;
 U64            u64Total;
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 } Layer3StreamLatencyInfo32;
typedef Layer3StreamLatencyInfo32 Layer3V1StreamLatencyInfo;
typedef struct tagLayer3StreamLongLatencyInfo
 {
 unsigned long ulStream;
 U64           u64Total;
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 unsigned long ulTotalFrames;
 unsigned long ulSequenced;
 unsigned long ulDuplicate;
 unsigned long ulLost;
 unsigned long ulFrames[16];
 } Layer3StreamLongLatencyInfo;
typedef struct tagLayer3StreamJitterComboInfo
 {
 unsigned long ulStream;
 U64           u64Total;
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 unsigned long ulTotalFrames;
 U64           u64TotalJitter;
 unsigned long ulReserved;
 unsigned long ulFrames[16];
 } Layer3StreamJitterComboInfo;
typedef struct tagLayer3StreamMulticastInfo
 {
 unsigned long	ulStream;
 U64           u64Total;
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 unsigned long ulRxFrames;
 unsigned long ulFirstRxTime;
 unsigned long ulLastRxTime;
 unsigned long ulReserved;
 unsigned long ulFrames[16];
 } Layer3StreamMulticastInfo;
typedef struct tagLayer3StreamDistributionInfo
 {
 unsigned long ulStream;
 unsigned long ulFrames[16];
 } Layer3StreamDistributionInfo;
typedef struct tagLayer3HistTagInfo
 {
 unsigned long ulStream;
 unsigned long ulSequence;
 unsigned long ulTransmitTime;
 unsigned long ulReceiveTime;
 } Layer3HistTagInfo;
typedef struct tagLayer3HistLatency
 {
 unsigned long ulInterval;
 } Layer3HistLatency;
typedef struct tagLayer3HistDistribution
 {
 unsigned short uiInterval[16];
 } Layer3HistDistribution;
typedef struct tagLayer3V2HistDistribution
 {
 unsigned long ulInterval[16];
 } Layer3V2HistDistribution;
typedef struct tagLayer3HistActiveTest
	{
	unsigned long ulTest;
	unsigned long ulRecords;
	} Layer3HistActiveTest;
typedef struct tagLayer3IGMPInit
{
	unsigned char	ucVersion;
   unsigned char	ucOptions;
	unsigned short	uiMaxGroups;
} Layer3IGMPInit;
typedef struct tagLayer3IGMPJoin
{
 unsigned char ucIPAddress[4];
} Layer3IGMPJoin;
typedef struct tagLayer3IGMPLeave
{
 unsigned char ucIPAddress[4];
} Layer3IGMPLeave;
typedef struct tagIGMPJoinLeaveTimeStampInfo
{
 unsigned char ucIPAddress[4];
 unsigned long ulJoinTime;
 unsigned long ulLeaveTime;
} IGMPJoinLeaveTimeStampInfo;
typedef struct tagL3DataCheck
{
		unsigned char	bRcvMarkerCheck;
		unsigned char	ucReserved[3];
		unsigned char   ucMarker[8];
} L3DataCheck;
typedef struct tagL3StreamExtension
{
		unsigned long	ulFrameRate;
		unsigned long	ulTxMode;
		unsigned long	ulBurstCount;
		unsigned long	ulMBurstCount;
		unsigned long	ulBurstGap;
		unsigned short	uiInitialSeqNumber;
		unsigned char	ucIPHeaderChecksumError;
		unsigned char	ucIPTotalLengthError;
		unsigned char	ucIPManipulateMode;
		unsigned char	ucIncUDPPort;
		unsigned short	uiIPLimitCount;
		unsigned long	ulStartOffset;
		unsigned long	ulBGPatternIndex;
		unsigned char	ucDataCheckEnable;
		unsigned char	ucCRCErrorEnable;
		unsigned char	ucRandomBGEnable;
		unsigned char	ucDataIntegrityErrorEnable;
		unsigned char  ucStepCount;
		unsigned char  ucIPBitsOffset;
		unsigned char  ucMPLSCount;
		unsigned char	ucIPOptionsCount;
		unsigned long	ulCustomStreamID;
		unsigned char	ucEnableCustomStreamID;
		unsigned char	ucReserved[11];
} L3StreamExtension;
typedef struct tagMPLSItem
{
   unsigned long  ulLabel;
   unsigned char  ucExperimentalUse;
   unsigned char  ucBottomStack;
   unsigned char  ucTimeToLive;
}MPLSItem;
typedef struct tagNSMPLSLabel
{
   unsigned long  ulLabel;
   unsigned char  ucExperimentalUse;
   unsigned char  ucBottomStack;
   unsigned char  ucTimeToLive;
}NSMPLSLabel;
typedef struct tagNSMPLSList
{
   unsigned short uiNumLabels;
   NSMPLSLabel Labels[32];
}NSMPLSList;
typedef struct tagVoiceTestSetup
{
   unsigned long  ulTestDuration;
   unsigned long  ulReserved[7];
}VoiceTestSetup;
typedef struct tagL3StreamBGConfig
{
	unsigned char	ucPattern[64];
} L3StreamBGConfig;
typedef struct tagNSVFD
{
		unsigned char 	ucType;
		unsigned char	ucMode;
		unsigned short	uiOffset;
		unsigned short	uiRange;
		unsigned long	ulCycleCount;
		unsigned short	uiBlockCount;
		unsigned char	ucStepValue;
		unsigned char	ucStepShift;
		unsigned char 	ucSubnetAware;
		unsigned char	ucSubnetMaskLength;
		unsigned char	ucEnableCarryChaining;
		unsigned char	ucPattern[6];
		unsigned char	ucReserved[16];
} NSVFD;
typedef struct tagL3ModifyStream
	{
	unsigned long		ulIndex;
	unsigned long		ulCount;
	unsigned long		ulField;
	unsigned long		ulFieldCount;
	unsigned long		ulDelta;
	} L3ModifyStream;
typedef struct tagL3ModifyStreamArray
	{
	unsigned long		ulIndex;
	unsigned long		ulCount;
	unsigned long		ulField;
	unsigned long		ulFieldCount;
	unsigned long     ulFieldRepeat;
	unsigned long		ulData[8192 ];
	} L3ModifyStreamArray;
typedef struct tagLayer3_Tracking_Latency
	{
	unsigned long ulInterval;
	} Layer3_Tracking_Latency;
typedef struct tagLayer3_Tracking_Distribution
	{
	unsigned short uiInterval[16];
	} Layer3_Tracking_Distribution;
typedef struct tagLayer3_V2_Tracking_Distribution
	{
	unsigned long ulInterval[16];
	} Layer3_V2_Tracking_Distribution;
typedef struct tagLayer3_TrackingActiveTest
	{
	unsigned long ulTest;
	unsigned long ulRecords;
	} Layer3_TrackingActiveTest;
typedef struct tagLayer3TagInfo
	{
	unsigned long ulStream;
	unsigned long ulSequence;
	unsigned long ulTransmitTime;
	unsigned long ulReceiveTime;
	} Layer3TagInfo;
typedef struct tagLayer3TrackingLatency
	{
	unsigned long ulInterval;
	} Layer3TrackingLatency;
typedef struct tagLayer3TrackingDistribution
	{
	unsigned short uiInterval[16];
	} Layer3TrackingDistribution;
typedef struct tagLayer3V2TrackingDistribution
	{
	unsigned long ulInterval[16];
	} Layer3V2TrackingDistribution;
typedef struct tagLayer3TrackingActiveTest
	{
	unsigned long ulTest;
	unsigned long ulRecords;
	} Layer3TrackingActiveTest;
typedef struct tagLayer3MulticastCounters
	{
	unsigned long   ulTxFrames;
   unsigned long   ulTxJoinGroups;
   unsigned long   ulTxLeaveGroups;
   unsigned long   ulRxFrames;
   unsigned long   ulRxUnknownType;
   unsigned long   ulRxIpChecksumErrors;
   unsigned long   ulRxIgmpChecksumErrors;
   unsigned long   ulRxIgmpLengthErrors;
   unsigned long   ulRxWrongVersionQueries;
   unsigned char   reserved[96];
	} Layer3MulticastCounters;
typedef struct tagL3StatsInfo{
	U64				u64RxVlanFrames;
	U64				u64RxIPFrames;
	U64				u64IPChecksumError;
	unsigned long	ulArpReplySent;
	unsigned long	ulArpReplyRecv;
	unsigned long	ulArpRequestSent;
	unsigned long	ulArpRequestRecv;
	unsigned long	ulPingReplySent;
	unsigned long	ulPingReplyRecv;
	unsigned long	ulPingRequestSent;
	unsigned long	ulPingRequestRecv;
	unsigned long	ulRxStackCount;
	unsigned long	ulTxStackCount;
   U64            u64RxDataIntegrityError;
   U64            u64RxSignatureFrames;
   U64            u64TxSignatureFrames;
	unsigned long	ulReserved[2];
} L3StatsInfo;

// # 1268 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/atmitems.h" 1 3
// # 1 "/usr/local/include/wanitems.h" 1 3
// # 14 "/usr/local/include/atmitems.h" 2 3

typedef struct tagATMAddress
{
	unsigned char	ucPrefix[13];
	unsigned char	ucEsi[6];
	unsigned char	ucSel;
} ATMAddress;
typedef struct tagATMLineParams
{
	unsigned char ucFramingMode;
	unsigned char ucTxClockSource;
	unsigned char ucCellScrambling;
	unsigned char ucHecCoset;
	unsigned char ucRxErroredCells;
	unsigned char ucLoopbackEnable;
	unsigned char ucIdleCellHeader[4];
} ATMLineParams;
typedef struct tagATMDS3E3LineParams
{
	unsigned char ucFramingMode;
	unsigned char ucTxClockSource;
	unsigned char ucCellScrambling;
	unsigned char ucHecCoset;
	unsigned char ucRxErroredCells;
	unsigned char ucLoopbackEnable;
	unsigned char ucLineBuildout;
	unsigned char ucIdleCellHeader[4];
} ATMDS3E3LineParams;
typedef struct tagATMDS1E1LineParams
{
	unsigned char	ucFramingMode;
	unsigned char	ucTxClockSource;
	unsigned char	ucCellScrambling;
	unsigned char	ucHecCoset;
	unsigned char	ucRxErroredCells;
	unsigned char	ucLoopbackEnable;
	unsigned char	ucLineBuildout;
	unsigned char	ucLineCoding;
	unsigned char	ucLineFraming;
	unsigned char	ucIdleCellHeader[4];
} ATMDS1E1LineParams;
typedef long ATMCellTime;
typedef struct tagATMStream
{
	unsigned short	uiIndex;
	unsigned char	ucConnType;
	unsigned char	ucEncapType;
	unsigned char	ucGenRateClass;
	unsigned long	ulGenPCR;
	unsigned long	ulGenSCR;
	unsigned long	ulGenMBS;
	ATMCellTime		ctGenCDVT;
	unsigned char	ucFwdTdType;
	unsigned long	ulFwdPCR0;
	unsigned long	ulFwdPCR01;
	unsigned long	ulFwdSCR0;
	unsigned long	ulFwdSCR01;
	unsigned long	ulFwdMBS0;
	unsigned long	ulFwdMBS01;
	unsigned char	ucBwdTdType;
	unsigned long	ulBwdPCR0;
	unsigned long	ulBwdPCR01;
	unsigned long	ulBwdSCR0;
	unsigned long	ulBwdSCR01;
	unsigned long	ulBwdMBS0;
	unsigned long	ulBwdMBS01;
	unsigned char	ucFwdQoS;
	unsigned char	ucBwdQoS;
	unsigned char	ucBcClass;
	unsigned char	ucTimingReq;
	unsigned char	ucTrafficType;
	unsigned char	ucClipping;
	unsigned long	ulCellHeader;
	unsigned char	ucDestAtmAddr[20];
	unsigned char	ucDestMacAddr[6];
	unsigned char	ucDestIpAddr[4];
	unsigned char	ucSnapHeader[5];
	unsigned char	ucElanInst;
} ATMStream;
typedef struct tagATMFrameDefinition
{
	unsigned short	uiStreamIndex;
	unsigned short	uiFrameLength;
	unsigned short	uiDataLength;
	unsigned short	uiFrameFillPattern;
	unsigned long	ulFrameFlags;
	unsigned char	ucFrameData[2048];
} ATMFrameDefinition;
typedef struct tagATMConnection
{
	unsigned long 	ulIndex;
	unsigned char	ucType;
	unsigned char	ucRateClass;
	unsigned long	ulRatePCR;
	unsigned long	ulRateSCR;
	unsigned long	ulRateMBS;
	ATMCellTime		ctCellDelayVar;
	unsigned long	ulCellHeader;
	unsigned short	uiCallSetupIndex;
	unsigned short	uiAddressIndex;
	unsigned char	ucCallDistType;
	unsigned char	ucCallLengthType;
	unsigned char	ucStopOnError;
	unsigned char	ucLogEvents;
	unsigned char	ucEnableCellLoadGen;
	unsigned long	ulCallStartDelay;
	unsigned long	ulCallCountLimit;
	unsigned long	ulCallLength;
	unsigned long	ulRandomLengthDelta;
	unsigned long	ulInterCallGap;
	unsigned long	ulRandomGapDelta;
	unsigned long	ulBurstCount;
	unsigned long	ulInterBurstGap;
} ATMConnection;
typedef struct tagATMConnectionEx
{
	unsigned long 	ulIndex;
	unsigned char	ucType;
	unsigned char	ucRateClass;
	unsigned long	ulRatePCR;
	unsigned long	ulRateSCR;
	unsigned long	ulRateMBS;
	ATMCellTime		ctCellDelayVar;
	unsigned long	ulCellHeader;
	unsigned short	uiCallSetupIndex;
	unsigned short	uiAddressIndex;
	unsigned char	ucCallDistType;
	unsigned char	ucCallLengthType;
	unsigned char	ucStopOnError;
	unsigned char	ucLogEvents;
	unsigned char	ucEnableCellLoadGen;
	unsigned long	ulCallStartDelay;
	unsigned long	ulCallCountLimit;
	unsigned long	ulCallLength;
	unsigned long	ulRandomLengthDelta;
	unsigned long	ulInterCallGap;
	unsigned long	ulRandomGapDelta;
	unsigned long	ulBurstCount;
	unsigned long	ulInterBurstGap;
	unsigned long	ulRateMCR;
} ATMConnectionEx;
typedef struct tagATMConnectionCopyParams
{
	unsigned long ulSrcIndex;
	unsigned long ulDstIndex;
	unsigned long ulCount;
} ATMConnectionCopyParams;
typedef struct tagATMConnectionModify
{
	unsigned long	ulSrcIndex;
	unsigned long	ulCount;
	unsigned long	ulType;
	long		      lDelta;
} ATMConnectionModify;
typedef struct tagATMConnectionModifyArray
{
	unsigned long		ulSrcIndex;
	unsigned long		ulCount;
	unsigned long		ulID;
	unsigned long		ulArraySize;
	unsigned long		ulValues[2048 ];
} ATMConnectionModifyArray;
typedef struct 	tagATMCallSetupParams
{
	unsigned short	uiCallSetupIndex;
	unsigned long	ulFwdTrafficDescriptorType;
	unsigned long	ulFwdPCR_0;
	unsigned long	ulFwdPCR_01;
	unsigned long	ulFwdSCR_0;
	unsigned long	ulFwdSCR_01;
	unsigned long	ulFwdMBS_0;
	unsigned long	ulFwdMBS_01;
	unsigned long	ulBwdTrafficDescriptorType;
	unsigned long	ulBwdPCR_0;
	unsigned long	ulBwdPCR_01;
	unsigned long	ulBwdSCR_0;
	unsigned long	ulBwdSCR_01;
	unsigned long	ulBwdMBS_0;
	unsigned long	ulBwdMBS_01;
	unsigned char	ucFwdQOS;
	unsigned char	ucBwdQOS;
	unsigned char	ucBbcClass;
	unsigned char	ucBbcTimingReq;
	unsigned char	ucBbcTrafficType;
	unsigned char	ucBbcSusceptibleToClipping;
} ATMCallSetupParams;
typedef struct tagATMCallSetupParamsEx
{
	unsigned short	uiCallSetupIndex;
	unsigned long	ulFwdTrafficDescriptorType;
	unsigned long	ulFwdPCR_0;
	unsigned long	ulFwdPCR_01;
	unsigned long	ulFwdSCR_0;
	unsigned long	ulFwdSCR_01;
	unsigned long	ulFwdMBS_0;
	unsigned long	ulFwdMBS_01;
	unsigned long	ulBwdTrafficDescriptorType;
	unsigned long	ulBwdPCR_0;
	unsigned long	ulBwdPCR_01;
	unsigned long	ulBwdSCR_0;
	unsigned long	ulBwdSCR_01;
	unsigned long	ulBwdMBS_0;
	unsigned long	ulBwdMBS_01;
	unsigned char	ucFwdQOS;
	unsigned char	ucBwdQOS;
	unsigned char	ucBbcClass;
	unsigned char	ucBbcTimingReq;
	unsigned char	ucBbcTrafficType;
	unsigned char	ucBbcSusceptibleToClipping;
	unsigned long	ulFwdMCR_01;
	unsigned long	ulBwdMCR_01;
	unsigned char	ucATC;
	unsigned char	ucATC_present;
	unsigned char	ucInc;
	unsigned long	ulRM_FRTT;
	unsigned long	ulFwdICR_01;
	unsigned long	ulFwdTBE_01;
	unsigned long	ulFwdRIF_01;
	unsigned long	ulFwdRDF_01;
	unsigned long	ulBwdICR_01;
	unsigned long	ulBwdTBE_01;
	unsigned long	ulBwdRIF_01;
	unsigned long	ulBwdRDF_01;
	 unsigned char ucFwdNrm_present;
	 unsigned char ucFwdTrm_present;
	 unsigned char ucFwdCdf_present;
	 unsigned char ucFwdAdtf_present;
	 unsigned short usFwdNrm;
	 unsigned short usFwdTrm;
	 unsigned short usFwdCdf;
	 unsigned short usFwdAdtf;
	 unsigned char ucBwdNrm_present;
	 unsigned char ucBwdTrm_present;
	 unsigned char ucBwdCdf_present;
	 unsigned char ucBwdAdtf_present;
	 unsigned short usBwdNrm;
	 unsigned short usBwdTrm;
	 unsigned short usBwdCdf;
	 unsigned short usBwdAdtf;
	 unsigned char ucEnableABRSetupParam;
	 unsigned char ucEnableABRAddlParam;
} ATMCallSetupParamsEx;
typedef struct	tagATMCallAddrList
{
	unsigned short		uiStartAddrIndex;
	unsigned short		uiCount;
	ATMAddress        atmAddress[128 ];
} ATMCallAddrList;
typedef struct tagATMILMIParams
{
	unsigned long	ulColdStartTimer;
	unsigned long	ulRegTimeoutTimer;
	unsigned char	ucESI[6];
} ATMILMIParams;
typedef struct tagATMILMIStaticParams
{
	 ATMAddress		atmAddress;
} ATMILMIStaticParams;
typedef struct tagATMSSCOPParams
{
	unsigned long	ulMaxCC;
	unsigned long	ulMaxPD;
	unsigned long	ulMaxStat;
	unsigned long	ulMaxReseq;
	unsigned long	ulRxWindow;
	unsigned long	ulTmrCC;
	unsigned long	ulTmrKeepAlive;
	unsigned long	ulTmrNoResp;
	unsigned long	ulTmrPoll;
	unsigned long	ulTmrIdle;
} ATMSSCOPParams;
typedef struct tagATMUNIParams
{
	unsigned long	ulVer;
	unsigned long	ulTmrT303;
	unsigned long	ulTmrT308;
	unsigned long	ulTmrT310;
	unsigned long	ulTmrT313;
	unsigned long	ulTmrT322;
	unsigned long	ulTmrT398;
	unsigned long	ulTmrT399;
	unsigned long	ulTmrT309;
	unsigned long	ulTmrT316;
	unsigned long	ulTmrT317;
	unsigned long  ulTmrTeardown;
} ATMUNIParams;
typedef struct tagATMELANRegister
{
	unsigned char		ucInstance;
	unsigned char		ucInitMethod;
	ATMAddress			ManualAtmAddr;
	unsigned char		ucC2Type;
	unsigned char		ucC3Mtu;
	unsigned char		ucC5Name[32 ];
	unsigned char		ucC6MacAddr[6];
	unsigned short		uiC7ControlTimeout;
	unsigned short		uiC13ArpRetryCount;
	unsigned short		uiC20ArpResponseTime;
} ATMELANRegister;
typedef struct tagATMELANDeregister
{
	unsigned char		ucInstance;
} ATMELANDeregister;
typedef struct tagATMClassicalIP
{
	unsigned char		ucArpServerAtmAddr[20];
	unsigned char		ucArpClientIpAddr[4];
	unsigned long		ulInterArpGap;
	unsigned long		ulInterCallGap;
	unsigned short		uiArpRetries;
	unsigned char		ucInvArpReplyOff;
} ATMClassicalIP;
typedef struct tagATMStartCardSetupParams
{
	unsigned long		ulConnIndex;
	unsigned long		ulCount;
} ATMStartCardSetupParams;
typedef struct tagATMStopCardSetupParams
{
	unsigned long		ulConnIndex;
	unsigned long		ulCount;
	unsigned char		ucStopNewCalls;
	unsigned char		ucStopCellLoadGen;
	unsigned char		ucTeardownCalls;
} ATMStopCardSetupParams;
typedef struct	tagATMStreamControl
{
	unsigned char		ucAction;
	unsigned long		ulStreamIndex;
	unsigned long		ulStreamCount;
} ATMStreamControl;
typedef struct tagATMTrigger
{
	unsigned char		ucEnable;
	unsigned char		ucMode;
	unsigned char		ucDirection;
	unsigned char		ucCompCombo;
	unsigned char		ucHeaderNoMatch;
	unsigned char		ucComp1NoMatch;
	unsigned char		ucComp2NoMatch;
	unsigned long		ulHeaderPattern;
	unsigned long		ulHeaderMask;
	unsigned short		uiComp1Offset;
	unsigned short		uiComp1Range;
	unsigned char		ucComp1Pattern[6];
	unsigned char		ucComp1Mask[6];
	unsigned short		uiComp2Offset;
	unsigned short		uiComp2Range;
	unsigned char		ucComp2Pattern[6];
	unsigned char		ucComp2Mask[6];
} ATMTrigger;
typedef struct tagATMGlobalTrigger
{
	 unsigned char	    ucEnable;
	 unsigned char     ucCompCombo;
	 unsigned long	    ulComp2Pattern;
	 unsigned short	 uiComp1Offset;
	 unsigned short    uiComp2Offset;
	 unsigned long	    ulComp1Mask;
	 unsigned long     ulComp2Mask;
} ATMGlobalTrigger;
typedef struct tagATMConnTriggerParams
{
	 unsigned short    uiConnIndex;
	 unsigned long	    ulComp1Pattern;
} ATMConnTriggerParams;
typedef struct tagATMCardInfo
{
	unsigned short	uiMainFwVersion;
	unsigned short	uiSarBootFwVersion;
	unsigned short	uiSarMainFwVersion;
	unsigned short	uiPciFpgaVersion;
	unsigned short	uiGapFpgaVersion;
	unsigned short	uiBptrgFpgaVersion;
	unsigned short	uiAm29240Revision;
	unsigned short	uiBt8222Revision;
	unsigned short	uiL64363Revision;
	unsigned short	uiImageCheck;
	unsigned short	uiDiagFlags;
	unsigned short	uiProductCode;
} ATMCardInfo;
typedef struct tagATMCardType
{
	unsigned short uiProductCode;
	unsigned short uiReserved[15];
} ATMCardType;
typedef struct tagATMCardCapabilities
{
	unsigned long	ulLineCellRate;
	unsigned short	uiMaxStream;
	unsigned short	uiMaxConnection;
	unsigned short	uiMaxCalls;
	unsigned short	uiMaxHostTxBuffer;
	unsigned short	uiMaxHostRxBuffer;
	unsigned short	uiMaxLaneClients;
	unsigned short	uiMaxVPIBits;
	unsigned short	uiMaxVCIBits;
	unsigned short uiSupportedFeatures;
	unsigned short uiMaxRateWithTeardown;
	unsigned short uiMaxRateWithoutTeardown;
	unsigned char	ucUNI_Version;
} ATMCardCapabilities;
typedef struct tagATMSonetLineInfo
{
	unsigned short	uiAlarmCurrent;
	unsigned short	uiAlarmHistory;
	unsigned long	ulSectionBip8;
	unsigned long	ulLineBip24;
	unsigned long	ulLineFebe;
	unsigned long	ulPathBip8;
	unsigned long	ulPathFebe;
	unsigned short	uiSectionBip8Rate;
	unsigned short	uiLineBip24Rate;
	unsigned short	uiLineFebeRate;
	unsigned short	uiPathBip8Rate;
	unsigned short	uiPathFebeRate;
} ATMSonetLineInfo;
typedef struct tagATMDS3E3LineInfo
{
	 unsigned short	uiAlarmCurrent;
	 unsigned short	uiAlarmHistory;
	 unsigned long		ulCodeViolationCount;
	 unsigned long		ulFrameErrorCount;
	 unsigned long		ulParityErrorCount;
	 unsigned long		ulCParityErrorCount;
	 unsigned long		ulFebeErrorCount;
	 unsigned long		ulFerfErrorCount;
	 unsigned long		ulPlcpFrameErrorCount;
	 unsigned long		ulPlcpBipErrorCount;
	 unsigned long		ulPlcpFebeErrorCount;
	 unsigned long		ulCodeViolationRate;
	 unsigned long		ulFrameErrorRate;
	 unsigned long		ulParityErrorRate;
	 unsigned long		ulCParityErrorRate;
	 unsigned long		ulFebeErrorRate;
	 unsigned long		ulFerfErrorRate;
	 unsigned long		ulPlcpFrameErrorRate;
	 unsigned long		ulPlcpBipErrorRate;
	 unsigned long		ulPlcpFebeErrorRate;
} ATMDS3E3LineInfo;
typedef struct tagATMDS1E1LineInfo
{
	 unsigned short	uiAlarmCurrent;
	 unsigned short	uiAlarmHistory;
	 unsigned long		ulCodeViolationCount;
	 unsigned long		ulFrameErrorCount;
	 unsigned long		ulSyncErrorCount;
	 unsigned long		ulFebeErrorCount;
	 unsigned long		ulPlcpOofErrorCount;
	 unsigned long		ulPlcpFrameErrorCount;
	 unsigned long		ulPlcpBipErrorCount;
	 unsigned long		ulPlcpFebeErrorCount;
	 unsigned long		ulCodeViolationRate;
	 unsigned long		ulFrameErrorRate;
	 unsigned long		ulSyncErrorRate;
	 unsigned long		ulFebeErrorRate;
	 unsigned long		ulPlcpOofErrorRate;
	 unsigned long		ulPlcpFrameErrorRate;
	 unsigned long		ulPlcpBipErrorRate;
	 unsigned long		ulPlcpFebeErrorRate;
} ATMDS1E1LineInfo;
typedef struct tagATMLayerInfo
{
	U64				ullTxCell;
	unsigned long	ulTxCellRate;
	U64				ullRxCell;
	unsigned long	ulRxCellRate;
	U64				ullRxHecCorrErrors;
	unsigned long	ulRxHecCorrErrorsRate;
	U64				ullRxHecUncorrErrors;
	unsigned long	ulRxHecUncorrErrorsRate;
} ATMLayerInfo;
typedef struct tagATMAAL5LayerInfo
{
	unsigned long	ulTimeStamp;
	unsigned long	ulTxCell;
	unsigned long	ulTxFrame;
	unsigned long	ulRxCell;
	unsigned long	ulRxFrame;
	unsigned long	ulRxCRC32Errors;
	unsigned long	ulRxLengthErrors;
} ATMAAL5LayerInfo;
typedef struct tagATMVCCIStatus
{
	unsigned long	ulCellHeader;
	unsigned long	ulTimeStamp;
	unsigned long	ulTxFrame;
	unsigned long	ulRxFrame;
} ATMVCCIStatus;
typedef struct tagATMVCCInfo
{
	unsigned short	uiIndex;
	unsigned short	uiCount;
	ATMVCCIStatus	status[2048 +2];
} ATMVCCInfo;
typedef struct tagATMTriggerInfo
{
	unsigned long	ulTrigger;
	unsigned long	ulLatency;
} ATMTriggerInfo;
typedef struct tagATMConnTriggerStatus
{
	unsigned long	ulTrigger;
	unsigned long	ulTxTimestamp;
	unsigned long	ulRxTimestamp;
} ATMConnTriggerStatus;
typedef struct tagATMConnTriggerInfo
{
	unsigned short	uiStartConnIndex;
	unsigned short	uiConnCount;
	ATMConnTriggerStatus status[2048 +2];
} ATMConnTriggerInfo;
typedef struct tagATMStreamDetailedStatus
{
	unsigned short	uiStreamIndex;
	unsigned short	uiConnIndex;
	unsigned long	ulCellHeader;
	unsigned char	ucStreamState;
	unsigned char	ucArpRetryCount;
	unsigned long	ulArpRespLatency;
	unsigned char	ucSvcCallState;
	unsigned char	ucSvcCauseLoc;
	unsigned char	ucSvcCauseCode;
	unsigned long	ulSvcSetupLatency;
} ATMStreamDetailedStatus;
typedef struct tagATMStreamDetailedInfo
{
	unsigned short				uiStartIndex;
	unsigned short				uiCount;
	ATMStreamDetailedStatus status[2048 ];
} ATMStreamDetailedInfo;
typedef struct tagATMStreamSearchInfo
{
	unsigned short	uiStartIndex;
	unsigned short	uiCount;
	unsigned short	uiReturnItemId;
	unsigned short	uiSearchItemId;
	unsigned long	ulSearchRangeLow;
	unsigned long	ulSearchRangeHigh;
	unsigned short	uiReturnItemSize;
	unsigned short	uiReserved;
	unsigned long	ulItem[2048];
} ATMStreamSearchInfo;
typedef struct tagATMConnectionStatus
{
	unsigned long	ulCellHeader;
	unsigned long	ulCallsAttempted;
	unsigned long	ulCallsEstablished;
	unsigned long	ulCallsFailed;
	unsigned long	ulCallsReleasedInError;
	unsigned char	ucState;
	unsigned char	ucUNICallState;
	unsigned char	ucLastCauseLoc;
	unsigned char	ucLastCauseCode;
	unsigned long	ulMinRTSetupLatency;
	unsigned long	ulMaxRTSetupLatency;
	unsigned long  ulTotRTSetupLatency;
	unsigned long  ulMinTeardownAckLatency;
	unsigned long  ulMaxTeardownAckLatency;
	unsigned long  ulTotTeardownAckLatency;
	unsigned long  ulTestDuration;
} ATMConnectionStatus;
typedef struct tagATMConnectionInfo
{
	unsigned long	ulIndex;
	unsigned long	ulCount;
	ATMConnectionStatus status[512 ];
} ATMConnectionInfo;
typedef struct tagATMConnectionInfoSummary
{
	unsigned long	ulIndex;
	unsigned long	ulCount;
	unsigned long	ulCallsAttempted;
	unsigned long	ulCallsEstablished;
	unsigned long	ulCallsFailed;
	unsigned long	ulCallsReleasedInError;
	unsigned long	ulCallsActive;
	unsigned long	ulMinRTSetupLatency;
	unsigned long	ulMaxRTSetupLatency;
	unsigned long	ulTotRTSetupLatency;
	unsigned long	ulMinTeardownAckLatency;
	unsigned long	ulMaxTeardownAckLatency;
	unsigned long	ulTotTeardownAckLatency;
	unsigned long	ulTestDuration;
	unsigned long	ulFirstFailedIndex;
} ATMConnectionInfoSummary;
typedef struct tagATMConnection64Status
{
	unsigned long	ulCellHeader;
	unsigned long	ulCallsAttempted;
	unsigned long	ulCallsEstablished;
	unsigned long	ulCallsFailed;
	unsigned long	ulCallsReleasedInError;
	unsigned char	ucState;
	unsigned char	ucUNICallState;
	unsigned char	ucLastCauseLoc;
	unsigned char	ucLastCauseCode;
	U64				ullMinRTSetupLatency;
	U64				ullMaxRTSetupLatency;
	U64			   ullTotRTSetupLatency;
	U64			   ullMinTeardownAckLatency;
	U64			   ullMaxTeardownAckLatency;
	U64			   ullTotTeardownAckLatency;
	U64			   ullTestDuration;
} ATMConnection64Status;
typedef struct tagATMConnection64Info
{
	unsigned long	ulIndex;
	unsigned long	ulCount;
	ATMConnection64Status status[512 ];
} ATMConnection64Info;
typedef struct tagATMConnection64InfoSummary
{
	unsigned long	ulIndex;
	unsigned long	ulCount;
	unsigned long	ulCallsAttempted;
	unsigned long	ulCallsEstablished;
	unsigned long	ulCallsFailed;
	unsigned long	ulCallsReleasedInError;
	unsigned long	ulCallsActive;
	U64				ullMinRTSetupLatency;
	U64				ullMaxRTSetupLatency;
	U64				ullTotRTSetupLatency;
	U64				ullMinTeardownAckLatency;
	U64				ullMaxTeardownAckLatency;
	U64				ullTotTeardownAckLatency;
	U64				ullTestDuration;
	unsigned long	ulFirstFailedIndex;
	unsigned long	ulFirstActiveFailedIndex;
} ATMConnection64InfoSummary;
typedef struct tagATMILMIInfo
{
	unsigned char	ucState;
	unsigned short	uiColdStarts;
	unsigned short	uiGoodPackets;
	unsigned short	uiBadPackets;
	unsigned short	uiSentPackets;
	ATMAddress		RegAddr;
} ATMILMIInfo;
typedef struct tagATMSAALInfo
{
	unsigned char	ucSscopState;
	unsigned char	ucSaalState;
	unsigned long	ulVtSendState;
	unsigned long	ulVtPollSend;
	unsigned long	ulVtMaxSend;
	unsigned long	ulVtPollData;
	unsigned long	ulVrRxState;
	unsigned long	ulVrHighestExpected;
	unsigned long	ulVrMaxReceive;
} ATMSAALInfo;
typedef struct tagATMSigEmulatorInfo
{
	unsigned long	ulCallsHandled;
	unsigned long	ulCallsProgressing;
	unsigned long	ulCallsActive;
} ATMSigEmulatorInfo;
typedef struct tagATMSigRestartAckInfo
{
	unsigned char	ucCurrentState;
} ATMSigRestartAckInfo;
typedef struct tagATMSigTraceParams
{
	unsigned char	ucStopConfig;
} ATMSigTraceParams;
typedef struct tagATMSigTraceEventInfo
{
	unsigned long	ulEventCount;
} ATMSigTraceEventInfo;
typedef struct tagATMSigTraceEventData
{
	unsigned char	ucEvent;
	unsigned char	ucCardNumber;
	unsigned char	ucCauseLocation;
	unsigned char	ucCauseCode;
	unsigned long	ulCallSeqNumber;
	unsigned long	ulTimeStamp;
} ATMSigTraceEventData;
typedef struct tagATMELANInfo
{
	unsigned char	ucInstance;
	unsigned char	ucState;
	unsigned char	ucC2Type;
	unsigned char	ucC3MTU;
	unsigned char	ucC5Name[32 ];
	unsigned short	uiC14LecIndex;
	unsigned short	uiCtrlDirectConnIndex;
	unsigned short	uiCtrlDistConnIndex;
	unsigned short	uiMcastSendConnIndex;
	unsigned short	uiMcastFwdConnIndex;
	ATMAddress		LesAtmAddr;
	ATMAddress		BusAtmAddr;
} ATMELANInfo;
typedef struct tagATMClassicalIPInfo
{
	unsigned char	ucSvcCallState;
	unsigned char	ucSvcCauseLoc;
	unsigned char	ucSvcCauseCode;
	unsigned char	ucReserved;
	unsigned short	uiArpRequestPackets;
	unsigned short	uiArpResponsePackets;
	unsigned short	uiInarpRequestPackets;
	unsigned short	uiInarpResponsePackets;
} ATMClassicalIPInfo;
typedef struct 	tagATMSigEmulTeardown
	{
	unsigned char 			ucTeardown;
	unsigned char			ucReserved1[3];
	unsigned long			ucReserved2[3];
	} ATMSigEmulTeardown;
typedef struct		tabATMPVCADNewParams
{
	 unsigned long      	ulTmrOutstandingReqid;
	 unsigned long       ulPort;
} ATMPVCADNewParams;
typedef struct		tagATMPVCADVPIVCIForGetnext
{
	 unsigned char 	ucReserved;
	 unsigned char		ucVPI;
	 unsigned short	uiVCI;
	 unsigned long		ulReserved;
} ATMPVCADVPIVCIForGetnext;
typedef struct		tagATMPVCADResponse
{
	unsigned char 	ucEntryState;
	unsigned char	ucVPI;
	unsigned short	uiVCI;
	unsigned long	ulPVCStatus;
	unsigned long	ulFwdTrafficDescriptorType;
	unsigned long	ulFwdPCR_0;
	unsigned long	ulFwdPCR_01;
	unsigned long	ulFwdSCR_0;
	unsigned long	ulFwdSCR_01;
	unsigned long	ulFwdMBS_0;
	unsigned long	ulFwdMBS_01;
	unsigned long	ulBwdTrafficDescriptorType;
	unsigned long	ulBwdPCR_0;
	unsigned long	ulBwdPCR_01;
	unsigned long	ulBwdSCR_0;
	unsigned long	ulBwdSCR_01;
	unsigned long	ulBwdMBS_0;
	unsigned long	ulBwdMBS_01;
	unsigned char	ucFwdQOS;
	unsigned char	ucBwdQOS;
	unsigned char	ucReserved[2];
} ATMPVCADResponse;
typedef struct		tagATMVCDBListReq
{
	 unsigned long		ulStartEntryNum;
	 unsigned char		ucEntryState;
	 unsigned char		ucReserved[3];
	 unsigned long		ulEntryCount;
} ATMVCDBListReq;
typedef struct		tagATMVCDBListHdr
{
	unsigned long		ulStartEntryNum;
	unsigned char		ucEntryState;
	unsigned char		ucReserved[3];
	unsigned long		ulEntryCount;
} ATMVCDBListHdr;
typedef struct		tagATMVCDBEntryParams
{
	unsigned long	ulPVCStatus;
} ATMVCDBEntryParams;
typedef struct		tagATMVCDBClearFlagReq
{
	unsigned short		uiFlags;
} ATMVCDBClearFlagReq;
typedef struct		tagATMVCDBEntryRtvl
{
	unsigned long		ulEntryNum;
	unsigned long		ulStateTimestamp;
	unsigned char		ucEntryState;
	unsigned char		ucEncapType;
	unsigned char		ucReserved1;
	unsigned char		ucVPI;
	unsigned short 	uiVCI;
	unsigned short		uiConnIndex;
	unsigned long		ulCallRef;
	unsigned long	ulFwdTrafficDescriptorType;
	unsigned long	ulFwdPCR_0;
	unsigned long	ulFwdPCR_01;
	unsigned long	ulFwdSCR_0;
	unsigned long	ulFwdSCR_01;
	unsigned long	ulFwdMBS_0;
	unsigned long	ulFwdMBS_01;
	unsigned long	ulBwdTrafficDescriptorType;
	unsigned long	ulBwdPCR_0;
	unsigned long	ulBwdPCR_01;
	unsigned long	ulBwdSCR_0;
	unsigned long	ulBwdSCR_01;
	unsigned long	ulBwdMBS_0;
	unsigned long	ulBwdMBS_01;
	unsigned char	ucFwdQOS;
	unsigned char	ucBwdQOS;
	unsigned char	ucReserved2[2];
	unsigned char	ucBbcClass;
	unsigned char	ucBbcTimingReq;
	unsigned char	ucBbcTrafficType;
	unsigned char	ucBbcSusceptibleToClipping;
	ATMAddress		AtmCaller;
	unsigned char	ucIPAddr[4];
	unsigned char	ucReserved3[4];
} ATMVCDBEntryRtvl;
typedef struct		tagATMVCDBInfo
{
	unsigned long		ulStartEntryNum;
	unsigned char		ucEntryState;
	unsigned char		ucReserved[3];
	unsigned long		ulEntryCount;
	ATMVCDBEntryRtvl  status[512 ];
}	ATMVCDBInfo;
typedef struct		tagATMVCDBPurge
{
	unsigned char		ucEntryState;
} ATMVCDBCPurge;
typedef struct 	tagATMIncomingSVCMethod
	{
	unsigned char	ucReserved[3];
	unsigned char	ucMethod;
	} ATMIncomingSVCMethod;
typedef enum
{
	 PVCAD_DOWN = 0,
	 PVCAD_INACTIVE,
	 PVCAD_CHECKING_VCCS,
	 PVCAD_RUNNING
} PVCAD_STATE;
typedef struct		tagATMVCCounts
{
	 unsigned long		ulNewSVCCount;
	 unsigned long		ulStableSVCCount;
	 unsigned long		ulModifiedSVCCount;
	 unsigned long		ulDeletedSVCCount;
	 unsigned long		ulTransitorySVCCount;
} ATMVCDBCounts;
 typedef struct 	tagATMPerConnBurstCount
	{
	unsigned short	uiStartConnIdx;
	unsigned short	uiConnCount;
	unsigned char	ucFunction;
	unsigned char	ucReserved;
	unsigned short	uiMultiBurstCount;
	unsigned long	ulInterBurstGap;
	unsigned long	ulFrameBurstSize;
	} ATMPerConnBurstCount;
 typedef struct 	tagATMPerPortBurstCount
	{
	unsigned char	ucFunction;
	unsigned char	ucReserved[3];
	unsigned long	ulReserved;
	unsigned long	ulFrameBurstSize;
	} ATMPerPortBurstCount;
 typedef struct 	tagATMStreamParamsCopy
	{
	unsigned short	uiSrcStrNum;
	unsigned short	uiDstStrNum;
	unsigned short	uiDstStrCount;
	unsigned short	uiReserved;
	unsigned long	ulReserved;
	} ATMStreamParamsCopy;
 typedef struct 	tagATMStreamParamsModify
	{
	unsigned short	uiStartStrNum;
	unsigned short	uiStrCount;
	unsigned short	uiParamItemID;
	unsigned short	uiParamCount;
	unsigned char	ucData[2048 ];
  } ATMStreamParamsModify;
 typedef struct 	tagATMStreamParamsFill
	{
	unsigned short	uiSrcStrNum;
	unsigned short	uiDstStrNum;
	unsigned short	uiDstStrCount;
	unsigned short	uiParamItemID;
	unsigned char	ucDelta[20 ];
	} ATMStreamParamsFill;
  typedef struct 	tagATMFrameCopyMod
	{
	unsigned short	uiStrIdx;
	unsigned short	uiDataOffset;
	unsigned char	ucDataLen;
	unsigned char  ucReserved[3];
	unsigned char 	ucData[12 ];
	} ATMFrameCopyMod;
 typedef struct 	tagATMFrameCopyReq
	{
	unsigned short	uiStartStrNum;
	unsigned short	uiStrCount;
	unsigned short	uiNumMods;
	ATMFrameCopyMod ModArray[100 ];
	} ATMFrameCopyReq;
 typedef struct 	tagATMSchedParams
	{
	unsigned long	ulUtilization;
	unsigned short	uiSchedType;
	unsigned short	uiReserved;
	unsigned long	ulReserved1;
	unsigned long	ulReserved2;
	} ATMSchedParams;
typedef struct 	tagATMPETLogFileReq
	{
	unsigned char	ucFunction;
	unsigned char	ucReserved[3];
	unsigned long	ulLogFileSize;
	} ATMPETLogFileReq;
typedef struct 	tagATMPETReq
	{
	unsigned long	ulReserved1;
	unsigned long	ulReserved2;
	unsigned long	ulConnTraceEvents;
	unsigned long	ulILMITraceEvents;
	unsigned long	ulLANETraceEvents;
	unsigned long	ulSAALTraceEvents;
	} ATMPETReq;
typedef struct		tagATMPETReadReq
	{
	unsigned long	ulReserved;
	unsigned short	uiReserved;
	unsigned short	uiEntryCount;
	} ATMPETReadReq;
typedef struct		tagATMPETListHdr
	{
	unsigned long	ulReserved;
	unsigned short	uiReserved;
	unsigned short	uiEntryCount;
	} ATMPETListHdr;
typedef struct 	tagATMPETEntryRtvl
	{
	unsigned long	ulRefNum;
	unsigned long	ulTimeStamp;
	unsigned char	ucEventData[140 ];
	} ATMPETEntryRtvl;
typedef struct		tagATMPETInfo
	{
	unsigned long	ulReserved;
	unsigned short	uiReserved;
	unsigned short	uiEntryCount;
	ATMPETEntryRtvl	status[512 ];
	}	ATMPETInfo;
typedef struct tagATMExtVCCIStatus
{
	unsigned long	ulConnIndex;
	unsigned long	ulCellHeader;
	unsigned long	ulTimeStamp;
	unsigned long	ulTxFrame;
	unsigned long	ulRxFrame;
	unsigned long	ulRxCRC32Err;
	unsigned long	ulRxTriggerCt;
	unsigned long	ulReserved[2];
} ATMExtVCCIStatus;
typedef struct tagATMExtVCCInfo
{
	unsigned short	uiIndex;
	unsigned short	uiCount;
	ATMExtVCCIStatus	status[2048 +2];
} ATMExtVCCInfo;
typedef struct tagATMStreamTriggerTimeStatus
{
	unsigned long	ulTrigger;
	unsigned long	ulTxTimestamp;
	unsigned long	ulRxTimestamp;
	unsigned long	ulTimestamp;
} ATMStreamTriggerTimeStatus;
typedef struct tagATMStreamTriggerTimeInfo
{
	unsigned short	uiStartIndex;
	unsigned short	uiCount;
	ATMStreamTriggerTimeStatus status[2048 +2];
} ATMStreamTriggerTimeInfo;
typedef struct 	tagATMConfigureDUT
	{
	unsigned short			iPortID;
	unsigned short			iIlmiMethod;
	ATMDS1E1LineParams		Line;
	char					Reserved1[3];
	ATMSSCOPParams			SSCOP;
	ATMUNIParams			UNI;
	ATMILMIParams			ILMI;
	ATMILMIStaticParams		ILMIStatic;
	unsigned char			ucConnectionType;
	unsigned char			ucEncaptionType;
	unsigned char			ucVPI;
	unsigned char			ucVCI[2];
	ATMClassicalIP			ClassicalIP;
	char 					Reserved2[75];
	} ATMConfigureDUT;

// # 1274 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/gigitems.h" 1 3
typedef struct tagGIGCaptureSetup
{
 unsigned char ucCRCErrors;
 unsigned char ucRxTrigger;
 unsigned char ucTxTrigger;
 unsigned char ucRCErrors;
 unsigned char ucFilterMode;
 unsigned char ucStartStopOnConditionMode;
 unsigned char uc64BytesOnly;
 unsigned char ucLast64Bytes;
 unsigned char ucStartStop;
} GIGCaptureSetup;
typedef struct tagGIGTransmit
{
 unsigned short uiMainLength;
 unsigned char  ucPreambleByteLength;
 unsigned char  ucFramesPerCarrier;
 unsigned long  ulGap;
 unsigned char  ucMainRandomBackground;
 unsigned char  ucBG1RandomBackground;
 unsigned char  ucBG2RandomBackground;
 unsigned char  ucSS1RandomBackground;
 unsigned char  ucSS2RandomBackground;
 unsigned char  ucMainCRCError;
 unsigned char  ucBG1CRCError;
 unsigned char  ucBG2CRCError;
 unsigned char  ucSS1CRCError;
 unsigned char  ucSS2CRCError;
 unsigned char  ucJabberCount;
 unsigned char  ucLoopback;
 unsigned long  ulBG1Frequency;
 unsigned long  ulBG2Frequency;
 unsigned short uiBG1Length;
 unsigned short uiBG2Length;
 unsigned short uiSS1Length;
 unsigned short uiSS2Length;
 unsigned short uiLinkConfiguration;
 unsigned short uiVFD1Offset;
 short          iVFD1Range;
 unsigned char  ucVFD1Mode;
 unsigned long  ulVFD1CycleCount;
 unsigned char  ucVFD1Data[8];
 unsigned short uiVFD2Offset;
 short          iVFD2Range;
 unsigned char  ucVFD2Mode;
 unsigned long  ulVFD2CycleCount;
 unsigned char  ucVFD2Data[8];
 unsigned short uiVFD3Offset;
 unsigned short uiVFD3Range;
 unsigned long  ulVFD3Count;
 unsigned char  ucVFD3Mode;
 unsigned char  ucMainBG1Mode;
 unsigned long  ulBurstCount;
 unsigned long  ulMultiburstCount;
 unsigned long  ulInterBurstGap;
 unsigned char  ucTransmitMode;
 unsigned char  ucEchoMode;
 unsigned char  ucPeriodicGap;
 unsigned char  ucCountRcverrOrOvrsz;
 unsigned char  ucGapByBitTimesOrByRate;
 unsigned char  ucRandomLengthEnable;
 unsigned short  uiVFD1BlockCount;
 unsigned short  uiVFD2BlockCount;
 unsigned short  uiVFD3BlockCount;
 unsigned char	  ucControlBits;
 unsigned char	  ucError;
} GIGTransmit;
typedef struct tagGIGAltTransmit
{
 unsigned char   ucEnableSS1;
 unsigned char   ucEnableSS2;
 unsigned char   ucEnableBG1;
 unsigned char   ucEnableBG2;
 unsigned char   ucEnableHoldoff;
 unsigned char   ucReserved[3];
} GIGAltTransmit;
typedef struct tagGIGAutoFiberNegotiate
{
 unsigned char   ucMode;
 unsigned char   ucRestart;
 unsigned short  uiLinkConfiguration;
 unsigned char  ucEnableCCode;
 unsigned char  ucEnableHoldoff;
 unsigned char  ucReserved[6];
} GIGAutoFiberNegotiate;
typedef struct tagGIGTrigger
{
 unsigned char ucTrigger1Mode;
 unsigned char ucTrigger1Range;
 unsigned short uiTrigger1Offset;
 unsigned char ucTrigger1Data[8];
 unsigned char ucTrigger1Mask[8];
 unsigned char ucTrigger2Mode;
 unsigned char ucTrigger2Range;
 unsigned short uiTrigger2Offset;
 unsigned char ucTrigger2Data[8];
 unsigned char ucTrigger2Mask[8];
 unsigned char ucTriggerMode;
 unsigned char ucReserved;
} GIGTrigger;
typedef struct tagGIGCaptureFrameInfo
{
 unsigned long  ulFrame;
 unsigned long  reserved1;
 U64            ullTimestamp;
 unsigned short uiStatus;
 unsigned short uiLength;
} GIGCaptureFrameInfo;
typedef struct tagGIGCaptureInfo
{
 GIGCaptureFrameInfo FrameInfo[96 ];
} GIGCaptureInfo;
typedef struct tagGIGCaptureCountInfo
{
 unsigned long ulCount;
} GIGCaptureCountInfo;
typedef struct tagGIGCaptureDataInfo
{
 unsigned long ulFrame;
 unsigned char  ucData[2048];
} GIGCaptureDataInfo;
typedef struct tagGIGCardInfo
{
		unsigned short uiLinkConfiguration;
		unsigned long ulLinkStateChanges;
} GIGCardInfo;
typedef struct tagGIGCounterInfo
{
 U64           ullTxFrames;
 U64           ullTxBytes;
 U64           ullTxTriggers;
 unsigned long ulTxLatency;
 U64           ullRxFrames;
 U64           ullRxBytes;
 U64           ullRxTriggers;
 unsigned long ulRxLatency;
 U64           ullCRCErrors;
 U64           ullOverSize;
 U64           ullUnderSize;
} GIGCounterInfo;
typedef struct tagGIGRateInfo
{
 unsigned long ulTxFrames;
 unsigned long ulTxBytes;
 unsigned long ulTxTriggers;
 unsigned long ulRxFrames;
 unsigned long ulRxBytes;
 unsigned long ulRxTriggers;
 unsigned long ulCRCErrors;
 unsigned long ulOverSize;
 unsigned long ulUnderSize;
} GIGRateInfo;
typedef struct tagGIGVersions
{
 unsigned short  uiFirmwareVersion;
 unsigned short  uiTransmitDataVersion;
 unsigned short  uiTransmitControlVersion;
 unsigned short  uiTransmitLowlevelVersion;
 unsigned short  uiReceiveDataVersion;
 unsigned short  uiReceiveControlVersion;
 unsigned short  uiReceiveLowlevelVersion;
 unsigned short  uiBackplaneControlVersion;
 unsigned short  uiLinkControlVersion;
 unsigned char   ucFirmwareCheck;
 unsigned char   ucTransmitDataCheck;
 unsigned char   ucTransmitControlCheck;
 unsigned char   ucTransmitLowlevelCheck;
 unsigned char   ucReceiveDataCheck;
 unsigned char   ucReceiveControlCheck;
 unsigned char   ucReceiveLowlevelCheck;
 unsigned char   ucBackplaneControlCheck;
 unsigned char   ucLinkControlCheck;
 unsigned char   ucBootVersion;
 unsigned char   ucReserved[16];
} GIGVersions;
typedef struct tagGIGCaptureInfoRequest
{
 unsigned long   ulStartIndex;
 unsigned long   ulEndIndex;
} GIGCaptureInfoRequest;
typedef struct tagGIGCaptureData
{
 unsigned long ulFrame;
 unsigned char  ucData[2048];
} GIGCaptureData;
// # 1280 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/fritems.h" 1 3
typedef struct tagFRLineCfg
{
 unsigned long ulSpeed;
 unsigned long ulProgBits;
 unsigned long ulProgBitsLen;
 unsigned char ucLineMode;
 unsigned char ucClocking;
 unsigned char ucClkPolarity;
 unsigned char ucEncoding;
 unsigned char ucGapCtl;
 unsigned char ucLoopbackOn;
 unsigned char ucCrcOff;
 unsigned char ucUseCRC32;
 unsigned char ucDataUnchanged;
 unsigned char ucDsrOn;
 unsigned char ucCtsOn;
 unsigned char ucDcdOn;
 unsigned char ucTmOn;
 unsigned char ucDtrOn;
 unsigned char ucRtsOn;
 unsigned char ucRdlOn;
 unsigned char ucLlbOn;
 unsigned char ucRxClocking;
 unsigned char ucRxClkPolarity;
 unsigned char ucReserved[13];
} FRLineCfg;
typedef struct tagFRT1E1LineCfg
{
 unsigned char	ucLineMode;
 unsigned char	ucClocking;
 unsigned char	ucDataEncoding;
 unsigned char	ucGapCtl;
 unsigned char	ucCrcOff;
 unsigned char	ucUseCRC32;
 unsigned char	ucDataUnchanged;
 unsigned char	ucLoopbackEnable;
 unsigned char	ucLineBuildout;
 unsigned char	ucLineCoding;
 unsigned char	ucLineFraming;
 unsigned char	ucChannels[32];
 unsigned char	ucReserved[9];
} FRT1E1LineCfg;
typedef struct tagFRT1E1LineInfo
{
 unsigned short uiAlarmCurrent;
 unsigned short uiAlarmHistory;
 unsigned long	ulCodeVviolationC;
 unsigned long	ulFrameErrorC;
 unsigned long	ulSyncErrorC;
 unsigned long	ulCodeViolationR;
 unsigned long	ulFrameErrorR;
 unsigned long	ulSyncErrorR;
 unsigned long	reserve[4];
} FRT1E1LineInfo;
typedef struct tagFRCardCfg
{
 unsigned long ulMultiBurstCnt;
 unsigned long ulBurstCnt;
 unsigned long ulInterBurstGap;
 unsigned long ulTransmitMode;
 unsigned char ucCardNum;
 unsigned char ucGroupMember;
 unsigned char ucMACAddress[6];
 unsigned char ucIPAddress[4];
 unsigned char ucNetmask[4];
 unsigned char ucDefaultGateway[4];
 unsigned char ucPingTargetAddress[4];
 unsigned char ucLatencyScaling;
 unsigned char ucHistogramType;
 unsigned char ucLmiOn;
 unsigned char ucSnmpFrames;
 unsigned char ucProtocolFrames;
 unsigned char ucPingFrames;
 unsigned char ucRipPeriod;
 unsigned char ucSnmpPeriod;
 unsigned char ucPingPeriod;
 unsigned char ucGeneralIPResponse;
 unsigned char ucEncapType;
 unsigned char	reserve1[3];
 unsigned char ucHistogramNoDE;
 unsigned char ucFrmDistType;
 unsigned char ucIntervalTime;
 unsigned char ucHistogramPerPVC;
 unsigned char ucReserved[11];
} FRCardCfg;
typedef struct tagFRCardProtoCfgParmType
{
	unsigned char		ucProtoStack;
	unsigned char  	ucEncapType;
	unsigned char 		pad[2];
	unsigned long		reserved[10];
} FRCardProtocolCfg;
typedef struct tagFRLayer3LongLatencyDEInfo
{
 unsigned long ulMinimum;
 unsigned long ulMaximum;
 U64           u64Total;
 unsigned long ulFrames;
 unsigned long ulDEMinimum;
 unsigned long ulDEMaximum;
 U64           u64DETotal;
 unsigned long ulDEFrames;
} FRLayer3LongLatencyDEInfo;
typedef struct tagFRTriggerCfg
{
 unsigned char  ucEnable;
 unsigned char  ucDirection;
 unsigned char  ucCompCombo;
 unsigned char  ucReserved1;
 unsigned short uiTrig1Offset;
 unsigned short uiTrig1Range;
 unsigned char  ucTrig1Pattern[6];
 unsigned char  ucTrig1Mask[6];
 unsigned short uiTrig2Offset;
 unsigned short uiTrig2Range;
 unsigned char  ucTrig2Pattern[6];
 unsigned char  ucTrig2Mask[6];
 unsigned char  ucReserved[20];
} FRTriggerCfg;
typedef struct tagFRIPSubnetRegister
{
 unsigned short   uiIPSubnetId;
 unsigned char    ucIPAddress[4];
 unsigned char    ucNetmask[4];
 unsigned char    ucDefaultGateway[4];
} FRIPSubnetRegister;
typedef struct tagFRIPSubnetDeRegister
{
 unsigned short   uiSubnetCount;
 unsigned short   uiIPSubnetId;
} FRIPSubnetDeRegister;
typedef struct tagFRPvcTableEntry
{
 unsigned long  ulCIR;
 unsigned short uiDLCI;
 unsigned short uiFrameSize;
 unsigned long  ulBc;
 unsigned long  ulAccessRate;
 unsigned long  ulBe;
 unsigned short uiFrameRate;
 unsigned short uiStreamCount;
 unsigned short uiIPSubnetId;
 unsigned char   ucReserved[12];
} FRPvcTableEntry;
typedef struct tagFRPvcStrmMapCfg
{
 unsigned long  ulStreamId;
 unsigned short uiDLCI;
 unsigned short uiVfdState;
 unsigned short uiBgFillLen;
 unsigned short uiMinFrameSize;
 unsigned short uiMaxFrameSize;
 unsigned char  ucFcsError;
 unsigned char  ucAbortFlag;
 unsigned char  ucEncapType;
 unsigned char  ucCR;
 unsigned char  ucFECN;
 unsigned char  ucBECN;
 unsigned char  ucDE;
 unsigned char  ucReserved1;
 unsigned char  ucEncapHeader[16 ];
 unsigned char  ucReserved[12];
} FRPvcStrmMapCfg;
typedef struct tagFRLmiCfg
{
 unsigned char		ucLinkManagement;
 unsigned char		ucUNIMode;
 unsigned char		ucNN1;
 unsigned char		ucNN2;
 unsigned char		ucNN3;
 unsigned char		ucNN4;
 unsigned char		ucNT1;
 unsigned char		ucNT2;
 unsigned char		ucNT3;
} FRLmiCfg;
typedef struct tagFRVersionInfo
{
 unsigned short     uiMainFwVersion;
 unsigned short     uiBootFwVersion;
 unsigned short     uiFpgaVersion;
} FRVersionInfo;
typedef struct tagFRLinkStatusInfo
{
 unsigned long  ulSpeed;
 unsigned long  ulReserved[19];
} FRLinkStatusInfo;
typedef struct tagFRPVCStatusInfo
{
 unsigned char ucBitMap[384 ];
} FRPVCStatusInfo;
typedef struct  tagFRLinkInfo
{
 unsigned long  ulTimestamp;
 unsigned long  ulRxFrameRate;
 unsigned long  ulRxByteRate;
 unsigned long  ulRxFcsErrRate;
 unsigned long  ulRxTriggerRate;
 unsigned long  ulRxAbortRate;
 unsigned long  ulRxInvLenErrRate;
 unsigned long  ulRxNonOctetAlignedErrRate;
 unsigned long  ulRxOverflowErrRate;
 unsigned long  ulRxFrames;
 unsigned long  ulRxBytes;
 unsigned long  ulRxFcs_err;
 unsigned long  ulRxTrigger;
 unsigned long  ulRxAbort;
 unsigned long  ulRxInvLenErr;
 unsigned long  ulRxNonOctetAlignedErr;
 unsigned long  ulRxOverflowErr;
 unsigned long  ulRxIdleSeq;
 unsigned long  ulRxDeFrames;
 unsigned long  ulRxBECNCount;
 unsigned long  ulRxFECNCount;
 unsigned long  ulRxInvalidPVC;
 unsigned long  ulRxTrigLatency;
 unsigned long  ulRxTags;
 unsigned long  ulRxStack;
 unsigned long  ulRxInvARPReq;
 unsigned long  ulRxARPReq;
 unsigned long  ulRxARPReply;
 unsigned long  ulRxPingReq;
 unsigned long  ulRxPingReply;
 unsigned long  ulTxFrameRate;
 unsigned long  ulTxByteRate;
 unsigned long  ulTxFcsErrRate;
 unsigned long  ulTxAbortRate;
 unsigned long  ulTxTriggerRate;
 unsigned long  ulTxFrames;
 unsigned long  ulTxBytes;
 unsigned long  ulTxFcsErr;
 unsigned long  ulTxAbort;
 unsigned long  ulTxTrigger;
 unsigned long  ulTxDeFrames;
 unsigned long  ulTxBECNFrames;
 unsigned long  ulTxFECNFrames;
 unsigned long  ulTxTrigLatency;
 unsigned long  ulTxStack;
 unsigned long  ulTxInvARPReq;
 unsigned long  ulTxARPReq;
 unsigned long  ulTxARPReply;
 unsigned long  ulTxPingReq;
 unsigned long  ulTxPingReply;
 unsigned long  ulReserved[20];
} FRLinkInfo;
typedef struct tagFRLmiInfo
{
 unsigned long ulConfiguredPvc;
 unsigned long ulActivePvc;
 unsigned long ulInactivePvc;
 unsigned long ulDisabledPvc;
 unsigned long ulTxStatusReq;
 unsigned long ulTxStatusMsg;
 unsigned long ulTxFullStatusReq;
 unsigned long ulTxFullStatusMsg;
 unsigned long ulTxStatusUpdate;
 unsigned long ulRxStatusReq;
 unsigned long ulRxStatusMsg;
 unsigned long ulRxFullStatusReq;
 unsigned long ulRxFullStatusMsg;
 unsigned long ulRxStatusUpdate;
 unsigned long ulPvcCongestion;
 unsigned long ulNewPvc;
 unsigned long ulPvcDeleted;
 unsigned long ulPvcDeactivated;
 unsigned long ulMulticastIe;
 unsigned long ulInvalidFrame;
 unsigned long ulReserved[3];
} FRLmiInfo;
typedef struct tagFRPvcMainInfo
{
 unsigned short  uiPadding;
 unsigned short  uiDLCI;
 unsigned long  ulTxFrameRate;
 unsigned long  ulTxByteRate;
 unsigned long  ulTxFrames;
 unsigned long  ulTxBytes;
 unsigned long  ulTxDeFrames;
 unsigned long  ulTotFECNsSent;
 unsigned long  ulTotBECNsSent;
 unsigned long  ulTxFcsErr;
 unsigned long  ulTxAbort;
 unsigned long  ulRxFrameRate;
 unsigned long  ulRxByteRate;
 unsigned long  ulRxFrames;
 unsigned long  ulRxBytes;
 unsigned long  ulRxDeFrames;
 unsigned long  ulFECN;
 unsigned long  ulBECN;
 unsigned long  ulReserved[4];
} FRPvcMainInfo;
typedef  struct tagFRStreamControl
{
 unsigned long   ulStreamId;
 unsigned char   ucEnable;
 unsigned char   ucFcsErr;
 unsigned char   ucAbortFlag;
 unsigned char   ucReserved;
 unsigned long   ulReserved[4];
} FRStreamControl;
typedef  struct tagFRPvcControl
 {
 unsigned short  uiDLCI;
 unsigned char   ucEnable;
 unsigned char   ucReserved[3];
 unsigned long   ulReserved[4];
 } FRPvcControl;
typedef struct tagFRGetCaptureCountInfo
 {
 unsigned long  ulCaptureCnt;
 } FRGetCaptureCountInfo;
typedef struct tagFRGetCaptureFrameCmdInfo
 {
 unsigned long ulFrameNum;
 } FRGetCaptureFrameCmdInfo;
typedef struct tagFRReleaseCaptureFrameInfo
 {
 unsigned long ulCaptureType;
 } FRReleaseCaptureFrameInfo;
typedef struct tagFRMemoryDumpInfo
 {
 unsigned long  ulAddr;
 unsigned long ulLen;
 } FRMemoryDumpInfo;
typedef struct tagFRAssignAddress
 {
 unsigned char  ucMACAddress[6];
 unsigned char  ucIPAddress[4];
 unsigned char  ucNetmask[4];
 unsigned char  ucDefaultGateway[4];
 unsigned char  ucPingTargetAddress[4];
 unsigned char  ucHistogramType;
 unsigned char  ucSnmpArp;
 unsigned char  ucProtocolFrames;
 unsigned char  ucPingFrames;
 unsigned char  ucRipPeriod;
 unsigned char  ucSnmpPeriod;
 unsigned char  ucPingPeriod;
 } FRAssignAddress;
typedef struct tagFRHistogram
 {
 unsigned long   ulHistType;
 unsigned long   ulTimeBucket;
 unsigned long   ulLatRef[16];
 } FRHistogram;
typedef struct tagFRHistReset
{
 unsigned long   ulHistType;
} FRHistReset;
typedef struct tagFRHistScale
{
 unsigned long   ulScale;
} FRHistScale;
typedef struct tagFRHistTypeInfo
{
 unsigned long  ulHistType;
 unsigned long  ulStart;
 unsigned long  ulRange;
} FRHistDataInfo;
typedef struct tagFRIntervalTimeInfo
{
 unsigned long  ulTxStart;
 unsigned long  ulTxStop;
 unsigned long  ulRxStart;
 unsigned long  ulRxStop;
} FRIntervalTimeInfo;
// # 1698 "/usr/local/include/fritems.h" 3
typedef struct tagWNDS3LineCfg
{
	unsigned long  ulPortNo;
	unsigned long  ulCount;
	unsigned char  ucLineMode;
	unsigned char  ucLineFraming;
	unsigned char  ucClocking;
	unsigned char  ucLoopbackEnable;
	unsigned char  ucLineEncoding;
	unsigned char  ucChannelised;
	unsigned char  ucActive;
	unsigned char  ucLineBuildout;
	unsigned long  ulReserved;
} WNDS3LineCfg;
typedef struct tagWNDS3LineCtrl
{
  unsigned long ulPortNo;
  unsigned long ulCount;
  unsigned char ucEnable;
  unsigned char ucReserved[3];
} WNDS3LineCtrl;
typedef struct tagWNT1E1LineCfg
{
	unsigned long  ulT1E1LineNo;
	unsigned long  ulCount;
	unsigned char  ucClocking;
	unsigned char  ucLoopbackEnable;
	unsigned char  ucLineBuildout;
	unsigned char  ucLineCoding;
	unsigned char  ucLineFraming;
	unsigned char  ucActive;
	unsigned char  ucPad[2];
	unsigned long  ulReserved;
} WNT1E1LineCfg;
typedef struct tagWNT1E1LineCtrl
{
	unsigned long  ulT1E1LineNo;
	unsigned long	ulCount;
	unsigned char	ucEnable;
	unsigned char  ucPad[3];
	unsigned long  ulReserved;
} WNT1E1LineCtrl;
typedef struct tagWNChanPhysCfg
{
 unsigned long	 ulChannelId;
 unsigned long  ulCount;
 unsigned char  ucTimeSlots[32];
 unsigned char  ucDataEncoding;
 unsigned char  ucGapCtl;
 unsigned char  ucCRCoff;
 unsigned char  ucUseCRC32;
 unsigned char  ucDataUnchanged;
 unsigned char  ucReserved[7];
} WNChanPhysCfg;
typedef struct tagWNChanAttribCfg
{
 unsigned long	  ulChannelId;
 unsigned long   ulCount;
 unsigned char   ucEnable;
 unsigned char   ucConnType;
 unsigned char   ucTXMode;
 unsigned char   ucFCSErr;
 unsigned char   ucAbortFlag;
 unsigned char	  ucPad[3];
 unsigned long   ulMultiBurstCnt;
 unsigned long   ulBurstCnt;
 unsigned long   ulInterBurstCnt;
 unsigned long   ulReserved2[4];
} WNChanAttribCfg;
typedef struct tagWNChanCtrl
{
 unsigned long	  ulChannelId;
 unsigned long   ulCount;
 unsigned char   ucEnable;
 unsigned char   ucPad[3];
 unsigned long   ulReserved;
} WNChanCtrl;
typedef struct tagWNChanDel
{
 unsigned long	  ulChannelId;
 unsigned long   ulCount;
} WNChanDel;
typedef struct tagWNPvcCfg
{
 unsigned long   ulDLCI;
 unsigned long   ulCount;
 unsigned long   ulChannelId;
 unsigned char	  ucPvcEnable;
 unsigned char	  ucEncapType;
 unsigned char	  ucPad[2];
 unsigned long   ulCIR;
 unsigned long   ulBc;
 unsigned long   ulBe;
 unsigned char	  ucLocalIPAddr[4];
 unsigned char	  ucPeerIPAddr[4];
 unsigned char	  ucNetMask[4];
} WNPvcCfg;
typedef struct tagWNPvcCtrl
{
 unsigned long	  ulDlci;
 unsigned long	  ulCount;
 unsigned long	  ulChannelId;
 unsigned char   ucEnable;
 unsigned char   ucPad[3];
 unsigned long   ulReserved[2];
} WNPvcCtrl;
typedef struct tagWNPvcDel
{
 unsigned long	  ulDlci;
 unsigned long   ulCount;
 unsigned long   ulChannelId;
} WNPvcDel;
typedef struct tagWNStreamCtrl
{
 unsigned long   ulStreamId;
 unsigned long   ulCount;
 unsigned char   ucEnable;
 unsigned char   ucPad[3];
} WNStreamCtrl;
typedef struct tagWNStreamDel
{
 unsigned long   ulStreamId;
 unsigned long   ulCount;
 unsigned long	  ulChannelId;
} WNStreamDel;
typedef struct tagWNStrmExtCfg
{
 unsigned long   ulStreamID;
 unsigned long   ulCount;
 unsigned long   ulDLCIorPPPid;
 unsigned long   ulChannelId;
 unsigned char   ucEncapType;
 unsigned char   ucPad[3];
 unsigned char   ucCR;
 unsigned char   ucFECN;
 unsigned char   ucBECN;
 unsigned char   ucDE;
 unsigned long   ulFrameRate;
 unsigned char	  ucIPManipulateMode;
 unsigned char	  ucStepCount;
 unsigned short  uiIPLimitCount;
 unsigned long   ulReserved[4];
} WNStrmExtCfg;
typedef struct tagWNLmiCfg
{
 unsigned long   ulChannelId;
 unsigned long   ulCount;
 unsigned char   ucLinkManagement;
 unsigned char   ucUNIMode;
 unsigned char   ucNN1;
 unsigned char   ucNN2;
 unsigned char   ucNN3;
 unsigned char   ucNN4;
 unsigned char   ucNT1;
 unsigned char   ucNT2;
 unsigned char   ucNT3;
 unsigned char   ucPad[3];
} WNLmiCfg;
typedef struct tagWNLmiDel
{
 unsigned long		ulChannelId;
 unsigned long		ulCount;
} WNLmiDel;
typedef struct tagIPSubnetReg
{
 unsigned long   ulIPSubnetId;
 unsigned long   ulCount;
 unsigned char   ucIPAddr[4];
 unsigned char   ucNetmask[4];
 unsigned char   ucGateway[4];
} IPSubnetReg;
typedef struct tagIPSubnetDeReg
{
 unsigned long   ulIPSubnetId;
 unsigned long   ulCount;
} IPSubnetDeReg;
typedef struct tagWNTriggerCtrl
{
 unsigned long   ulChannelId;
 unsigned long   ulCount;
 unsigned char   ucEnable;
 unsigned char   ucPad[3];
}WNTriggerCtrl;
typedef struct tagWNTriggerCfg
{
 unsigned long   ulChannelId;
 unsigned long   ulCount;
 unsigned char   ucEnable;
 unsigned char   ucDirection;
 unsigned char   ucCompCombo;
 unsigned char   ucPad;
 unsigned short  uiTrig1Offset;
 unsigned short  uiTrig1Range;
 unsigned char   ucTrig1Pattern[6];
 unsigned char   ucTrig1Mask[6];
 unsigned short  uiTrig2Offset;
 unsigned short  uiTrig2Range;
 unsigned char   ucTrig2Pattern[6];
 unsigned char   ucTrig2Mask[6];
} WNTriggerCfg;
typedef struct tagWNTriggerDel
{
 unsigned long   ulChannelId;
 unsigned long   ulCount;
}WNTriggerDel;
typedef FRVersionInfo  WNVersionInfo;
typedef struct tagWNCardCapInfo
{
 unsigned short  	uiMaxPorts;
 unsigned short  	uiMaxStreams;
 unsigned short  	uiMaxConnect;
 unsigned short  	uiMaxChannels;
 unsigned short  	uiMaxPvcs;
 unsigned long   	ulMaxHostTxBuf;
 unsigned long   	ulMaxHostRxBuf;
 unsigned short  	uiSupportFeatures;
 unsigned char   	ucReserved[4];
} WNCardCapInfo;
typedef struct  tagWNPortInfo
{
 unsigned long    ulPort;
 unsigned long    ulCount;
 unsigned long		ulTimestamp;
 unsigned long		ulRxFrameRate;
 unsigned long		ulRxByteRate;
 unsigned long		ulRxTriggerRate;
 unsigned long		ulRxFrames;
 unsigned long		ulRxBytes;
 unsigned long		ulRxFcs_err;
 unsigned long		ulRxTrigger;
 unsigned long		ulRxAbort;
 unsigned long		ulRxInvLenErr;
 unsigned long		ulRxNonOctetAlignedErr;
 unsigned long		ulRxOverflowErr;
 unsigned long		ulRxIdleSeq;
 unsigned long		ulRxDeFrames;
 unsigned long		ulRxBECNCount;
 unsigned long		ulRxFECNCount;
 unsigned long		ulRxInvalidPVC;
 unsigned long		ulRxTrigLatency;
 unsigned long		ulRxTags;
 unsigned long		ulRxStack;
 unsigned long		ulRxInvARPReq;
 unsigned long		ulRxARPReq;
 unsigned long		ulRxARPReply;
 unsigned long		ulRxPingReq;
 unsigned long		ulRxPingReply;
 unsigned long		ulTxFrameRate;
 unsigned long		ulTxByteRate;
 unsigned long		ulTxTriggerRate;
 unsigned long		ulTxFrames;
 unsigned long		ulTxBytes;
 unsigned long		ulTxFcsErr;
 unsigned long		ulTxAbort;
 unsigned long		ulTxTrigger;
 unsigned long		ulTxDeFrames;
 unsigned long		ulTxBECNFrames;
 unsigned long		ulTxFECNFrames;
 unsigned long		ulTxTrigLatency;
 unsigned long		ulTxStack;
 unsigned long		ulTxInvARPReq;
 unsigned long		ulTxARPReq;
 unsigned long		ulTxARPReply;
 unsigned long		ulTxPingReq;
 unsigned long		ulTxPingReply;
 unsigned long		ulReserved[2];
} WNPortInfo;
typedef struct tagWNDS3LineInfo
{
 unsigned long    ulPort;
 unsigned long    ulCount;
 unsigned short	uiAlarmCurrent;
 unsigned short	uiAlarmHistory;
 unsigned long		ulCodeVviolationC;
 unsigned long		ulFrameErrorC;
 unsigned long		ulSyncErrorC;
 unsigned long		ulCBitParityErrorC;
 unsigned long		ulPBitParityErrorC;
 unsigned long		ulFEBEErrorC;
 unsigned long		ulCodeViolationR;
 unsigned long		ulFrameErrorR;
 unsigned long		ulSyncErrorR;
 unsigned long		ulReserved[4];
} WNDS3LineInfo;
typedef struct tagWNDS3LineStatus
{
 unsigned long		ulPort;
 unsigned long    ulCount;
 unsigned char	  	ucState;
 unsigned char   	ucReserved[3];
} WNDS3LineStatus;
typedef struct  tagWNChannelInfo
{
 unsigned char    ucLineNo;
 unsigned char    ucChannelNo;
 unsigned long    ulCount;
 unsigned long		ulTimestamp;
 unsigned long		ulRxFrameRate;
 unsigned long		ulRxByteRate;
 unsigned long		ulRxTriggerRate;
 unsigned long		ulRxFrames;
 unsigned long		ulRxBytes;
 unsigned long		ulRxFcs_err;
 unsigned long		ulRxTrigger;
 unsigned long		ulRxAbort;
 unsigned long		ulRxInvLenErr;
 unsigned long		ulRxNonOctetAlignedErr;
 unsigned long		ulRxOverflowErr;
 unsigned long		ulRxIdleSeq;
 unsigned long		ulRxDeFrames;
 unsigned long		ulRxBECNCount;
 unsigned long		ulRxFECNCount;
 unsigned long		ulRxInvalidPVC;
 unsigned long		ulRxTrigLatency;
 unsigned long		ulRxTags;
 unsigned long		ulRxStack;
 unsigned long		ulRxInvARPReq;
 unsigned long		ulRxARPReq;
 unsigned long		ulRxARPReply;
 unsigned long		ulRxPingReq;
 unsigned long		ulRxPingReply;
 unsigned long		ulTxFrameRate;
 unsigned long		ulTxByteRate;
 unsigned long		ulTxTriggerRate;
 unsigned long		ulTxFrames;
 unsigned long		ulTxBytes;
 unsigned long		ulTxFcsErr;
 unsigned long		ulTxAbort;
 unsigned long		ulTxTrigger;
 unsigned long		ulTxDeFrames;
 unsigned long		ulTxBECNFrames;
 unsigned long		ulTxFECNFrames;
 unsigned long		ulTxTrigLatency;
 unsigned long		ulTxStack;
 unsigned long		ulTxInvARPReq;
 unsigned long		ulTxARPReq;
 unsigned long		ulTxARPReply;
 unsigned long		ulTxPingReq;
 unsigned long		ulTxPingReply;
 unsigned long		ulReserved[2];
} WNChannelInfo;
typedef struct tagWNT1E1LineInfo
{
 unsigned long 	ulT1E1LineNo;
 unsigned long    ulCount;
 unsigned short	uiAlarmCurrent;
 unsigned short	uiAlarmHistory;
 unsigned long		ulCodeVviolationC;
 unsigned long		ulFrameErrorC;
 unsigned long		ulSyncErrorC;
 unsigned long		ulFebeErrorC;
 unsigned long		ulCodeViolationR;
 unsigned long		ulFrameErrorR;
 unsigned long		ulSyncErrorR;
 unsigned long		ulFebeErrorR;
 unsigned long   	ulReserved[2];
} WNT1E1LineInfo;
typedef struct tagWNPvcStatus
{
 unsigned char		ucBitmap[128  ];
} WNPvcStatus;
typedef struct tagWNPvcMainInfo
{
 unsigned long 	ulDLCI;
 unsigned long    ulCount;
 unsigned char    ucChannelNo;
 unsigned char    ucLineNo;
 unsigned long		ulTxFrameRate;
 unsigned long		ulTxByteRate;
 unsigned long		ulTxFrames;
 unsigned long		ulTxBytes;
 unsigned long		ulTxDeFrames;
 unsigned long		ulTotFECNsSent;
 unsigned long		ulTotBECNsSent;
 unsigned long		ulTxFcsErr;
 unsigned long		ulTxAbort;
 unsigned long		ulRxFrameRate;
 unsigned long		ulRxByteRate;
 unsigned long		ulRxFrames;
 unsigned long		ulRxBytes;
 unsigned long		ulRxDeFrames;
 unsigned long		ulFECNCount;
 unsigned long		ulBECNCount;
 unsigned long		ulReserved;
} WNPvcMainInfo;
typedef struct tagWNLmiInfo
{
 unsigned char   	ucChannelNo;
 unsigned char   	ucLineNo;
 unsigned long   	ulCount;
 unsigned long		ulConfiguredPvc;
 unsigned long		ulActivePvc;
 unsigned long		ulInactivePvc;
 unsigned long		ulDisabledPvc;
 unsigned long		ulTxStatusReq;
 unsigned long		ulTxStatusMsg;
 unsigned long		ulTxFullStatusReq;
 unsigned long		ulTxFullStatusMsg;
 unsigned long		ulTxStatusUpdate;
 unsigned long		ulRxStatusReq;
 unsigned long		ulRxStatusMsg;
 unsigned long		ulRxFullStatusReq;
 unsigned long		ulRxFullStatusMsg;
 unsigned long		ulRxStatusUpdate;
 unsigned long		ulPvcCongestion;
 unsigned long		ulNewPvc;
 unsigned long		ulPvcDeleted;
 unsigned long		ulPvcDeactivated;
 unsigned long		ulMulticastIe;
 unsigned long		ulInvalidFrame;
 unsigned long		ulReserved;
} WNLmiInfo;
// # 1286 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/fstitems.h" 1 3
typedef struct tagFSTAlternateTx
 {
 unsigned char  ucEnabled;
 unsigned char	 ucCRCErrors;
 unsigned char	 ucErrorSymbol;
 unsigned char	 ucDribble;
 unsigned long	 ulAlternateCount;
 unsigned short uiDataLength;
 unsigned char	 ucData[2048];
 } FSTAlternateTx;
typedef struct tagFSTControlAux
 {
 unsigned char	ucFlowControlPause;
 unsigned char	ucPreambleLen;
 } FSTControlAux;
typedef struct tagFSTCaptureParams
 {
 unsigned char	ucCRCErrors;
 unsigned char	ucOnTrigger;
 unsigned char  ucFilterMode;
 unsigned char	ucStartStopOnConditionXMode;
 unsigned char	uc64BytesOnly;
 unsigned char	ucLast64Bytes;
 unsigned char	ucCollisions;
 unsigned char	ucStartStop;
 } FSTCaptureParams;
typedef struct tagFSTVLAN
 {
 unsigned char  ucVLANEnable;
 unsigned short uiTPID;
 unsigned char  ucPRI;
 unsigned char  ucCFI;
 unsigned short uiVID;
 } FSTVLAN;
typedef struct tagFSTCaptureCountInfo
 {
 unsigned long	ulCaptureCount;
 } FSTCaptureCountInfo;
typedef struct tagFSTCaptureFrameInfo
 {
 unsigned long	 ulIndex;
 unsigned char	 ucStatus;
 unsigned char	 ucPreambleCount;
 unsigned short uiLength;
 unsigned long	 ulTimestamp;
 } FSTCaptureFrameInfo;
typedef struct tagFSTCaptureInfo
	{
	FSTCaptureFrameInfo	FrameInfo[96 ];
	} FSTCaptureInfo;
typedef struct tagFSTCaptureDataInfo
 {
 unsigned long	ulFrameNum;
 unsigned char	ucData[2048];
 } FSTCaptureDataInfo;
typedef struct tagFSTProtocolParameters
{
   unsigned char  ucDstMAC[6];
   unsigned char  ucSrcMAC[6];
   unsigned char  ucDstIP[4];
   unsigned char  ucSrcIP[4];
   unsigned char  ucNetMask[4];
   unsigned char  ucResponseMask[4];
   unsigned char  ucDefaultGateway[4];
   unsigned long  ulProtocolResponse;
   unsigned long  ulProtocolGenerate;
   unsigned long  ulARPPeriod;
   unsigned long  ulPINGPeriod;
   unsigned char  ucIPChecksumEnable;
   unsigned char  ucIPChecksumErrorEnable;
} FSTProtocolParameters;
typedef struct tagFSTProtocolCounterInfo
{
	U64   u64RxVLANFrames;
   U64   u64RxIPFrames;
	U64   u64IPChecksumErrors;
	unsigned long	ulRxARPReply;
	unsigned long	ulTxARPReply;
	unsigned long  ulTxARPRequest;
	unsigned long  ulRxARPRequest;
	unsigned long  ulRxPingReply;
	unsigned long  ulTxPingReply;
   unsigned long  ulTxPingRequest;
	unsigned long  ulRxPingRequest;
} FSTProtocolCounterInfo;
// # 1292 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/ethitems.h" 1 3
typedef struct tagETHTransmit
{
 unsigned char		ucTransmitMode;
 unsigned short	uiDataLength;
 unsigned char		ucDuplexMode;
 unsigned char		ucSpeed;
 unsigned short	uiCollisionBackoffAggressiveness;
 unsigned long		ulBurstCount;
 unsigned long		ulMultiBurstCount;
 unsigned long		ulInterFrameGap;
 unsigned short	uiInterFrameGapScale;
 unsigned long		ulInterBurstGap;
 unsigned short	uiInterBurstGapScale;
 unsigned char		ucRandomBackground;
 unsigned char		ucRandomLength;
 unsigned char		ucCRCErrors;
 unsigned char		ucAlignErrors;
 unsigned char 	ucSymbolErrors;
 unsigned short	uiDribbleBits;
 unsigned char		ucVFD1Mode;
 unsigned short	uiVFD1Offset;
 short				iVFD1Range;
 unsigned char		ucVFD1Pattern[6];
 unsigned short	uiVFD1CycleCount;
 unsigned short   uiVFD1BlockCount;
 unsigned char		ucVFD2Mode;
 unsigned short	uiVFD2Offset;
 short				iVFD2Range;
 unsigned char		ucVFD2Pattern[6];
 unsigned short 	uiVFD2CycleCount;
 unsigned short   uiVFD2BlockCount;
 unsigned char		ucVFD3Mode;
 unsigned short	uiVFD3Offset;
 unsigned short	uiVFD3Range;
 unsigned short	uiVFD3DataCount;
 unsigned short   uiVFD3BlockCount;
 unsigned char		ucVFD3Buffer[2044];
 unsigned char		ucAntiPartitioningEnable;
 unsigned char		ucReserved[63];
} ETHTransmit;
typedef struct tagETHTrigger
{
 unsigned char		ucTriggerMode;
 unsigned short	uiTrigger1Offset;
 unsigned short   uiTrigger1Range;
 unsigned char		ucTrigger1Pattern[6];
 unsigned short	uiTrigger2Offset;
 unsigned short   uiTrigger2Range;
 unsigned char		ucTrigger2Pattern[6];
} ETHTrigger;
typedef struct tagETHLatency
{
 unsigned short	uiMode;
 unsigned short 	uiRange;
 unsigned short	uiOffset;
 unsigned char		ucPattern[12];
} ETHLatency;
typedef struct tagETHCollision
{
 unsigned int uiOffset;
 unsigned int uiDuration;
 unsigned int uiCount;
 unsigned int uiMode;
} ETHCollision;
typedef struct tagETHMII
{
 unsigned short	uiAddress;
 unsigned short	uiRegister;
 unsigned short	uiValue;
} ETHMII;
typedef FSTProtocolParameters ETHProtocolParameters;
typedef struct tagETHVLAN
{
		unsigned short	uiTPID;
		unsigned char 	ucPRI;
		unsigned char	ucCFI;
		unsigned short	uiVID;
} ETHVLAN;
typedef struct tagETHLink
{
		short iSpeed;
		short iDuplex;
		short iFlowControl;
		short iMode;
		short iTimeout;
		short iRetryDecision;
		short iReserved[1018];
} ETHLink;
typedef struct tagETHRSMII
{
	unsigned char ucRSMIISelect;
	unsigned char ucMDIOAccessSelect;
	unsigned char ucReserved[4];
} ETHRSMII;
typedef struct tagNSPortTransmit
{
		unsigned char	ucTransmitMode;
		unsigned char	ucScheduleMode;
		unsigned long	ulInterFrameGap;
		unsigned long	ulInterBurstGap;
		unsigned short uiGapScale;
		unsigned long	ulBurstCount;
		unsigned long	ulMultiBurstCount;
		unsigned char	ucRandomGapEnable;
		unsigned long	ulRandomSeed;
		unsigned long	ulMinRandomGap;
		unsigned long	ulMaxRandomGap;
		unsigned long	ulMinRandomLength;
		unsigned long	ulMaxRandomLength;
		unsigned char	ucReserved[64];
} NSPortTransmit;
typedef struct tagETHCardInfo
{
 unsigned short	uiCardModel;
 char					szCardModel[32];
 char					cPortID;
 unsigned short	uiPortType;
 unsigned long		ulPortProperties;
 unsigned long		ulHWVersions[32];
} ETHCardInfo;
typedef struct tagETHCounterInfo
{
 unsigned long	ulRxFrames;
 unsigned long	ulTxFrames;
 unsigned long	ulCollisions;
 unsigned long	ulRxTriggers;
 unsigned long	ulRxBytes;
 unsigned long	ulCRCErrors;
 unsigned long	ulAlignErrors;
 unsigned long	ulOversize;
 unsigned long	ulUndersize;
 unsigned long	ulTxFrameRate;
 unsigned long	ulRxFrameRate;
 unsigned long	ulCRCErrorRate;
 unsigned long	ulOversizeRate;
 unsigned long	ulUndersizeRate;
 unsigned long	ulCollisionErrorRate;
 unsigned long	ulAlignErrorRate;
 unsigned long	ulRxTriggerRate;
 unsigned long	ulRxByteRate;
} ETHCounterInfo;
typedef struct tagETHEnhancedCounterInfo
{
		unsigned int	uiMode;
		unsigned int	uiPortType;
		unsigned long	ulMask1;
		unsigned long	ulMask2;
		unsigned long	ulData[64];
} ETHEnhancedCounterInfo;
typedef struct tagETHEnhancedStatusInfo
{
 unsigned long	ulStatus;
} ETHEnhancedStatusInfo;
typedef struct tagETHLatencyInfo
{
 unsigned long	ulLatency;
} ETHLatencyInfo;
typedef ETHMII ETHMIIInfo;
typedef struct tagETHExtendedCardInfo
{
		unsigned long ulLinkStateChanges;
		unsigned long ulTxMgmtFrames;
		unsigned long ulRxMgmtFrames;
		unsigned long ulRxARPRequests;
		unsigned long ulTxARPRequests;
		unsigned long ulTxARPReplies;
		unsigned long ulRxARPReplies;
		unsigned long ulTxPingReplies;
		unsigned long ulTxPingRequests;
		unsigned long ulRxPingRequests;
		unsigned long ulRxPingReplies;
		unsigned long ulRxVLANFrames;
		unsigned long ulRxIPFrames;
		unsigned long ulIPChecksumErrors;
		unsigned long ulMgmtFrameCRCErrors;
		unsigned long ulMgmtFrameIPChecksumErrors;
		unsigned long ulMgmtFrameUnknown;
		unsigned long ulTimecount;
		unsigned long ulReceiveErrors;
		unsigned long ulFalseCarrierSense;
		unsigned long ulRxNOKs;
		unsigned long ulExtendedPHYStatus;
		unsigned long ulReserved[2];
} ETHExtendedCardInfo;
typedef struct tagETHQoSCounterInfo
{
		U64	u64RxTriggers[8];
		unsigned long	ulReserved[4];
} ETHQoSCounterInfo;
typedef struct tagETHExtendedCounterInfo {
	U64				u64RxVLANFrames;
	U64				u64RxIPFrames;
	U64				u64RxIPChecksumErrors;
	unsigned long	ulTxARPReplies;
	unsigned long	ulRxARPReplies;
	unsigned long	ulTxARPRequests;
	unsigned long	ulRxARPRequests;
	unsigned long	ulTxPingReplies;
	unsigned long	ulRxPingReplies;
	unsigned long	ulTxPingRequests;
	unsigned long	ulRxPingRequests;
	U64				u64RxDataIntegrityErrors;
	U64				u64TxSignatureFrames;
	U64				u64RxSignatureFrames;
	unsigned long	ulReserved[12];
} ETHExtendedCounterInfo;
// # 1299 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/frmitems.h" 1 3
typedef struct tagFrameSpec
{
   int   iEncap;
   int   iSize;
   int   iProtocol;
	int	iPattern;
}FrameSpec_Type;
// # 1305 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/l2items.h" 1 3
typedef struct tagL2StatsInfo
{
	U64				u64TxFrame;
	U64				u64TxByte;
	U64				u64TxTrigger;
	unsigned long	ulTxLatency;
	U64				u64RxFrame;
	U64				u64RxByte;
	U64				u64RxTrigger;
	unsigned long	ulRxLatency;
	U64				u64RxCRCError;
	U64				u64RxOversize;
	U64				u64RxUndersize;
} L2StatsInfo;
typedef struct tagL2RateInfo
{
	unsigned long	ulTxFrameRate;
	unsigned long	ulTxByteRate;
	unsigned long	ulTxTriggerRate;
	unsigned long	ulRxFrameRate;
	unsigned long	ulRxByteRate;
	unsigned long	ulRxTriggerRate;
	unsigned long	ulRxCRCErrorRate;
	unsigned long	ulRxOversizeRate;
	unsigned long	ulRxUndersizeRate;
} L2RateInfo;

// # 1311 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/positems.h" 1 3
//
typedef struct tagPOSCardLineConfig
{
	unsigned char	ucCRC32Enabled;
	unsigned char	ucScramble;
   unsigned short uiSONETAlarmError;
} POSCardLineConfig;

typedef struct tagPOSCardPortEncapsulation
{
	unsigned char	ucEncapStyle;
	char			Pad[3];
} POSCardPortEncapsulation;

typedef struct tagPOSCardSetSpeed
{
	unsigned short	uiSpeed;
} POSCardSetSpeed;

typedef struct tagPOSCardGetSpeedInfo
{
	unsigned short	uiSpeed;
	unsigned short	uiSpeedCap;
	unsigned short	uiTransMode;
} POSCardGetSpeedInfo;

typedef struct tagPOSSonetPayloadConfig
{
		unsigned char ucType;
		unsigned char ucReserved[7];
} POSSonetPayloadConfig;

typedef struct tagPOSTrigger
{
 unsigned char ucTrigger1Mode;
 unsigned char ucTrigger1Range;
 unsigned short uiTrigger1Offset;
 unsigned char ucTrigger1Data[8];
 unsigned char ucTrigger1Mask[8];
 unsigned char ucTrigger2Mode;
 unsigned char ucTrigger2Range;
 unsigned short uiTrigger2Offset;
 unsigned char ucTrigger2Data[8];
 unsigned char ucTrigger2Mask[8];
 unsigned char ucTriggerMode;
 unsigned char ucReserved;
} POSTrigger;

// # 1312 "/usr/local/include/et1000.h" 2
// # 1 "/usr/local/include/pppitems.h" 1 3
typedef struct tagPPPParamCfg
{
	unsigned long	ulpppInstance;
	unsigned long	ulpppCount;
	unsigned short	uipppWeWish;
	unsigned short	uipppWeMust;
	unsigned short	uipppWeCan;
	unsigned char	ucpppEnablePPP;
	unsigned char	ucpppCHAPAlgo;
	unsigned short	uipppMRU;
	unsigned short	uipppMaxFailure;
	unsigned short	uipppMaxConfigure;
	unsigned short	uipppMaxTerminate;
	unsigned long	ulpppMagicNumber;
	unsigned char	ucpppOurID[32];
	unsigned char	ucpppOurPW[32];
	unsigned char	ucpppPeerID[32];
	unsigned char	ucpppPeerPW[32];
	unsigned char	ucpppIPEnable;
	unsigned char	ucpppNegotiateIPAddr;
	unsigned short	uipppIPCompress;
	unsigned char	ucpppOurIPAddr[4];
	unsigned char	ucpppPeerIPAddr[4];
	unsigned long	ulpppIPXNet;
	unsigned char	ucpppIPXEnable;
	unsigned char	ucpppIPXNode[6];
	unsigned char	ucReserved;
	unsigned short	uipppIPXCompress;
	unsigned short	uipppIPXRoutingProt;
	unsigned short	uipppRestartTimer;
	unsigned short	uipppRetryCount;
	unsigned char	ucModFrame;
	unsigned char	ucReserved1;
	unsigned char	ucMode;
	unsigned char	ucTimer;
	unsigned short	uiRetry;
	unsigned short	uiOptions;
	unsigned char	ucSourceMAC[6];
	unsigned char	ucDestMAC[6];
	unsigned short	uiServiceNameLen;
	unsigned char	ucServiceName[16];
	unsigned short	uiAcNameLen;
	unsigned char	ucAcName[16];
	unsigned long	ulReserved[2];
} PPPParamCfg;

typedef struct tagPPPControlCfg
{
	unsigned long	ulpppInstance;
	unsigned long	ulpppCount;
	unsigned char	ucpppAction;
	unsigned char	ucpppLCPPassiveMode;
	unsigned char	ucpppIPCPPassiveMode;
	unsigned char	ucReserved;
	unsigned long	ulpppEchoFreq;
	unsigned long	ulpppEchoErrFreq;
   unsigned long	ulpppInterConnDelay;
	unsigned long	ulReserved[3];
} PPPControlCfg;

typedef struct tagPPPDelCfg {
	unsigned long	ulpppInstance;
	unsigned long	ulpppCount;
} PPPDelCfg;

typedef struct tagPPPStatusInfo
{
	unsigned long	ulpppInstance;
	unsigned long	ulpppCount;
	unsigned char	ucppplcpState;
	unsigned char	ucpppipcpState;
	unsigned char	ucpppipxcpState;
	unsigned char	ucppplcpFailCode;
	unsigned long	ulpppMagicNumber;
	unsigned char	ucpppOurIPAddr[4];
	unsigned char	ucpppPeerIPAddr[4];
	unsigned long	ulpppWeGot;
	unsigned long	ulpppWeAcked;
	unsigned short	uipppMRU;
	unsigned short	uipppMTU;
	U64		ullpppLatency;
	U64		ullpppTotalLatency;
	unsigned char	ucState;
	unsigned char	ucMode;
	unsigned short	uiSessionID;
	unsigned char	ucSourceMAC[6];
	unsigned char	ucDestMAC[6];
	unsigned long	ulReserved[8];
} PPPStatusInfo;

typedef struct tagPPPStatsInfo {
	unsigned long	ulpppInstance;
	unsigned long	ulpppCount;
	unsigned long	ultimestamp;
	unsigned long	ullcpConfReqSent;
	unsigned long	ullcpConfAckSent;
	unsigned long	ullcpConfNakSent;
	unsigned long 	ullcpConfRejectSent;
	unsigned long	ullcpTermReqSent;
	unsigned long	ullcpTermAckSent;
	unsigned long	ullcpProtoRejectSent;
	unsigned long	ullcpEchoReqSent;
	unsigned long	ullcpEchoReplySent;
	unsigned long	ullcpEchoReqErrSent;
	unsigned long	ullcpEchoReplyErrSent;
	unsigned long	ullcpDiscardReqSent;
	unsigned long	ullcpCodeRejectSent;
	unsigned long	ullcpResetReqSent;
	unsigned long	ullcpResetAckSent;
	unsigned long	ullcpPAPReqSent;
	unsigned long	ullcpPAPAckSent;
	unsigned long	ullcpPAPNakSent;
	unsigned long	ullcpCHAPChlMSSent;
	unsigned long	ullcpCHAPChlMD5Sent;
	unsigned long	ullcpCHAPRspMSSent;
	unsigned long	ullcpCHAPRspMD5Sent;
	unsigned long	ullcpCHAPSuccessSent;
	unsigned long	ullcpCHAPFailSent;
	unsigned long	ullcpConfReqRcvd;
	unsigned long	ullcpConfAckRcvd;
	unsigned long	ullcpConfNakRcvd;
	unsigned long	ullcpConfRejectRcvd;
	unsigned long	ullcpTermReqRcvd;
	unsigned long	ullcpTermAckRcvd;
	unsigned long	ullcpProtoRejectRcvd;
	unsigned long	ullcpEchoReqRcvd;
	unsigned long	ullcpEchoReplyRcvd;
	unsigned long	ullcpEchoReqErrRcvd;
	unsigned long	ullcpEchoReplyErrRcvd;
	unsigned long	ullcpDiscardReqRcvd;
	unsigned long	ullcpCodeRejectRcvd;
	unsigned long	ullcpResetReqRcvd;
	unsigned long	ullcpResetAckRcvd;
	unsigned long	ullcpPAPReqRcvd;
	unsigned long	ullcpPAPAckRcvd;
	unsigned long	ullcpPAPNakRcvd;
	unsigned long	ullcpCHAPChlMSRcvd;
	unsigned long	ullcpCHAPChlMD5Rcvd;
	unsigned long	ullcpCHAPRspMSRcvd;
	unsigned long	ullcpCHAPRspMD5Rcvd;
	unsigned long	ullcpCHAPSuccessRcvd;
	unsigned long	ullcpCHAPFailRcvd;
	unsigned long	ulReserved[16];
} PPPStatsInfo;

 typedef struct tagPPPoEStatsInfo {
	unsigned long	ulStreamIndex;
	unsigned long	ulSent;
	unsigned long	ulReceived;
	unsigned long	ulDropped;
 } PPPoEStatsInfo;

typedef struct 	tagPPPParamsCopy
{
	unsigned short	uipppSrcStrNum;
	unsigned short	uipppDstStrNum;
	unsigned short	uipppDstStrCount;
	unsigned short	uiReserved;
	unsigned long	ulReserved;
} PPPParamsCopy;

typedef struct 	tagPPPParamsModify
{
	unsigned short	uipppStartStrNum;
	unsigned short	uipppStrCount;
	unsigned short	uipppParamItemID;
	unsigned short	uipppParamCount;
	unsigned char	ucpppData[2048 ];
} PPPParamsModify;

typedef struct 	tagPPPParamsFill
{
	unsigned short	uipppSrcStrNum;
	unsigned short	uipppDstStrNum;
	unsigned short	uipppDstStrCount;
	unsigned short	uipppParamItemID;
	unsigned char	ucpppDelta[32 ];
} PPPParamsFill;

typedef struct tagPPPStatusSearchInfo
{
	unsigned short	uipppStartIndex;
	unsigned short	uipppCount;
	unsigned short	uipppReturnItemId;
	unsigned short	uipppSearchItemId;
	U64	ullpppSearchRangeLow;
	U64	ullpppSearchRangeHigh;
	unsigned short	uipppReturnItemSize;
	unsigned short	uipppReserved;
	U64	ullpppItem[2048];
} PPPStatusSearchInfo;

typedef struct
	{
	int Hub;
	int TransmitSlot;
	int ReceiveSlot[20];
	int Offset;
	int Range;
	unsigned char Pattern[12];
	} SetLatencyStructure;

%pragma no_default

//%pragma(python) include="shadow_add.py"

