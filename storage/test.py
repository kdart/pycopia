#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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


"""

import unittest

from pycopia import ipv4
from pycopia import proctools
from pycopia import scheduler

from pycopia.durusplus import persistent_attrdict
from pycopia.durusplus import persistent_data

from pycopia import storage
from pycopia.storage import server
from pycopia.storage import Storage
from pycopia.storage import storageCLI

class StorageTests(unittest.TestCase):

    def setUp(self):
        self._server = proctools.subprocess(server.storaged, ["storaged", "-n"])
        scheduler.sleep(2)

    def tearDown(self):
        self._server.kill()
        del self._server

    def test_PersistentAttrDict(self):
        ad = persistent_attrdict.PersistentAttrDict()
        ad.test = 1
        assert ad.data == {'test': 1}
        assert ad.test == 1
        ad.test = 2
        assert ad.data == {'test': 2}
        assert ad.test == 2
        assert ad["test"] == 2
        ad["test"] = 3
        assert ad["test"] == 3
        assert ad.test == 3

    def test_storage(self):
        db = Storage.get_client()
        r = db.get_root()
        c = r.add_container("subtree")
        c.value = 1
        db.commit()
        del db, r
        db = Storage.get_client()
        r = db.get_root()
        assert r.subtree.value == 1


if __name__ == '__main__':
    unittest.main()
