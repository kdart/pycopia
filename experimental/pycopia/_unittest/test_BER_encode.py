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
Test BER encoding module in SNMP package.

"""

import qatest

# the module under test
# XXX change to SNMP when complete
import SNMP.Basetypes as Basetypes
import SNMP.BER_decode as decode

# these should be pre-compiled by the mib2py program.
import mibs.IP_MIB, mibs.SNMPv2_MIB

sysUpTime = mibs.SNMPv2_MIB.sysUpTime.OID
ipNetToMediaPhysAddress = mibs.IP_MIB.ipNetToMediaPhysAddress.OID
ipNetToMediaType = mibs.IP_MIB.ipNetToMediaType.OID


class BERencodeBaseTest(qatest.Test):
    pass


#   As an example of applying the Basic Encoding Rules, suppose one
#   wanted to encode an instance of the GetBulkRequest-PDU [RFC3416]:
#
#     [5] IMPLICIT SEQUENCE {
#             request-id      1414684022,
#             non-repeaters   1,
#             max-repetitions 2,
#             variable-bindings {
#                 { name sysUpTime,
#                   value { unSpecified NULL } },
#                 { name ipNetToMediaPhysAddress,
#                   value { unSpecified NULL } },
#                 { name ipNetToMediaType,
#                   value { unSpecified NULL } }
#             }
#         }
#
#   Applying the BER, this may be encoded (in hexadecimal) as:
#
#   [5] IMPLICIT SEQUENCE          a5 82 00 39
#       INTEGER                    02 04 54 52 5d 76
#       INTEGER                    02 01 01
#       INTEGER                    02 01 02
#       SEQUENCE (OF)              30 2b
#           SEQUENCE               30 0b
#               OBJECT IDENTIFIER  06 07 2b 06 01 02 01 01 03
#               NULL               05 00
#           SEQUENCE               30 0d
#               OBJECT IDENTIFIER  06 09 2b 06 01 02 01 04 16 01 02
#               NULL               05 00
#           SEQUENCE               30 0d
#               OBJECT IDENTIFIER  06 09 2b 06 01 02 01 04 16 01 04
#               NULL               05 00
#
#   Note that the initial SEQUENCE in this example was not encoded using
#   the minimum number of length octets.  (The first octet of the length,
#   82, indicates that the length of the content is encoded in the next
#   two octets.)



EXPECTED = [
    ("[5]IMPLICIT SEQUENCE",       "\xa5\x82\x00\x39"),
    ("INTEGER",                    "\x02\x04\x54\x52\x5d\x76"), # 1414684022
    ("INTEGER",                    "\x02\x01\x01"),
    ("INTEGER",                    "\x02\x01\x02"),
    ("SEQUENCE",                   "\x30\x2b"),
        ("SEQUENCE",               "\x30\x0b"),
            ("OBJECT IDENTIFIER",  "\x06\x07\x2b\x06\x01\x02\x01\x01\x03"),
            ("NULL",               "\x05\x00"),
        ("SEQUENCE",               "\x30\x0d"),
            ("OBJECT IDENTIFIER",  "\x06\x09\x2b\x06\x01\x02\x01\x04\x16\x01\x02"),
            ("NULL",               "\x05\x00"),
        ("SEQUENCE",               "\x30\x0d"),
            ("OBJECT IDENTIFIER",  "\x06\x09\x2b\x06\x01\x02\x01\x04\x16\x01\x04"),
            ("NULL",               "\x05\x00"),
]


# puts together the above example into a complete BER encoded stream.
def _get_expected_encoding():
    ber = []
    for bertype, encoding in EXPECTED:
        ber.append(encoding)
    return "".join(ber)


class BERencodeIntegerTest(BERencodeBaseTest):
    """Verify the BER encoding of the interger types."""
    def test_method(self):
        TESTS = [
            (ber(Basetypes.INTEGER(0)), "\x02\x01\x00"),
            (ber(Basetypes.INTEGER(1)), "\x02\x01\x01"),
            (ber(Basetypes.INTEGER(255)), "\x02\x02\x00\xff"),
            (ber(Basetypes.INTEGER(1414684022)), "\x02\x04\x54\x52\x5d\x76"),
        ]
        for myenc, std in TESTS:
            self.assert_equal(myenc, std, "bad integer encoding: %s != %s" % (str2hex(myenc), str2hex(std),))
        return self.passed("INTEGERs encoded properly.")


class BERencodeGetBulkRequestPDU(BERencodeBaseTest):
    """Verify the BER encoding of a whole GetBulkRequest-PDU as given in the example."""

    def test_method(self):
        vblist = Basetypes.VarBindList()
        vblist.append(Basetypes.VarBind( sysUpTime ))
        vblist.append(Basetypes.VarBind( ipNetToMediaPhysAddress ))
        vblist.append(Basetypes.VarBind( ipNetToMediaType ))
        pdu = Basetypes.GetBulkRequestPDU \
            (request_id=Basetypes.INTEGER(1414684022), non_repeaters=Basetypes.INTEGER(1), max_repetitions=Basetypes.INTEGER(2), varbinds=vblist)

        pdu_ber = ber(pdu)
        expected = _get_expected_encoding()

        self.assert_equal(pdu_ber, expected, "bad BER encoding for GetBulkRequest-PDU\n%s\n != \n%s" % (str2hex(pdu_ber), str2hex(expected)))

        return self.passed("asserted our GetBulkRequestPDU matches example.")

class DecodeExample(BERencodeBaseTest):
    def test_method(self):
        std = _get_expected_encoding()
        tlv = decode.get_tlv(std)
        obj = tlv.decode()
        self.info(str(obj))
        assert obj.request_id == 1414684022, "request-id %s != %s" % (1414684022, obj.request_id)
        assert obj.non_repeaters == 1, "non-repeaters %s != %s" % (1, obj.non_repeaters)
        assert obj.max_repetitions == 2, "max-repetitions %s != %s" % (2, obj.max_repetitions)
        assert sysUpTime == obj.varbinds[0].name, "%s != %s" % (sysUpTime , obj.varbinds[0].name)
        assert ipNetToMediaPhysAddress == obj.varbinds[1].name, "%s != %s" % (ipNetToMediaPhysAddress , obj.varbinds[1].name)
        assert ipNetToMediaType ==obj.varbinds[2].name, "%s != %s" % (ipNetToMediaType , obj.varbinds[2].name)
        return self.passed("sample PDU properly decoded.")


########## suite ##########
class BERencodeSuite(qatest.TestSuite):
    pass

def get_suite(conf):
    suite = BERencodeSuite(conf)
    suite.add_test(BERencodeIntegerTest)
    suite.add_test(BERencodeGetBulkRequestPDU)
    suite.add_test(DecodeExample)
    return suite

def run(conf):
    suite = get_suite(conf)
    suite()

if __name__ == "__main__":
    import config
    cf = config.get_config()
    run(cf)
