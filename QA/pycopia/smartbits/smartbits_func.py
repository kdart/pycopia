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

import smartbits_funcc
import new


#-------------- FUNCTION WRAPPERS ------------------

ptrvalue = smartbits_funcc.ptrvalue

ptrset = smartbits_funcc.ptrset

ptrcreate = smartbits_funcc.ptrcreate

ptrfree = smartbits_funcc.ptrfree

ptradd = smartbits_funcc.ptradd

HTGetStructureSize = smartbits_funcc.HTGetStructureSize

HTGetStructSize = smartbits_funcc.HTGetStructSize

ETAlignCount = smartbits_funcc.ETAlignCount

ETBNC = smartbits_funcc.ETBNC

ETBurst = smartbits_funcc.ETBurst

ETCaptureParams = smartbits_funcc.ETCaptureParams

ETCaptureRun = smartbits_funcc.ETCaptureRun

ETCollision = smartbits_funcc.ETCollision

ETDataLength = smartbits_funcc.ETDataLength

ETDataPattern = smartbits_funcc.ETDataPattern

ETDribbleCount = smartbits_funcc.ETDribbleCount

ETGap = smartbits_funcc.ETGap

ETGapScale = smartbits_funcc.ETGapScale

ETGetAlignCount = smartbits_funcc.ETGetAlignCount

ETGetBaud = smartbits_funcc.ETGetBaud

ETGetBNC = smartbits_funcc.ETGetBNC

ETGetBurstCount = smartbits_funcc.ETGetBurstCount

ETGetBurstMode = smartbits_funcc.ETGetBurstMode

ETGetCapturePacket = smartbits_funcc.ETGetCapturePacket

ETGetCapturePacketCount = smartbits_funcc.ETGetCapturePacketCount

ETGetCapturePacketInfo = smartbits_funcc.ETGetCapturePacketInfo

ETGetCaptureErrors = smartbits_funcc.ETGetCaptureErrors

ETGetCaptureParams = smartbits_funcc.ETGetCaptureParams

ETGetCaptureTime = smartbits_funcc.ETGetCaptureTime

ETGetCollision = smartbits_funcc.ETGetCollision

ETGetTotalLinks = smartbits_funcc.ETGetTotalLinks

ETGetLinkFromIndex = smartbits_funcc.ETGetLinkFromIndex

ETGetCurrentLink = smartbits_funcc.ETGetCurrentLink

ETSetLinksHubAccessMode = smartbits_funcc.ETSetLinksHubAccessMode

ETGetController = smartbits_funcc.ETGetController

ETGetProductFamily = smartbits_funcc.ETGetProductFamily

ETGetCounters = smartbits_funcc.ETGetCounters

ETGetCRCError = smartbits_funcc.ETGetCRCError

ETGetDataLength = smartbits_funcc.ETGetDataLength

ETGetDataPattern = smartbits_funcc.ETGetDataPattern

ETGetDribbleCount = smartbits_funcc.ETGetDribbleCount

ETGetErrorStatus = smartbits_funcc.ETGetErrorStatus

ETGetFirmwareVersion = smartbits_funcc.ETGetFirmwareVersion

ETGetFlashVersion = smartbits_funcc.ETGetFlashVersion

ETGetGap = smartbits_funcc.ETGetGap

ETGetGapScale = smartbits_funcc.ETGetGapScale

ETGetHardwareVersion = smartbits_funcc.ETGetHardwareVersion

ETGetJET210Mode = smartbits_funcc.ETGetJET210Mode

ETGetLibVersion = smartbits_funcc.ETGetLibVersion

ETGetLinkStatus = smartbits_funcc.ETGetLinkStatus

ETGetPreamble = smartbits_funcc.ETGetPreamble

ETGetReceiveTrigger = smartbits_funcc.ETGetReceiveTrigger

ETGetRun = smartbits_funcc.ETGetRun

ETGetSel = smartbits_funcc.ETGetSel

ETGetSerialNumber = smartbits_funcc.ETGetSerialNumber

ETGetSwitch = smartbits_funcc.ETGetSwitch

ETGetTransmitTrigger = smartbits_funcc.ETGetTransmitTrigger

ETGetVFDRun = smartbits_funcc.ETGetVFDRun

ETLink = smartbits_funcc.ETLink

ETSocketLink = smartbits_funcc.ETSocketLink

ETSocketLinkRsvNone = smartbits_funcc.ETSocketLinkRsvNone

ETDebugLink = smartbits_funcc.ETDebugLink

ETLoopback = smartbits_funcc.ETLoopback

ETLNM = smartbits_funcc.ETLNM

ETGetLNM = smartbits_funcc.ETGetLNM

ETMFCounter = smartbits_funcc.ETMFCounter

ETPreamble = smartbits_funcc.ETPreamble

ETReceiveTrigger = smartbits_funcc.ETReceiveTrigger

ETRemote = smartbits_funcc.ETRemote

ETReset = smartbits_funcc.ETReset

ETResume = smartbits_funcc.ETResume

ETRun = smartbits_funcc.ETRun

ETSetBaud = smartbits_funcc.ETSetBaud

ETSetCurrentLink = smartbits_funcc.ETSetCurrentLink

ETSetCurrentSockLink = smartbits_funcc.ETSetCurrentSockLink

ETSetCurrentLinkByIndex = smartbits_funcc.ETSetCurrentLinkByIndex

ETSetJET210Mode = smartbits_funcc.ETSetJET210Mode

ETSetSel = smartbits_funcc.ETSetSel

ETSetTimeout = smartbits_funcc.ETSetTimeout

NSSetIdleMax = smartbits_funcc.NSSetIdleMax

ETSetup = smartbits_funcc.ETSetup

ETTransmitCRC = smartbits_funcc.ETTransmitCRC

ETTransmitTrigger = smartbits_funcc.ETTransmitTrigger

ETUnLink = smartbits_funcc.ETUnLink

ETUnLinkAll = smartbits_funcc.ETUnLinkAll

ETVFDParams = smartbits_funcc.ETVFDParams

ETVFDRun = smartbits_funcc.ETVFDRun

NSSetControllerID = smartbits_funcc.NSSetControllerID

NSClearURLTable = smartbits_funcc.NSClearURLTable

HTAlign = smartbits_funcc.HTAlign

HTBurstCount = smartbits_funcc.HTBurstCount

HTBurstGap = smartbits_funcc.HTBurstGap

HTBurstGapAndScale = smartbits_funcc.HTBurstGapAndScale

HTCardModels = smartbits_funcc.HTCardModels

HTGetCardModel = smartbits_funcc.HTGetCardModel

HTClear = smartbits_funcc.HTClear

HTClearPort = smartbits_funcc.HTClearPort

HTCollision = smartbits_funcc.HTCollision

HTCollisionBackoffAggressiveness = smartbits_funcc.HTCollisionBackoffAggressiveness

HTCRC = smartbits_funcc.HTCRC

HTDataLength = smartbits_funcc.HTDataLength

HTDribble = smartbits_funcc.HTDribble

HTDuplexMode = smartbits_funcc.HTDuplexMode

HTSetSpeed = smartbits_funcc.HTSetSpeed

HTFillPattern = smartbits_funcc.HTFillPattern

HTModifyFillPattern = smartbits_funcc.HTModifyFillPattern

HTFindMIIAddress = smartbits_funcc.HTFindMIIAddress

HTGap = smartbits_funcc.HTGap

HTGapAndScale = smartbits_funcc.HTGapAndScale

HTGapScaleAndMode = smartbits_funcc.HTGapScaleAndMode

HTGetBuiltInAddress = smartbits_funcc.HTGetBuiltInAddress

HTGetCounters = smartbits_funcc.HTGetCounters

HTGetEnhancedCounters = smartbits_funcc.HTGetEnhancedCounters

HTGetEnhancedStatus = smartbits_funcc.HTGetEnhancedStatus

HTGetHWVersion = smartbits_funcc.HTGetHWVersion

HTGetHubLEDs = smartbits_funcc.HTGetHubLEDs

HTGetLEDs = smartbits_funcc.HTGetLEDs

HTGroupStart = smartbits_funcc.HTGroupStart

HTGroupStep = smartbits_funcc.HTGroupStep

HTGroupStop = smartbits_funcc.HTGroupStop

HTHubId = smartbits_funcc.HTHubId

HTHubSlotPorts = smartbits_funcc.HTHubSlotPorts

HTLatency = smartbits_funcc.HTLatency

HTMultiBurstCount = smartbits_funcc.HTMultiBurstCount

HTPortType = smartbits_funcc.HTPortType

HTPortTypeChar = smartbits_funcc.HTPortTypeChar

HTPortProperty = smartbits_funcc.HTPortProperty

HTMinAcceptableLength = smartbits_funcc.HTMinAcceptableLength

HTMaxAcceptableLength = smartbits_funcc.HTMaxAcceptableLength

HTMinAllowableLength = smartbits_funcc.HTMinAllowableLength

HTMaxAllowableLength = smartbits_funcc.HTMaxAllowableLength

HTMinAcceptableGap = smartbits_funcc.HTMinAcceptableGap

HTMaxAcceptableGap = smartbits_funcc.HTMaxAcceptableGap

HTMinAllowableGap = smartbits_funcc.HTMinAllowableGap

HTMaxAllowableGap = smartbits_funcc.HTMaxAllowableGap

HTMinGapIncrement = smartbits_funcc.HTMinGapIncrement

HTReadMII = smartbits_funcc.HTReadMII

HTResetPort = smartbits_funcc.HTResetPort

HTRun = smartbits_funcc.HTRun

HTSelectReceive = smartbits_funcc.HTSelectReceive

HTSelectTransmit = smartbits_funcc.HTSelectTransmit

HTSendCommand = smartbits_funcc.HTSendCommand

HTSeparateHubCommands = smartbits_funcc.HTSeparateHubCommands

HTSetStructure = smartbits_funcc.HTSetStructure

HTGetStructure = smartbits_funcc.HTGetStructure

HTSetCommand = smartbits_funcc.HTSetCommand

HGSetStructure = smartbits_funcc.HGSetStructure

HGSetCommand = smartbits_funcc.HGSetCommand

HTDefaultStructure = smartbits_funcc.HTDefaultStructure

HTGetTypeStrings = smartbits_funcc.HTGetTypeStrings

ETIsSyncCapable = smartbits_funcc.ETIsSyncCapable

ETSetGPSActionTime = smartbits_funcc.ETSetGPSActionTime

ETSetGPSActionTimeWithDelay = smartbits_funcc.ETSetGPSActionTimeWithDelay

ETGetGPSTime = smartbits_funcc.ETGetGPSTime

HTGetStandardFWVersion = smartbits_funcc.HTGetStandardFWVersion

HTGetCardFWVersion = smartbits_funcc.HTGetCardFWVersion

HTSetTokenRingProperty = smartbits_funcc.HTSetTokenRingProperty

HTSetTokenRingErrors = smartbits_funcc.HTSetTokenRingErrors

HTSetTokenRingLLC = smartbits_funcc.HTSetTokenRingLLC

HTSetTokenRingMAC = smartbits_funcc.HTSetTokenRingMAC

HTSetTokenRingSrcRouteAddr = smartbits_funcc.HTSetTokenRingSrcRouteAddr

HTSetTokenRingAdvancedControl = smartbits_funcc.HTSetTokenRingAdvancedControl

HTSetVGProperty = smartbits_funcc.HTSetVGProperty

HTSymbol = smartbits_funcc.HTSymbol

HTTransmitMode = smartbits_funcc.HTTransmitMode

HTScheduleMode = smartbits_funcc.HTScheduleMode

HTTrigger = smartbits_funcc.HTTrigger

HTTriggerAndMask = smartbits_funcc.HTTriggerAndMask

HTVFD = smartbits_funcc.HTVFD

HTWriteMII = smartbits_funcc.HTWriteMII

HGStartSetGroup = smartbits_funcc.HGStartSetGroup

HGSetGroup = smartbits_funcc.HGSetGroup

HGClearGroup = smartbits_funcc.HGClearGroup

HGSetGroupType = smartbits_funcc.HGSetGroupType

HGAddtoGroup = smartbits_funcc.HGAddtoGroup

HGRemoveFromGroup = smartbits_funcc.HGRemoveFromGroup

HGRemovePortIdFromGroup = smartbits_funcc.HGRemovePortIdFromGroup

HGEndSetGroup = smartbits_funcc.HGEndSetGroup

HGIsPortInGroup = smartbits_funcc.HGIsPortInGroup

HGIsHubSlotPortInGroup = smartbits_funcc.HGIsHubSlotPortInGroup

HGGetGroupCount = smartbits_funcc.HGGetGroupCount

HGClear = smartbits_funcc.HGClear

HGGetLEDs = smartbits_funcc.HGGetLEDs

HGSelectTransmit = smartbits_funcc.HGSelectTransmit

HGClearPort = smartbits_funcc.HGClearPort

HGGetCounters = smartbits_funcc.HGGetCounters

HGGetEnhancedCounters = smartbits_funcc.HGGetEnhancedCounters

HGFillPattern = smartbits_funcc.HGFillPattern

HGModifyFillPattern = smartbits_funcc.HGModifyFillPattern

HGGap = smartbits_funcc.HGGap

HGGapAndScale = smartbits_funcc.HGGapAndScale

HGGapScaleAndMode = smartbits_funcc.HGGapScaleAndMode

HGTransmitMode = smartbits_funcc.HGTransmitMode

HGScheduleMode = smartbits_funcc.HGScheduleMode

HGBurstCount = smartbits_funcc.HGBurstCount

HGMultiBurstCount = smartbits_funcc.HGMultiBurstCount

HGBurstGap = smartbits_funcc.HGBurstGap

HGBurstGapAndScale = smartbits_funcc.HGBurstGapAndScale

HGDataLength = smartbits_funcc.HGDataLength

HGDuplexMode = smartbits_funcc.HGDuplexMode

HGResetPort = smartbits_funcc.HGResetPort

HGRun = smartbits_funcc.HGRun

HGStart = smartbits_funcc.HGStart

HGStep = smartbits_funcc.HGStep

HGStop = smartbits_funcc.HGStop

HGRunFixedTime = smartbits_funcc.HGRunFixedTime

HGRunGPSDelay = smartbits_funcc.HGRunGPSDelay

HGTrigger = smartbits_funcc.HGTrigger

HGTriggerAndMask = smartbits_funcc.HGTriggerAndMask

HGVFD = smartbits_funcc.HGVFD

HGCollisionBackoffAggressiveness = smartbits_funcc.HGCollisionBackoffAggressiveness

HGWriteMII = smartbits_funcc.HGWriteMII

HGSendCardData = smartbits_funcc.HGSendCardData

HGSetTokenRingProperty = smartbits_funcc.HGSetTokenRingProperty

HGSetTokenRingErrors = smartbits_funcc.HGSetTokenRingErrors

HGSetTokenRingLLC = smartbits_funcc.HGSetTokenRingLLC

HGSetTokenRingMAC = smartbits_funcc.HGSetTokenRingMAC

HGSetTokenRingSrcRouteAddr = smartbits_funcc.HGSetTokenRingSrcRouteAddr

HGSetTokenRingAdvancedControl = smartbits_funcc.HGSetTokenRingAdvancedControl

HGSetVGProperty = smartbits_funcc.HGSetVGProperty

HGAlign = smartbits_funcc.HGAlign

HGCRC = smartbits_funcc.HGCRC

HGDribble = smartbits_funcc.HGDribble

HGSymbol = smartbits_funcc.HGSymbol

HGCollision = smartbits_funcc.HGCollision

HTSlotReserve = smartbits_funcc.HTSlotReserve

HTSlotRelease = smartbits_funcc.HTSlotRelease

HTSlotOwnership = smartbits_funcc.HTSlotOwnership

NSGetMultiUserCapability = smartbits_funcc.NSGetMultiUserCapability

NSSetPortMappingMode = smartbits_funcc.NSSetPortMappingMode

NSGetMaxHubs = smartbits_funcc.NSGetMaxHubs

NSGetMaxSlots = smartbits_funcc.NSGetMaxSlots

NSGetMaxPorts = smartbits_funcc.NSGetMaxPorts

NSGetNumHubs = smartbits_funcc.NSGetNumHubs

NSGetNumSlots = smartbits_funcc.NSGetNumSlots

NSGetNumPorts = smartbits_funcc.NSGetNumPorts

NSGetChannelId = smartbits_funcc.NSGetChannelId

HTMapUserToNative = smartbits_funcc.HTMapUserToNative

HTMapNativeToUser = smartbits_funcc.HTMapNativeToUser

NSCreateFrame = smartbits_funcc.NSCreateFrame

NSSetPayload = smartbits_funcc.NSSetPayload

HTFrame = smartbits_funcc.HTFrame

NSDeleteFrame = smartbits_funcc.NSDeleteFrame

NSCreateFrameAndPayload = smartbits_funcc.NSCreateFrameAndPayload

NSModifyFrame = smartbits_funcc.NSModifyFrame

NSGetControllerFWVersion = smartbits_funcc.NSGetControllerFWVersion

ETSetGPSDelay = smartbits_funcc.ETSetGPSDelay

NSGetSyncMode = smartbits_funcc.NSGetSyncMode

NSGetGPSStatus = smartbits_funcc.NSGetGPSStatus

NSSocketLink = smartbits_funcc.NSSocketLink

NSUnLink = smartbits_funcc.NSUnLink

NSUnLinkAll = smartbits_funcc.NSUnLinkAll

NSSetDefaultsFile = smartbits_funcc.NSSetDefaultsFile

NSDelay = smartbits_funcc.NSDelay

NSGetDetailedLibVersion = smartbits_funcc.NSGetDetailedLibVersion

NSCommandMode = smartbits_funcc.NSCommandMode

NSSetErrorCallback = smartbits_funcc.NSSetErrorCallback

ETEraseFlash = smartbits_funcc.ETEraseFlash

ETLoadHex = smartbits_funcc.ETLoadHex

ETDiagReset = smartbits_funcc.ETDiagReset

ETSendString = smartbits_funcc.ETSendString

ETReadChar = smartbits_funcc.ETReadChar

ETSendRecv = smartbits_funcc.ETSendRecv

ETSetXonXoff = smartbits_funcc.ETSetXonXoff

ETGetXonXoff = smartbits_funcc.ETGetXonXoff

ETIsBackgroundProcessing = smartbits_funcc.ETIsBackgroundProcessing

ETEnableBackgroundProcessing = smartbits_funcc.ETEnableBackgroundProcessing

ETCommandLog = smartbits_funcc.ETCommandLog

ETCommandComment = smartbits_funcc.ETCommandComment

ETSetIdleMax = smartbits_funcc.ETSetIdleMax

HTBurst = smartbits_funcc.HTBurst

HTEcho = smartbits_funcc.HTEcho

HTSelectReceivePort = smartbits_funcc.HTSelectReceivePort

HTSelectTMTPort = smartbits_funcc.HTSelectTMTPort

HTSetLED = smartbits_funcc.HTSetLED

HTGroup = smartbits_funcc.HTGroup

HGBurst = smartbits_funcc.HGBurst

HGEcho = smartbits_funcc.HGEcho

HGSelectReceivePort = smartbits_funcc.HGSelectReceivePort

HGSelectTMTPort = smartbits_funcc.HGSelectTMTPort

HGSetLED = smartbits_funcc.HGSetLED

HGSetSpeed = smartbits_funcc.HGSetSpeed

HTLatencyTest = smartbits_funcc.HTLatencyTest

HTLayer3SetAddress = smartbits_funcc.HTLayer3SetAddress

HTLayer3GetAddress = smartbits_funcc.HTLayer3GetAddress

HTTcpRecordCount = smartbits_funcc.HTTcpRecordCount



#-------------- VARIABLE WRAPPERS ------------------

