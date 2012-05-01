#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 and onwards, Keith Dart <keith@dartworks.biz>
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
Collection of SSL management operations.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia import tty
from pycopia.ssl import certs


def get_pass(verify):
    """Basic callback for getting passphrase."""
    if verify:
        retries = 3
        while retries > 0:
            pw = tty.getpass("Passphrase? ")
            npw = tty.getpass("Passphrase again? ")
            if pw == npw:
                return pw
            print("Phrases don't match. Please try again.")
            retries -= 1
        raise crypto.Error("Too many tries reading passphrase.")
    else:
        return tty.getpass("Passphrase? ")


def certificate_request(filename, country=None, state=None, locality=None, organization=None,
        organization_unit=None, name=None, email=None, passphrase=get_pass):
    """Basic certificate request with no extensions."""
    req = certs.CertificateRequest(country, state, locality, organization,
            organization_unit, name, email)
    pkey = certs.create_rsa_keypair()
    req.pubkey = pkey
    req.sign(pkey, "sha1")
    with open(filename, "w+") as fo:
        req.emit(fo)
    print("Encrypt private key with secret.")
    ektext = pkey.encrypt(passphrase)
    with open(filename+".key", "w+") as fo:
        fo.write(ektext)




if __name__ == "__main__":
    certificate_request("/tmp/certreqtest.pem",
            country="US",
            state="California",
            locality="Santa Clara",
            organization="Acme Inc.",
            organization_unit="Slaves",
            name="www.foo.com",
            )
