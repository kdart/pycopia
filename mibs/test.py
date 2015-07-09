
"""
MIBs module unit tests.
"""

import unittest

# just import a basic sample
import pycopia.mibs
import pycopia.SMI
from pycopia.mibs import SNMPv2_SMI, SNMPv2_MIB

class MibsTests(unittest.TestCase):
    def test_import(self):
        self.assertEqual(pycopia.SMI.OIDMAP['1.3.6.1.1'].OID, [1,3,6,1,1])


if __name__ == '__main__':
    unittest.main()
