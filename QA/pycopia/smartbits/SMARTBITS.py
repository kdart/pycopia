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

PORT_A = 1
PORT_B = 0

MFPORT_A = 0
MFPORT_B = 1

LOOP_PORT_A = 0
LOOP_PORT_B = 1

CAPTURE_NONE = 0x0000
CAPTURE_ALL = 0xFFFF
CAPTURE_ERRS_RXTRIG = 0xFFFF
CAPTURE_ANY = 0x0800
CAPTURE_NOT_GOOD = 0x0200
CAPTURE_GOOD = 0x0100
CAPTURE_RXTRIG = 0x0001
CAPTURE_CRC = 0x0002
CAPTURE_ALIGN = 0x0004
CAPTURE_OVERSIZE = 0x0008
CAPTURE_UNDERSIZE = 0x0010
CAPTURE_COLLISION = 0x0020

CAPTURE_ENTIRE_PACKET = 0
CAPTURE_RANGE = 1
CAPTURE_OFF = 2

TIME_TAG_ON = 1
TIME_TAG_OFF = 0

BUFFER_CONTINUOUS = 0
BUFFER_ONESHOT = 1

COLLISION_OFF = 0
COLLISION_LONG = 1
COLLISION_ADJ = 2
CORP_A = 3
CORP_B = 4
ETCOLLISION_MAX = 4

SYMBOL_OFF = 0
SYMBOL_ON = 1

ETCOM1 = 0
ETCOM2 = 1
ETCOM3 = 2
ETCOM4 = 3
ETCOM5 = 4
ETCOM6 = 5
ETCOM7 = 6
ETCOM8 = 7

ETMAXCOM = 50

ET_ON = 1
ET_OFF = 0

ETBURST_ON = 1
ETBURST_OFF = 0

ETGAP_100NS = 1
ETGAP_1US = 0

ETLOOPBACK_ON = 1
ETLOOPBACK_OFF = 0

ETCRC_OFF = 0
ETCRC_ON = 1
ETCRC_NONE = 2

ETRUN_STOP = 0
ETRUN_STEP = 1
ETRUN_RUN = 2

ETVFD_ENABLE = 1
ETVFD_DISABLE = 0

ETLNM_ON = 1
ETLNM_OFF = 0

ETBAUD_2400 = 0
ETBAUD_4800 = 1
ETBAUD_9600 = 2
ETBAUD_19200 = 3
ETBAUD_38400 = 4

ETLOCALMODE = 0
ETREMOTEMODE = 1

ETRUN = 2
ETSTEP = 1
ETSTOP = 0
HTRUN = 2
HTSTEP = 1
HTSTOP = 0

RUN_NON_BLOCKING_FLAG = 0x0100
RUN_NON_BLOCKING_MASK = 0x00FF

ETSELA = 0
ETSELB = 1
ETPINGPONG = 2

#  constants for ETGetController 
CONTROLLER_UNKNOWN = 0
CONTROLLER_ET1000 = 1
CONTROLLER_SMB1000 = 2
CONTROLLER_SMB2000 = 3
CONTROLLER_SMB6000 = 4
CONTROLLER_SMB200 = 5
CONTROLLER_SMB600 = 6

# constants for ETGetProductFamily 
FAMILY_UNKNOWN = 0
FAMILY_ET1000 = 1
FAMILY_SMB2000 = 2
FAMILY_SMB6000 = 3

# constants for NSSetPortMappingMode 
PORT_MAPPING_COMPATIBLE = 0
PORT_MAPPING_NATIVE = 1

# constants for iReserve parameter to NSSocketLink
RESERVE_NONE = 0
RESERVE_ALL = 1

# constants for HTSlotOwnership 
SLOT_RESERVED_BY_OTHER = 0
SLOT_RESERVED_BY_USER = 1
SLOT_AVAILABLE = 2


ETSTORESETUP = 0
ETRECALLSETUP = 1

CT_NOT_PRESENT = 0
CT_ACTIVE = 1
CT_PASSIVE = 2
CT_FASTX = 3
CT_TOKENRING = 4
CT_VG = 5
CT_L3 = 6
CT_ATM = 7
CT_GIGABIT = 8
CT_ATM_SIGNALING = 9
CT_WAN_FRAME_RELAY = 10
CT_POS = 11
CT_MAX_CARD_TYPE = CT_POS

CM_UNKNOWN = -1
CM_NOT_PRESENT = 0
CM_SE_6205 = 1
CM_SC_6305 = 2
CM_ST_6405 = 3
CM_ST_6410 = 4
CM_SX_7205 = 5
CM_SX_7405 = 6
CM_SX_7410 = 7
CM_TR_8405 = 8
CM_VG_7605 = 9
CM_L3_6705 = 10
CM_AT_9025 = 11
CM_AT_9155 = 12
CM_AS_9155 = 13
CM_GX_1405 = 14
CM_WN_3405 = 15
CM_AT_9015 = 16
CM_AT_9020 = 17
CM_AT_9034 = 18
CM_AT_9045 = 19
CM_AT_9622 = 20
CM_L3_6710 = 21
CM_SX_7210 = 22
CM_ML_7710 = 23
CM_ML_5710A = 24
CM_WN_3415 = 25
CM_WN_3420 = 26
CM_LAN_6200 = 27
CM_LAN_6100 = 28
CM_LAN_3200 = 29
CM_POS_6500A = 30
CM_GX_1420A = 31
CM_LAN_6201A = 32
CM_AT_9155C = 33
CM_WN_3445A = 34
CM_POS_6502A = 35
CM_POS_6500B = 36
CM_GX_1420B = 37
CM_LAN_6201B = 38
CM_AT_9045B = 39
CM_LAN_6101 = 40
CM_POS_6505A = 41
CM_LAN_6301A = 42
CM_WN_3442A = 43
CM_WN_3441A = 44
CM_LAN_3150A = 45
CM_AT_9034B = 46
CM_LAN_6311A = 47
CM_POS_6504A = 48
CM_LAN_6300A = 49
CM_LAN_6310A = 50
CT_MAX_CARD_MODELS = CM_LAN_6310A


#*****************************************/
#* MII-related definitions */
#*****************************************/

# register names 
MII_REGISTER_CONTROL = 0
MII_REGISTER_STATUS = 1
MII_REGISTER_AN_ADVERTISEMENT = 4
MII_REGISTER_AN_LINK_PARTNER = 5
MII_REGISTER_AN_EXPANSION = 6
MII_REGISTER_1000_CONTROL = 9
MII_REGISTER_1000_STATUS = 10

# register 0 (control register) bits 
MII_CTRL_RESET = 0x8000
MII_CTRL_LOOPBACK = 0x4000
MII_CTRL_SPEED = 0x2000
MII_CTRL_AUTONEGOTIATE = 0x1000
MII_CTRL_POWERDOWN = 0x0800
MII_CTRL_ISOLATE = 0x0400
MII_CTRL_RESTARTAUTONEGOTIATE = 0x0200
MII_CTRL_DUPLEXMODE = 0x0100
MII_CTRL_COLLISIONTEST = 0x0080
MII_CTRL_SPEED_MSB = 0x0040
MII_CTRL_SPEED_LSB = MII_CTRL_SPEED

# register 1 definitions 
MII_STATUS_EXT_CAP = 0x0001
MII_STATUS_JABBER_DETECT = 0x0002
MII_STATUS_LINK = 0x0004
MII_STATUS_AN_ABILITY = 0x0008
MII_STATUS_REMOTE_FAULT = 0x0010
MII_STATUS_AN_COMPLETE = 0x0020
MII_STATUS_MF_PREAMBLE_SUP = 0x0040
MII_STATUS_EXT_STATUS = 0x0100
MII_STATUS_100BASE_T2_HALF = 0x0200
MII_STATUS_100BASE_T2_FULL = 0x0400
MII_STATUS_10_HALF = 0x0800
MII_STATUS_10_FULL = 0x1000
MII_STATUS_100BASE_X_HALF = 0x2000
MII_STATUS_100BASE_X_FULL = 0x4000
MII_STATUS_100BASE_T4 = 0x8000

# register 4 & 5 definitions 
MII_AN_10BASE_T = 0x0020
MII_AN_10BASE_T_FULL = 0x0040
MII_AN_100BASE_TX = 0x0080
MII_AN_100BASE_TX_FULL = 0x0100
MII_AN_100BASE_T4 = 0x0200
MII_AN_FLOW_CONTROL = 0x0400
MII_AN_REMOTE_FAULT = 0x2000
MII_AN_ACKNOWLEDGE = 0x4000
MII_AN_NEXT_PAGE = 0x8000

# register 6
MII_AN_LINK_PARTNER = 0x0001

# register 9 definitions 
MII_CONTROL9_1000BASE = 0x0080
MII_CONTROL9_1000BASE_FULL = 0x0100

# register 10 definitions 
MII_STATUS10_1000BASE = 0x0080
MII_STATUS10_1000BASE_FULL = 0x0100


# Failure Codes 
UNSPECIFIED_ERROR = -1
PORT_NOT_LINKED = -2
UNLINK_FAILED = -3
INCORRECT_MODE = -4
PARAMETER_RANGE = -5
PACKET_NOT_AVAILABLE = -6
SERIAL_PORT_DATA = -7
ET1000_OUT_OF_SYNC = -8
PACKET_NOT_FOUND = -9
FUNCTION_ABORT = -10
ACTIVE_HUB_NOT_INITIALIZED = -11
ACTIVE_HUB_NOT_PRESENT = -12
WRONG_HUB_CARD_TYPE = -13
MEMORY_ALLOCATION_ERROR = -14
UNSUPPORTED_INTERLEAVE = -15
PORT_ALREADY_LINKED = -16
HUB_SLOT_PORT_UNAVAILABLE = -17
GROUP_HUB_SLOT_PORT_ERROR = -18
REENTRANT_ERROR = -19
DEVICE_NOT_FOUND_ERROR = -20
PORT_RELINK_REQUIRED = -21
DEVICE_NOT_READY = -22
GROUP_NOT_HOMOGENEOUS = -23
INVALID_GROUP_COMMAND = -24
ERROR_SMARTCARD_INIT_FAILED = -25
SOCKET_FAILED = -26
SOCKET_TIMEOUT = -27
COMMAND_RESPONSE_ERROR = -28
CRC_ERROR = -29
INVALID_LINK_PORT_TYPE = -30
INVALID_SYNC_CONFIGURATION = -31
HIGH_DENSITY_CONTROLLER_ERROR = -32
HIGH_DENSITY_CARD_ERROR = -33
DATA_NOT_AVAILABLE = -34
UNSUPPORTED_PLATFORM = -35
FILE_IO_ERROR = -36
MULTI_USER_CONFLICT = -37

SERIAL_PORT_TIMEOUT = -98

# Errors occurring in the Tcl interface [will we see these in python?]
NSTCL_PARAMETER_TYPE = -501
NSTCL_INVALID_MSG_FUNC = -502
NSTCL_PARAMETER_RANGE = -503
NSTCL_STRUCT_NOT_DEFINED = -504


# Non-fatal errors 
UNSUPPORTED_COMMAND = -1001
UPDATED_FIRMWARE_NEEDED = -1002

# Non-fatal errors specific to autonegotiation 
AN_LINK_NOT_NEGOTIATED = -1100
AN_NO_EXTENDED_CAPABILITY = -1101
AN_LINK_PARTNER_INCAPABLE = -1102
AN_INVALID_MII_ADDRESS = -1103
AN_SETTINGS_NOT_VERIFIED = -1104

EXPRESS_UNLINK = 1
NORMAL_UNLINK = 0

#---------------------- SmartCard Objects flags -----------
SMARTCARD_STATUS_OK = 0

#--------------------- BNC Configuration ------------------
ETBNC_1 = 1
ETBNC_2 = 2
ETBNC_3 = 3

ETBNC_INPUT = 0
ETBNC_RXEA = 1
ETBNC_RXEB = 2
ETBNC_RCKA = 3
ETBNC_RCKB = 4
ETBNC_RDATA = 5
ETBNC_RDATB = 6
ETBNC_TXEA = 7
ETBNC_TXEB = 8
ETBNC_TDAT = 9
ETBNC_COLLISIONA = 10
ETBNC_COLLISIONB = 11
ETBNC_CRCA = 12
ETBNC_CRCB = 13
ETBNC_UNDRA = 14
ETBNC_UNDRB = 15
ETBNC_OVRA = 16
ETBNC_OVRB = 17
ETBNC_ALA = 18
ETBNC_ALB = 19
ETBNC_TXTRIG = 20
ETBNC_RXTRIG = 21
ETBNC_10MHZ = 22
ETBNC_10MHZINV = 23
ETBNC_20MHZ = 24
ETBNC_20MHZINV = 25
ETBNC_EXTCLK = 26
ETBNC_EXTCLKINV = 27

ETBNC_MAX = 27
ETBNC_JET210 = 99

#---------------- Types of ET-1000 Transmit Data Patterns ------------
ETDP_ALLZERO = 0
ETDP_ALLONE = 1
ETDP_RANDOM = 2
ETDP_AAAA = 3
ETDP_5555 = 4
ETDP_F0F0 = 5
ETDP_0F0F = 6
ETDP_00FF = 7
ETDP_FF00 = 8
ETDP_0000FFFF = 9
ETDP_FFFF0000 = 10
ETDP_00000000FFFFFFFF = 11
ETDP_FFFFFFFF00000000 = 12
ETDP_INCR8 = 13
ETDP_INCR16 = 14
ETDP_DECR8 = 15
ETDP_DECR16 = 16
ETDP_FULLCUSTOM = 17
MAX_DATA_PATTERN = ETDP_FULLCUSTOM

#----------------- Receive Error and Trigger LED Parameters -----------
RXLED_ANY = 0
RXLED_ERRORA = 1
RXLED_ERRORB = 2
RXLED_ERRORAB = 3
RXLED_UNDERSIZEA = 4
RXLED_UNDERSIZEB = 5
RXLED_UNDERSIZEAB = 6
RXLED_OVERSIZEA = 7
RXLED_OVERSIZEB = 8
RXLED_OVERSIZEAB = 9
RXLED_ALIGNA = 0x0a
RXLED_ALIGNB = 0x0b
RXLED_ALIGNAB = 0x0c
RXLED_NONE = 0

TRIGLED_MISSING = 0
TRIGLED_TXRX = 1
TRIGLED_RX = 2
TRIGLED_TX = 3

#----------------- Preamble Parameters -------------
ETPREAMBLE_MAX = 128
ETPREAMBLE_MIN = 10

#----------------- ET-1000 Multifunction Counters ---------------
ETMF_PACKET_LENGTH = 0
ETMF_RXTRIG_COUNT = 1
ETMF_TXTRIG_COUNT = 2
ETMF_TIME_ROUNDTRIP = 3
ETMF_TIME_PORT2PORT = 4
ETMF_RXTRIG_RATE = 5
ETMF_TXTRIG_RATE = 6
ETMF_PREAMBLE_COUNT = 7
ETMF_GAP_TIME = 8
ETMF_SQE_COUNT = 9
ETMF_TOTAL_LENGTH = 10

ETMF_MAX = ETMF_TOTAL_LENGTH

#----------------------- Hub Tester ----------------------
MAX_HUBS = 4
MAX_SLOTS = 20
MAX_PORTS = 4

MAX_HUBS_HD = 4
MAX_SLOTS_HD = 32
MAX_PORTS_HD = 16

MAX_HUBS_SMB200 = 1
MAX_SLOTS_SMB200 = 4

MAX_MAX_HUBS = MAX_HUBS_HD
MAX_MAX_SLOTS = MAX_SLOTS_HD
MAX_MAX_PORTS = MAX_PORTS_HD

MAX_SUBSYSTEMS = 2

PORTS_PER_ACTIVE_CARD = 1
PORTS_PER_PASSIVE_CARD = 2

MAX_PORT_IDS = (MAX_MAX_HUBS*MAX_MAX_SLOTS*MAX_MAX_PORTS)
MAX_ACTIVE_SLOTS = (MAX_MAX_HUBS*MAX_MAX_SLOTS*PORTS_PER_ACTIVE_CARD)
MAX_PASSIVE_SLOTS = (MAX_MAX_HUBS*MAX_MAX_SLOTS*PORTS_PER_PASSIVE_CARD)
MAX_TOTAL_PORTS = (MAX_MAX_HUBS*MAX_MAX_SLOTS*MAX_MAX_PORTS)
MAX_SLOTLIST_SIZE = 255
MAX_GROUP_SIZE = 450
MAX_VFD_SIZE = 2048
MAX_FILL_PATTERN_SIZE = 2044

RESET_FULL = 1
RESET_PARTIAL = 2

HTLED_OFF = 0
HTLED_RED = 1
HTLED_GREEN = 2
HTLED_ORANGE = 3

HTLED_TXRED = 0x0001
HTLED_TXGREEN = 0x0002
HTLED_COLLRED = 0x0004
HTLED_COLLGREEN = 0x0008
HTLED_RXRED = 0x0010
HTLED_RXGREEN = 0x0020

CA_SIGNALRATE_10MB = 0x00000001L
CA_SIGNALRATE_100MB = 0x00000002L
CA_DUPLEX_FULL = 0x00000004L
CA_DUPLEX_HALF = 0x00000008L
CA_CONNECT_MII = 0x00000010L
CA_CONNECT_TP = 0x00000020L
CA_CONNECT_BNC = 0x00000040L
CA_CONNECT_AUI = 0x00000080L
CA_CAN_ROUTE = 0x00000100L
CA_VFDRESETCOUNT = 0x00000200L
CA_SIGNALRATE_4MB = 0x00000400L
CA_SIGNALRATE_16MB = 0x00000800L
CA_CAN_COLLIDE = 0x00001000L
CA_SIGNALRATE_25MB = 0x00002000L
CA_SIGNALRATE_155MB = 0x00004000L
CA_BUILT_IN_ADDRESS = 0x00008000L
CA_HAS_DEBUG_MONITOR = 0x00010000L
CA_SIGNALRATE_1000MB = 0x00020000L
CA_CONNECT_FIBER = 0x00040000L
CA_CAN_CAPTURE = 0x00080000L
CA_ATM_SIGNALING = 0x00100000L
CA_CONNECT_V35 = 0x00200000L
CA_SIGNALRATE_8MB = 0x00400000L
CA_SIGNALRATE_622MB = 0x00800000L
CA_SIGNALRATE_45MB = 0x01000000L
CA_SIGNALRATE_34MB = 0x02000000L
CA_SIGNALRATE_1_544MB = 0x04000000L
CA_SIGNALRATE_2_048MB = 0x08000000L
CA_HASVFDREPEATCOUNT = 0x10000000L
CA_CONNECT_USB = 0x20000000L
CA_TRANSCEIVER_MULTIMODE = 0x40000000L
CA_GBIC = 0x80000000L

# reference bit masks for standard SMB counters in HxGetEnhancedCounters()--use ulMask1 
SMB_STD_MASK = 0x000007FFL
SMB_STD_TXFRAMES = 0x00000001L
SMB_STD_TXBYTES = 0x00000002L
SMB_STD_TXTRIGGER = 0x00000004L
SMB_STD_RXFRAMES = 0x00000008L
SMB_STD_RXBYTES = 0x00000010L
SMB_STD_RXTRIGGER = 0x00000020L
SMB_STD_ERR_CRC = 0x00000040L
SMB_STD_ERR_ALIGN = 0x00000080L
SMB_STD_ERR_UNDERSIZE = 0x00000100L
SMB_STD_ERR_OVERSIZE = 0x00000200L
SMB_STD_ERR_COLLISION = 0x00000400L

# indices for referencing standard SMB counters in HxGetEnhancedCounters() 
ISMB_STD_TXFRAMES = 0
ISMB_STD_TXBYTES = 1
ISMB_STD_TXTRIGGER = 2
ISMB_STD_RXFRAMES = 3
ISMB_STD_RXBYTES = 4
ISMB_STD_RXTRIGGER = 5
ISMB_STD_ERR_CRC = 6
ISMB_STD_ERR_ALIGN = 7
ISMB_STD_ERR_UNDERSIZE = 8
ISMB_STD_ERR_OVERSIZE = 9
ISMB_STD_ERR_COLLISION = 10

# reference bit masks for VG/AnyLan enhanced counters in HxGetEnhancedCounters()--use ulMask2 
SMB_VG_INV_PKTMARK = 0x00000001
SMB_VG_ERR_PKT = 0x00000002
SMB_VG_TRANSTRAIN_PKT = 0x00000004
SMB_VG_PRIO_PROM_PKT = 0x00000008
SMB_VG_MASK = 0x0000000F

# indices for referencing the enhanced counters in HxGetEnhancedCounters() 
ISMB_VG_INV_PKTMARK = 32
ISMB_VG_ERR_PKT = 33
ISMB_VG_TRANSTRAIN_PKT = 34
ISMB_VG_PRIO_PROM_PKT = 35

# reference bit masks for Layer 3 enhanced counters in HxGetEnhancedCounters()--use ulMask2 
L3_MASK = 0x00004FFFL
L3_FRAMEERROR = 0x00000001L
L3_TX_RETRIES = 0x00000002L
L3_TX_EXCESSIVE = 0x00000004L
L3_TX_LATE = 0x00000008L
L3_RX_TAGS = 0x00000010L
L3_TX_STACK = 0x00000020L
L3_RX_STACK = 0x00000040L
L3_ARP_REQ = 0x00000080L
L3_ARP_SEND = 0x00000100L
L3_ARP_REPLIES = 0x00000200L
L3_PINGREP_SENT = 0x00000400L
L3_PINGREQ_SENT = 0x00000800L
L3_PINGREQ_RECV = 0x00001000L
L3_DATA_INTEGRITY_ERRORS = 0x00002000L
L3_IP_CHECKSUM_ERRORS = 0x00004000L


# indices for referencing the enhanced counters in HxGetEnhancedCounters() 
IL3_FRAMEERROR = 32
IL3_TX_RETRIES = 33
IL3_TX_EXCESSIVE = 34
IL3_TX_LATE = 35
IL3_RX_TAGS = 36
IL3_TX_STACK = 37
IL3_RX_STACK = 38
IL3_ARP_REQ = 39
IL3_ARP_SEND = 40
IL3_ARP_REPLIES = 41
IL3_PINGREP_SENT = 42
IL3_PINGREQ_SENT = 43
IL3_PINGREQ_RECV = 44
IL3_DATA_INTEGRITY_ERRORS = 45
IL3_IP_CHECKSUM_ERRORS = 46


# reference bit masks for ATM enhanced counters in HxGetEnhancedCounters()--use ulMask2 
ATM_MASK = 0x0007FFFFL
ATM_CELLS = 0x00000001L
ATM_CORRECTEDHEADERS = 0x00000002L
ATM_UNCORRECTABLEHEADERS = 0x00000004L
ATM_CELLSLOST = 0x00000008L
ATM_OUT_OF_SEQUENCE = 0x00000010L
ATM_MISDELIVERED = 0x00000020L
ATM_OAM_F4 = 0x00000040L
ATM_OAM_F5 = 0x00000080L
ATM_SIGNALING = 0x00000100L
ATM_CELL_ERROR_RATIO = 0x00000200L
ATM_SEVERE_ERROR_CB_RATIO = 0x00000400L
ATM_CELL_LOSS_RATIO = 0x00000800L
ATM_MISINSERTION = 0x00001000L
ATM_CELL_TRANSFER_DELAY = 0x00002000L
ATM_MEAN_CELL_TRANSFER_DELAY = 0x00004000L
ATM_CELL_DELAY_VARIATION = 0x00008000L
ATM_TX_CELLS = 0x00010000L
ATM_TX_AAL_PDU = 0x00020000L
ATM_TIMEOUT = 0x00040000L

# indices for referencing the enhanced counters in HxGetEnhancedCounters() 
IATM_CELLS = 32
IATM_CORRECTEDHEADERS = 33
IATM_UNCORRECTABLEHEADERS = 34
IATM_CELLSLOST = 35
IATM_OUT_OF_SEQUENCE = 36
IATM_MISDELIVERED = 37
IATM_OAM_F4 = 38
IATM_OAM_F5 = 39
IATM_SIGNALING = 40
IATM_CELL_ERROR_RATIO = 41
IATM_SEVERE_ERROR_CB_RATIO = 42
IATM_CELL_LOSS_RATIO = 43
IATM_MISINSERTION = 44
IATM_CELL_TRANSFER_DELAY = 45
IATM_MEAN_CELL_TRANSFER_DELAY = 46
IATM_CELL_DELAY_VARIATION = 47
IATM_TX_CELLS = 48
IATM_TX_AAL_PDU = 49
IATM_TIMEOUT = 50

# reference bit masks for Token Ring enhanced counters in HxGetEnhancedCounters()--use ulMask2 
TR_MASK = 0x001FFFFFL
TR_RXMAC = 0x00000001L
TR_RXABORTFRAMES = 0x00000002L
TR_LINEERRORS = 0x00000004L
TR_BURSTERRORS = 0x00000008L
TR_BADTOKEN = 0x00000010L
TR_PURGEEVENTS = 0x00000020L
TR_BEACONEVENTS = 0x00000040L
TR_CLAIMEVENTS = 0x00000080L
TR_INSERTIONS = 0x00000100L
TR_MAC_LINEERRORS = 0x00000200L
TR_MAC_INTERNALERRORS = 0x00000400L
TR_MAC_BURSTERRORS = 0x00000800L
TR_MAC_ACERRORS = 0x00001000L
TR_MAC_ABORTTX = 0x00002000L
TR_MAC_LOSTFRAME = 0x00004000L
TR_MAC_RXCONGESTED = 0x00008000L
TR_MAC_FRAMECOPIED = 0x00010000L
TR_MAC_FREQUENCYERROR = 0x00020000L
TR_MAC_TOKENERROR = 0x00040000L
TR_LATENCY = 0x00080000L
TR_TOKEN_RT = 0x00100000L

# indices for referencing the extended counters in HxGetEnhancedCounters() 
ITR_RXMAC = 32
ITR_RXABORTFRAMES = 33
ITR_LINEERRORS = 34
ITR_BURSTERRORS = 35
ITR_BADTOKEN = 36
ITR_PURGEEVENTS = 37
ITR_BEACONEVENTS = 38
ITR_CLAIMEVENTS = 39
ITR_INSERTIONS = 40
ITR_MAC_LINEERRORS = 41
ITR_MAC_INTERNALERRORS = 42
ITR_MAC_BURSTERRORS = 43
ITR_MAC_ACERRORS = 44
ITR_MAC_ABORTTX = 45
ITR_MAC_LOSTFRAME = 46
ITR_MAC_RXCONGESTED = 47
ITR_MAC_FRAMECOPIED = 48
ITR_MAC_FREQUENCYERROR = 49
ITR_MAC_TOKENERROR = 50
ITR_LATENCY = 51
ITR_TOKEN_RT = 52

# ------------------ TokenRing parameter values ------------------- 
TR_SPEED_4MBITS = 0
TR_SPEED_16MBITS = 1
TR_TOKEN_EARLY_RELEASE = 1
TR_TOKEN_DEFAULT = 0
TR_DUPLEX_FULL = 1
TR_DUPLEX_HALF = 0
TR_MODE_DEVICE = 1
TR_MODE_MAU = 0
TR_PROPERTY_ENTRY = 4

# ------------------ TokenRing Error bits ------------------- 
TR_ERR_FCS = 0x0001
TR_ERR_FRAME_COPY = 0x0002
TR_ERR_FRAME_BIT = 0x0004
TR_ERR_FRAME_FS = 0x0008
TR_ERR_ABORT_DELIMITER = 0x0010
TR_ERR_BURST = 0x0020

# ------------------ TokenRing FC byte values ------------------- 
TRFC_DEFAULT = 0x40
TRFC_PCFON = 0x01
TRFC_PCF_BEACON = 0x02
TRFC_PCF_CLAIMTOKEN = 0x03
TRFC_PCF_RINGPURGE = 0x04
TRFC_PCF_AMP = 0x05
TRFC_PCF_SMP = 0x06
TRFC_PCF_DAT = 0x01
TRFC_PCF_RRS = 0x01
TRFC_PCF_EXPRESSBUFFER = 0x01

# ------------------ VG card parameter values ------------------- 
VG_CFG_END_NODE = 0
VG_CFG_MASTER = 1
VG_CFG_NO_PRIO_PROMO = 0
VG_CFG_PRIORITY_PROMO = 1
VG_CFG_TOKENRING = 1
VG_CFG_ETHERNET = 0
VG_PROPERTY_ENTRY = 3

# ------------------ TokenRing Enhanced Status bits ------------------- 
TR_STATUS_ACCESSED = 0x000100L
TR_STATUS_BADSTREAM = 0x000200L
TR_STATUS_BURST_MODE = 0x000400L
TR_STATUS_BEACONING = 0x000800L
TR_STATUS_DEVICE = 0x001000L
TR_STATUS_EARLY_TOKEN_RELEASE = 0x002000L
TR_STATUS_FULL_DUPLEX = 0x004000L
TR_STATUS_16MB = 0x008000L
TR_STATUS_RING_ALIVE = 0x010000L
TR_STATUS_LATENCY_STABLE = 0x020000L
TR_STATUS_TRANSMITTING = 0x040000L

# ------------------ Gigabit Ethernet Enhanced Status bits ------------------- 
GIG_STATUS_LINK = 0x000200L
#                                               this is the only status bit 
#                                               supported by the LAN-6201 */
GIG_STATUS_TX_PAUSE = 0x000400L   # is pause holdoff in process 
GIG_STATUS_CAPTURED_FRAMES = 0x000800L   # are there captured frames 
GIG_STATUS_CAPTURE_STOPPED = 0x001000L   # is capture stopped 
GIG_STATUS_1420 = 0x002000L # is the card a GX-1420 
GIG_STATUS_1420B = 0x004000L # is the card a GX-1420B 
GIG_STATUS_100MHZ = 0x010000L # is the card at 100MHz speed 
GIG_STATUS_10MHZ = 0x020000L # is the card at 10MHz speed 

# ------------------ 100 MB SX-7410 Fast Ethernet Enhanced Status bits ------------------- 
FAST7410_STATUS_LINK = 0x000200L   # is link established 
FAST7410_STATUS_TX_PAUSE = 0x000400L   # is pause holdoff in process 

# ------------------ 10 MB Ethernet Layer 3 Enhanced Status bits ------------------- 
# this bit will be set if the 10 MB Layer 3 card is an L3-6710, else it is an L3-6705 
L3_STATUS_6710 = 0x080000L

# ------------------ 10 and 10/100 MB Ethernet Layer 3 and Multi-Layer Enhanced Status bits ------------------- 
L3_ARPS_NOT_RESOLVED = 0x100000 # if ARPS are not resolved for all streams 
L3_ARPS_STILL_TXING = 0x200000 # if ARPS are still transmitting 

#------------------- USB CARDs -------------------
L3_USB_PORT_ENABLED = 0x400000    # if USB Port is enabled.
L3_USB_PORT_LINKED = 0x800000    # if USB Port is linked to a USB device (enumeration was successful).


# ------------------ VG Enhanced Status bits ------------------- 
# this bit will be set if the mode is Ethernet, else it will be in Token Ring mode 
VG_STATUS_MODE = 0x000200L

# ------------------ WAN Frame Relay Enhanced Status bits ------------------- 
FR_STATUS_LINK_OK = 0x000200L   # is link established 
FR_STATUS_GROUP_MEMBER = 0x000400L   # set if Card is "grouped" 
FR_STATUS_UNI_UP = 0x008000L   # set if UNI is up 
FR_STATUS_EIA_DSR = 0x010000L   # set if DSR line is high 
FR_STATUS_EIA_CTS = 0x020000L   # set if CTS line is high 
FR_STATUS_EIA_DCD = 0x040000L   # set if DCD line is high 
FR_STATUS_EIA_TM = 0x080000L   # set if TM line is high 
FR_STATUS_EIA_DTR = 0x100000L   # set if DTR line is high 
FR_STATUS_EIA_RTS = 0x200000L   # set if RTS line is high 
FR_STATUS_EIA_RDL = 0x400000L   # set if RDL line is high 
FR_STATUS_EIA_LLB = 0x800000L   # set if LLB line is high 

# ------------------ SmartBits chassis (hub) identifiers ----------------- 
HTHUBID_1 = 1
HTHUBID_2 = 2
HTHUBID_3 = 3
HTHUBID_4 = 4
HTHUBID_ALL = 0

# ------------------ Data stream Transmission modes ------------------- 
CONTINUOUS_PACKET_MODE = 0
FIRST_TRANSMIT_MODE = CONTINUOUS_PACKET_MODE
SINGLE_BURST_MODE = 1
MULTI_BURST_MODE = 2
CONTINUOUS_BURST_MODE = 3
ECHO_MODE = 4
LAST_TRANSMIT_MODE = ECHO_MODE


#   Supported duplex modes of different SmartCards.
#   Not all cards support all duplex settings
#   See the SmartCard reference for supported settings

FULLDUPLEX_MODE = 0
HALFDUPLEX_MODE = 1


HTRECEIVE_OFF = 0

# ------------------ ET-1000 Port B transmit modes ------------------- 
HTTRANSMIT_OFF = 0
HTTRANSMIT_STD = 1
HTTRANSMIT_COL = 2

# ------------------ SmartCard Trigger params ------------------- 
HTTRIGGER_OFF = 0
HTTRIGGER_1 = 1
HTTRIGGER_2 = 2
HTTRIGGER_DEPENDENT = 3
HTTRIGGER_INDEPENDENT = 4
HTTRIGGER_ON = 4

# ------------------ SmartCard VFD params ------------------- 
HVFD_1 = 1
HVFD_2 = 2
HVFD_3 = 3

HVFD_NONE = 0
HVFD_RANDOM = 1
HVFD_INCR = 2
HVFD_DECR = 3
HVFD_ENABLED = 4
HVFD_STATIC = 5

# ------------- SmartCard Echo transmission mode control ------------ 
HTECHO_OFF = 0
HTECHO_ON = 1

# ------------------ SmartCard Latency params ------------------- 
HT_RUN_LATENCY = 0
HT_GET_LATENCY = 1

HT_LATENCY_OFF = 0
HT_LATENCY_RX = 1
HT_LATENCY_TX = 2
HT_LATENCY_REPORT = 3
HT_LATENCY_RXTX = 4

# ------------- Collision backoff aggressiveness values ------------- 
HT_CBA_DEFAULT = 0
HT_CBA_1 = 1
HT_CBA_2 = 2
HT_CBA_3 = 3
HT_CBA_4 = 4
HT_CBA_5 = 5
HT_CBA_6 = 6
HT_CBA_7 = 7
HT_CBA_8 = 8
HT_CBA_9 = 9
HT_CBA_10 = 10

# ------------- Library command debug and logging values ------------- 
ET_SECURE = 1
ET_NO_SECURE = 0

ET_CMDLOG_COMMANDS = 0x0001L # Display the input, outpu
#                                                        or comment data */
ET_CMDLOG_SHOW_IOTYPE = 0x0002L # Display input or outp
#                                                        prefix at start of each
#                                                        line */
ET_CMDLOG_TIMESTAMP = 0x0004L # Place timestamps at t
#                                                        start of each line
#                                                        indicating when command was
#                                                        sent or received */
ET_CMDLOG_APPEND = 0x0008L # Append new log entries 
#                                                        the end of the existing
#                                                        file */
ET_CMDLOG_NOREAD = 0x0010L # Exclude entries for rea
#                                                        from the chassis */
ET_CMDLOG_NOWRITE = 0x0020L # Exclude entries to write to the chassis */
ET_CMDLOG_NOCOMMENT = 0x0040L # Exclude information comments */
ET_CMDLOG_NOVERSION = 0x0080L # Exclude library version information at link and unlink 
ET_CMDLOG_NOLINKINFO = 0x0100L # Exclude link info for multi-link situations */
ET_CMDLOG_ALWAYSLINKINFO = 0x0200L # Include link info even for single links (overrides NOLINKINFO) */


# --- Scales used for InterPacketGap (IPG) and InterBurstGap (IBG) --- 
NANO_SCALE = 1
MICRO_SCALE = 2
MILLI_SCALE = 3


#   Supported speeds of different SmartCards.
#   Not all cards support all speeds.
#   See the SmartCard reference for supported speeds.

SPEED_4MHZ = 0x0001
SPEED_10MHZ = 0x0002
SPEED_16MHZ = 0x0004
SPEED_100MHZ = 0x0008
SPEED_155MHZ = 0x0010
SPEED_25MHZ = 0x0020
SPEED_1GHZ = 0x0040
SPEED_DUPLEX_UNTOUCHED = 0x00ff

# ------------------ MFType Definitions ------------------- 
MFTYPEEVENT = 0
MFTYPERATE = 1

# ---------- HTSeparateHubCommands parameters ------------- 
HUB_GROUP_DEFAULT_ACTION = 0
HUB_GROUP_INDEPENDENT_ACTION = 1
HUB_GROUP_UNIT_ACTION = 2 # redundant -- effectively equivalent to HUB_GROUP_DEFAULT_ACTION; left in for legacy purposes
HUB_GROUP_SYNC_ACTION = 3


# ----------- Firmware Release Type ----------------------- 
PRODUCTION_RELEASE = 0
PATCH_RELEASE = 1
ENGINEERING_QA_RELEASE = 2
ENGINEERING_TEST_RELEASE = 3


# ----- return values for NSGetMultiUserCapability ----- 
MULTI_USER_INCAPABLE = 0
MULTI_USER_CAPABLE = 1

# return values for NSGetSyncMode command 
SYNC_NONE = 0
SYNC_GPS_MASTER = 1
SYNC_GPS_MASTER_AND_INOUT_SLAVE = 2
SYNC_INOUT_MASTER = 3
SYNC_INOUT_SLAVE = 4

# return values for NSGetGPSStatus command 
GPS_STATUS_UNKNOWN = 0
GPS_STATUS_OK = 1
GPS_STATUS_NOT_READY = 2
GPS_STATUS_NOT_CONNECTED = 3

# Log Command 
COMMAND_MODE_LOG_AND_SEND = 0 # send to socket and write to log file
COMMAND_MODE_LOG_ONLY = 1 # only write to log file, don't send to socket
COMMAND_MODE_SEND_ONLY = 2 # only send to socket, don't  write to log file


# SmartbitsError exception map. Map failure codes to strings.

_EXCEPTION_HELP = {
UNSPECIFIED_ERROR:  """An error condition was encountered but could not be identified. This will occur if the system experienced an error that does not fit into any of the above categories.""",
PORT_NOT_LINKED: """An attempt to use a Programming Library function was made without an active link to the SmartBits.""",
UNLINK_FAILED: """An attempt to unlink the SmartBits from the serial port failed. This could occur if the SmartBits is already unlinked from the port before the ETUnLink command is called. """,
INCORRECT_MODE: """The attached SmartBits was put into a mode of operation where the attempted call to the library function was not applicable. For instance, you cannot access packet data unless the capture mode has been enabled. """,
PARAMETER_RANGE: """An incorrect or invalid range was specified for a library function parameter. This may include ranges within structures whose pointers are passed as a parameter to the function. """,
PACKET_NOT_AVAILABLE: """An attempt was made to access information from an indexed packet not currently in the capture buffer of the attached SmartBits. """,
SERIAL_PORT_DATA: """No errors were detected on the serial port, but the data returned from it doesn't appear to be correct. This indicates a serial port with interference. Try reducing the baud rate by modifying the ETSetBaud() parameter. """,
ET1000_OUT_OF_SYNC: """The attached SmartBits is operating in a mode different from what was expected. Perform an ETUnLink command followed by Link. """,
PACKET_NOT_FOUND: """An attempt was made to locate a packet within the SmartBits's capture buffer, but the packet contents could not be found and/or verified. """,
FUNCTION_ABORT: """The user aborted a function before it could run to completion. """,
ACTIVE_HUB_NOT_INITIALIZED: """An attempt to execute a command that requires a card was unsuccessful because the library failed to properly initialize the board. The library will always try to initialize the board if it hasn't been done so already, but for some reason, the initialization failed. This could indicate a failed card. """,
ACTIVE_HUB_NOT_PRESENT: """An attempt to execute a command that requires a card was unsuccessful because the addressed port had no board installed in it. """,
WRONG_HUB_CARD_TYPE: """An attempt to execute a command that requires a card was unsuccessful because the addressed port contained a Passive Hub board. """,
MEMORY_ALLOCATION_ERROR: """An attempt to execute a command that requires a card was unsuccessful because the addressed port contained a Passive Hub board. """,
UNSUPPORTED_INTERLEAVE: """Not currently implemented. """,
PORT_ALREADY_LINKED: """The Programming Library supports one connection at a time to an SmartBits. An ETLink command was issued when an active link already exists. """,
HUB_SLOT_PORT_UNAVAILABLE: """A request was made to perform an operation on a Hub/Slot/Port that does notexist in the current configuration. """,
GROUP_HUB_SLOT_PORT_ERROR: """A request was made to create or perform an operation on a group with a Hub/Slot/Port that does not exist in the current configuration. """,
REENTRANT_ERROR: """An attempt was made to call a Programming Library function while BackgroundProcessing was enabled, and the Programming Library was already performing a function. """,
DEVICE_NOT_FOUND_ERROR: """An attempt was made to address an attached device that could not be found [e.g. an MII transceiver]. """,
PORT_RELINK_REQUIRED: """The connection is down, but no disconnect action was taken by either side. """,
DEVICE_NOT_READY: """Current use: Token Ring is down. """,
GROUP_NOT_HOMOGENEOUS: """Not currently implemented. (Used only by undocumented commands). """,
INVALID_GROUP_COMMAND: """Not currently implemented. (Used only by undocumented commands). """,
ERROR_SMARTCARD_INIT_FAILED: """Unable to initialize card. """,
SOCKET_FAILED: """Error in the socket connection for an Ethernet Link (PC to SMB). """,
SOCKET_TIMEOUT: """Timeout on the socket connection for an Ethernet Link (PC to SMB). """,
COMMAND_RESPONSE_ERROR: """Invalid command response received from SmartBits. """,
CRC_ERROR: """CRC error in the data transfer. """,
INVALID_LINK_PORT_TYPE: """An attempt was made to link a PC to a SmartBits chassis over a connection that is recognized as neither a normal Serial CommPort nora properTCP/IP Socket Link. (This error message should not occur.) """,
INVALID_SYNC_CONFIGURATION: """User attempted to perform a GPS sync action when the SmartBits is not set for GPS. (Could indicate that GPS is not ready.) """,
HIGH_DENSITY_CONTROLLER_ERROR: """The SmartBits chassis is reporting ar error. It has rejected the command. """,
HIGH_DENSITY_CARD_ERROR: """A SmartModule is reporting an error and has rejected the command. Possible causes include: Invalid parameter values or a command that is not appropriate for the card s current state. """,
DATA_NOT_AVAILABLE: """An attempt was made to retrieve data from a card when no data of the intended type was available. An example would be when you attempt to retrieve histogram results from a Layer3 card when no histogram information has been accumulated yet. """,
UNSUPPORTED_PLATFORM: """The function is not available on the current platform. Currently this is used for HTDefaultStructure and related functions that are not available on 16-bit Windows platforms. """,
FILE_IO_ERROR: """An error occurred in accessing a file. Currently this will occur when HTDefaultStructure or a related function is called and the defaults file is not found. """,
MULTI_USER_CONFLICT: """The attempted action conflicted with another user of the same SmartBits. This will occur when a GPS sync start or stop is attempted shortly after another user also attempts a GPS sync action. """,
SERIAL_PORT_TIMEOUT: """The serial port timed out while waiting for a response from the SmartBits. This usually indicates a problem with the physical serial link. """,

# Errors occurring in the Tcl interface [will the python module ever see
# these?]
NSTCL_PARAMETER_TYPE: """This error will occur when a given parameter is not of the expected type, for example if a non-numeric argument is given when an integer is expected. This error often occurs when a "$" is missing in front of a variable name. """,
NSTCL_INVALID_MSG_FUNC: """An attempt to unlink the SmartBits from the serial port failed. The Tcl interface is unable to process a message function because it doesn t recognize the given iType parameters as matching the accompanying data structure for the card at the specified location. """,
NSTCL_PARAMETER_RANGE: """An invalid parameter was given, especially regarding the Tcl interface. """,
NSTCL_STRUCT_NOT_DEFINED: """An improper structure type was used with a message function in the Tcl interface. """,

# Non-fatal errors 
UNSUPPORTED_COMMAND: """The command is not supported by the card. """,
UPDATED_FIRMWARE_NEEDED: """The command requires a newer version of firmware than is currently installed in the card. """,

# Non-fatal errors specific to autonegotiation 
AN_LINK_NOT_NEGOTIATED: """The card has not negotiated a link with its link partner. """,
AN_NO_EXTENDED_CAPABILITY: """<no text> """,
AN_LINK_PARTNER_INCAPABLE: """<no text> """,
AN_INVALID_MII_ADDRESS: """<no text> """,
AN_SETTINGS_NOT_VERIFIED: """<no text> """,
}

def get_error_text(errno):
    return _EXCEPTION_HELP.get(errno, "No description available.") 

def print_error_desc(exc):
    errno = exc[0]
    print "Smartlib error:", errno
    print get_error_text(errno)

