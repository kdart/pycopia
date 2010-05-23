# python2.6
# -*- coding: utf-8 -*-
# RFC 3720 (iSCSI) protocol implementation for conformance testing.

"""
iSCSI header definitions and constructor interfaces.

"""

from struct import Struct
from collections import namedtuple

from pycopia.iscsi.constants import *


## Field objects ##

class FieldBase(object):
    """Base for field packers/unpackers.
    """
    __slots__ = ("_offset",)
    _packer = None
    size = None

    def __init__(self, offset):
        self._offset = offset

    def pack_into(self, buf, value):
        packer = self.__class__._packer
        packer.pack_into(buf, self._offset, value)

    def unpack_from(self, buf):
        packer = self.__class__._packer
        return packer.unpack_from(buf, self._offset)[0]


class ByteField(FieldBase):
    _packer = Struct("!B")
    size = _packer.size


class HalfField(FieldBase):
    _packer = Struct("!H")
    size = _packer.size


class IntField(FieldBase):
    _packer = Struct("!I")
    size = _packer.size


class ISIDField(FieldBase):
    _packer = Struct("!BHBH")
    size = _packer.size

    def pack_into(self, buf, value):
        offset = self._offset
        raw = ISIDField._packer.pack(*value)
        buf[offset:offset+ISIDField.size] = raw

    def unpack_from(self, buf):
        pass # XXX

class DataSegmentLength(FieldBase):
    """Special handler for DataSegmentLength, a 24 bit packed field."""
    _packer = Struct("!I")
    size = 3

    def pack_into(self, buf, value):
        offset = self._offset
        raw = DataSegmentLength._packer.pack(value)
        buf[offset:offset+3] = raw[1:]

    def unpack_from(self, buf):
        pass # XXX


# Some specialized field value types

class ISID(namedtuple('ISIDBase', "a, b, c, d")):
    """Value part of an ISID header field"""
    # TODO: type and bit field access


class SSID(namedtuple('SSIDBase', "isid, tgpt")):
    pass


# generates field instances with buffer offsets
def _field_generator(specs):
    offset = 0
    d = {}
    for name, cls in specs:
        d[name] = cls(offset)
        offset += cls.size
    return d


### Header objects ###

class ISCSIHeader(object):
    _FIELDS = None # dict mapping field name to tuple of pack format and offset in buffer.
    OP = None       # PDU header base opcode

    def __init__(self, **kwargs):
        self._field_values = {"opcode": self.__class__.OP}
        fields = self.__class__._FIELDS
        for kwname, kwvalue in kwargs.items():
            if kwname in fields:
                object.__setitem__(self, kwname, kwvalue)
            else:
                raise TypeError("Invalid field name: %r" % (kwname,))
        self.initialize()

    def initialize(self):
        """Override in subclasses for additional initialization."""
        pass

    def __getitem__(self, name):
        if name in self.__class__._FIELDS:
            return self._field_values.get(name, 0)
        else:
            raise KeyError("Invalid field name: %r" % (name,))

    def __setitem__(self, name, value):
        if name in self.__class__._FIELDS:
            self._field_values[name] = value
        else:
            raise KeyError("Invalid field name: %r" % (name,))

    def pack_into(self, buf):
        for name, value in self._field_values.items():
            field = self.__class__._FIELDS[name]
            field.pack_into(buf, value)


class AdditionalHeader(ISCSIHeader):
    pass # TODO


class RequestHeader(ISCSIHeader):
    """Base class for initiator PDUs.

    Provides functionality common to all request PDU headers.
    """

    def _get_immediate(self):
        return self._field_values["opcode"] & OP_IMMEDIATE

    def _set_immediate(self, flag):
        opcode = self._field_values["opcode"]
        if flag:
            opcode = opcode | OP_IMMEDIATE
        else:
            opcode = opcode & ~OP_IMMEDIATE
        self._field_values["opcode"] = opcode

    def _clear_immediate(self):
        self._field_values["opcode"] = self._field_values["opcode"] & ~OP_IMMEDIATE

    immediate = property(_get_immediate, _set_immediate, _clear_immediate)



class ResponseHeader(ISCSIHeader):
    """Base class for target PDUs.

    Provides functionality common to all response PDU headers.
    """

    def decode(self, buf):
        pass


#### concrete PDU headers. ####

class LoginHeader(RequestHeader):
    """Login Header """
    OP = OP_LOGIN 
    _FIELDS = _field_generator([
        ('opcode', ByteField),
        ('flags', ByteField),
        ('VersionMax', ByteField),
        ('VersionMin', ByteField),
        ('totalAHSLength', ByteField),
        ('dataSegmentLength', DataSegmentLength),
        ('ISID', ISIDField),
        ('TSIH', HalfField),
        ('ITT', IntField),
        ('CID', HalfField),
        ('_rsvd', HalfField),
        ('CmdSN', IntField),
        ('ExpStatSN', IntField),
    ])

    def initialize(self):
        self.__setitem__("VersionMax", DRAFT20_VERSION)
        self.__setitem__("VersionMin", DRAFT20_VERSION)
        self.__setitem__("ITT", 0)
        self.immediate = True # login requests are always immediate


class LoginResponseHeader(ResponseHeader):
    """Login Response Header """
    OP = OP_LOGIN_RSP
    _FIELDS = _field_generator([
        ('opcode', ByteField),
    ])


class LogoutHeader(RequestHeader):
    """Logout Header """
    OP = OP_LOGOUT 

class LogoutResponseHeader(ResponseHeader):
    """Logout Response Header """
    OP = OP_LOGOUT_RSP


class SCSICommandHeader(RequestHeader):
    "iSCSI PDU Header """
    OP = OP_SCSI_CMD


class SCSICommandResponseHeader(ResponseHeader):
    """SCSI command response"""
    OP = OP_SCSI_CMD_RSP


class AsynchronousEventHeader(ResponseHeader):
    """Asynchronous Event Header """
    OP = OP_ASYNC_EVENT


class NOPOutHeader(ResponseHeader):
    """NOP-Out Message """
    OP = OP_NOOP_IN


class NOPInHeader(RequestHeader):
    """NOP-In Message """
    OP = OP_NOOP_OUT


class TaskManagementMessageHeader(RequestHeader):
    """SCSI Task Management Message Header """
    OP = OP_SCSI_TMFUNC


class TaskManagementResponseHeader(ResponseHeader):
    """SCSI Task Management Response Header """
    OP = OP_SCSI_TMFUNC_RSP


class R2THeader(ResponseHeader):
    """Ready To Transfer Header """
    OP = OP_R2T


class SCSIDataHeader(RequestHeader):
    """SCSI Data Hdr """
    OP = OP_SCSI_DATA_OUT


class SCSIDataResponseHeader(ResponseHeader):
    """SCSI Data Response Hdr """
    OP = OP_SCSI_DATA_IN


class TextHeader(RequestHeader):
    """Text Header """
    OP = OP_TEXT

class TextResponseHeader(ResponseHeader):
    """Text Response Header """
    OP = OP_TEXT_RSP


class SNACKHeader(RequestHeader):
    """SNACK Header """
    OP = OP_SNACK


class RejectMessageHeader(ResponseHeader):
    """Reject Message Header """
    OP = OP_REJECT


class RlengthHeader(AdditionalHeader):
    pass


class ExtendedCDBHeader(AdditionalHeader):
    """Extended CDB AHS """


#### Data segments ####

class KeyValueData(dict):

    def encode(self):
        s = []
        for key, value in self.items():
            s.append("%s=%s" % (key, value))
        return "\0".join(s) + "\0"


##### PDUs (whole messages) #####

class ISCSIPDU(object):
    def __init__(self):
        self._header = None
        self._additional_headers = []
        self._use_header_digest = False
        self._data = None
        self._use_data_digest = False

    def encode(self):
        # encode in reverse PDU order so lengths can be computed and
        # placed in header.
        pdulist = []
        ahslength = 0
        dlength = 0
        # add data, if present
        if self._data is not None:
            dbuf = self._data.encode()
            dlength = len(dbuf) # data length does not include padding
            r = dlength % PAD_LEN
            if r:
                dbuf += "\0" * (PAD_LEN - r)
            pdulist.append(dbuf)
            # add data digest if required, digest includes padding
            if self._use_data_digest:
                pdulist.insert(0, _data_digest(dbuf))

        self._header["dataSegmentLength"] = dlength

        # add header digest if required
        if self._use_header_digest:
            pdulist.append(None) # TODO: fix this ugly hack. None is replaced by CRC value later

        # do additional header segments first, so length can be computed
        for h in self._additional_headers:
            buf = h.encode()
            pdulist.append(buf)
            ahslength += len(buf)
        self._header["totalAHSLength"] = ahslength / 4

        # encode basic header
        hbuf = bytearray(48)
        self._header.pack_into(hbuf)
        pdulist.append(str(hbuf))

        # TODO: fix this ugly hack
        if self._use_header_digest:
            _header_digest(pdulist)

        pdulist.reverse()
        return "".join(pdulist)

    def _set_data(self, data):
        self._data = data

    def _del_data(self):
        self._data = None

    data = property(lambda s: s._data, _set_data, _del_data)

    def add_additional_header(self, hdr):
        pass # TODO


def _header_digest(pdulist):
    return pdulist # TODO

def _data_digest(buf):
    return "" # TODO


class LoginPDU(ISCSIPDU):
    def __init__(self):
        super(LoginPDU, self).__init__()
        self._header = LoginHeader()
        self._data = KeyValueData()

    def _set_transit(self, flag):
        if flag:
            self._header["flags"] |= FLAG_LOGIN_TRANSIT
        else:
            self._header["flags"] &= ~FLAG_LOGIN_TRANSIT

    def _get_transit(self):
        return self._header["flags"] & FLAG_LOGIN_TRANSIT

    transit = property(_get_transit, _set_transit)

    def _set_continue(self, flag):
        if flag:
            self._header["flags"] |= FLAG_LOGIN_CONTINUE
        else:
            self._header["flags"] &= ~FLAG_LOGIN_CONTINUE

    def _get_continue(self):
        return self._header["flags"] & FLAG_LOGIN_CONTINUE

    continue_ = property(_get_continue, _set_continue) # "continue" is a keyword

    def _get_isid(self):
        return self._header["ISID"]

    def _set_isid(self, value):
        assert isinstance(value, ISID)
        self._header["ISID"] = value

    ISID = property(_get_isid, _set_isid)

    def _get_current_stage(self):
        return (self._header["flags"] & FLAG_LOGIN_CURRENT_STAGE_MASK) >> 2

    def _set_current_stage(self, value):
        value = (value << 2) & FLAG_LOGIN_CURRENT_STAGE_MASK
        self._header["flags"] &= ~FLAG_LOGIN_CURRENT_STAGE_MASK 
        self._header["flags"] |= value

    current_stage = property(_get_current_stage, _set_current_stage)

    def _get_next_stage(self):
        return self._header["flags"] & FLAG_LOGIN_NEXT_STAGE_MASK

    def _set_next_stage(self, value):
        self._header["flags"] &= ~FLAG_LOGIN_NEXT_STAGE_MASK
        self._header["flags"] |= (value & FLAG_LOGIN_NEXT_STAGE_MASK)

    next_stage = property(_get_next_stage, _set_next_stage)

    # PDUs with key-value data use mapping interface
    def __setitem__(self, name, value):
        self._data[name] = value

    def __getitem__(self, name):
        return self._data[name]

    def __delitem__(self, name):
        del self._data[name]



if __name__ == "__main__":

    from pycopia import aid
    from pycopia import autodebug

    pdu = LoginPDU()
    pdu.ISID = ISID(0, 0x023d, 3, 0)
    buf = pdu.encode()
    print aid.str2hex(buf)
    pdu.transit = True
    pdu.next_stage = FULL_FEATURE_PHASE
    pdu.next_stage = OP_PARMS_NEGOTIATION_STAGE
    pdu["SessionType"] = "Normal"
    pdu["AuthMethod"] = "Chap,None"
    buf = pdu.encode()
    print aid.str2hex(buf)
    assert buf[0] == chr(0x03 + 0x40)
    assert buf[1] == chr(0x81)
    assert len(buf) % 4 == 0


