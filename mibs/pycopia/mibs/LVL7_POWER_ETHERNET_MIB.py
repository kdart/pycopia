# python
# This file is generated by a program (mib2py). Any edits will be lost.

from pycopia.aid import Enum
import pycopia.SMI.Basetypes
Range = pycopia.SMI.Basetypes.Range
Ranges = pycopia.SMI.Basetypes.Ranges

from pycopia.SMI.Objects import ColumnObject, MacroObject, NotificationObject, RowObject, ScalarObject, NodeObject, ModuleObject, GroupObject

# imports 
from SNMPv2_SMI import MODULE_IDENTITY, OBJECT_TYPE, Gauge32
from POWER_ETHERNET_MIB import pethPsePortEntry, pethMainPseEntry
from LVL7_REF_MIB import fastPath
from SNMPv2_TC import TruthValue

class LVL7_POWER_ETHERNET_MIB(ModuleObject):
	path = '/usr/share/mibs/site/LVL7-POWER-ETHERNET-MIB'
	conformance = 4
	name = 'LVL7-POWER-ETHERNET-MIB'
	language = 2
	description = 'This MIB Augments the POWER-ETHERNET-MIB created by the IETF Ethernet \nInterfaces and Hub MIB Working Group for managing Power Source \nEquipment (PSE).  The objects in this MIB are intended to provide \nadditional objects for reporting information available to the hardware \non this platform which are not represented in the draft MIB.'

# nodes
class fastPathpowerEthernetMIB(NodeObject):
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15])
	name = 'fastPathpowerEthernetMIB'

class agentPethObjects(NodeObject):
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1])
	name = 'agentPethObjects'

class agentPethMainPseObjects(NodeObject):
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 2])
	name = 'agentPethMainPseObjects'


# macros
# types 
# scalars 
# columns
class agentPethPowerLimit(ColumnObject):
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 1, 1, 1])
	syntaxobject = pycopia.SMI.Basetypes.Gauge32
	access = 5
	units = 'Watts'


class agentPethOutputPower(ColumnObject):
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 1, 1, 2])
	syntaxobject = pycopia.SMI.Basetypes.Gauge32
	access = 4
	units = 'Milliwatts'


class agentPethOutputCurrent(ColumnObject):
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 1, 1, 3])
	syntaxobject = pycopia.SMI.Basetypes.Gauge32
	access = 4
	units = 'Milliamps'


class agentPethOutputVolts(ColumnObject):
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 1, 1, 4])
	syntaxobject = pycopia.SMI.Basetypes.Gauge32
	access = 4
	units = 'Volts'


class agentPethMainPseLegacy(ColumnObject):
	access = 5
	status = 1
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 2, 1, 1, 1])
	syntaxobject = pycopia.SMI.Basetypes.TruthValue


# rows 
from POWER_ETHERNET_MIB import pethPsePortGroupIndex
from POWER_ETHERNET_MIB import pethPsePortIndex
class agentPethPsePortEntry(RowObject):
	status = 1
	index = pycopia.SMI.Objects.IndexObjects([pethPsePortGroupIndex, pethPsePortIndex], False)
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 1, 1])
	access = 2
	columns = {'agentPethPowerLimit': agentPethPowerLimit, 'agentPethOutputPower': agentPethOutputPower, 'agentPethOutputCurrent': agentPethOutputCurrent, 'agentPethOutputVolts': agentPethOutputVolts}


from POWER_ETHERNET_MIB import pethMainPseGroupIndex
class agentPethMainPseEntry(RowObject):
	status = 1
	index = pycopia.SMI.Objects.IndexObjects([pethMainPseGroupIndex], False)
	OID = pycopia.SMI.Basetypes.ObjectIdentifier([1, 3, 6, 1, 4, 1, 674, 10895, 5000, 2, 6132, 1, 1, 15, 1, 2, 1, 1])
	access = 2
	columns = {'agentPethMainPseLegacy': agentPethMainPseLegacy}


# notifications (traps) 
# groups 
# capabilities 

# special additions

# Add to master OIDMAP.
from pycopia import SMI
SMI.update_oidmap(__name__)