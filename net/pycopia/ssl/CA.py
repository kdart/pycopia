#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Certificate Authority functionality.

Implemented as a wrapper for openSSL and openssl binary tool.  Basically a port
to Python of the CA.pl script. Therefore, it's pretty ugly, and limited in what
your certs can contain.

It tries to automate the CA and other cert operations by using a custom openssl
configuration file and environment variables. But it's still limited and tedious.

The pyOpenSSL based modules are better. Use those if you can.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


import os
import errno
from pycopia import environ
from pycopia import proctools

OPENSSL = proctools.which("openssl")

SSL_CONFIG="/etc/pycopia/ssl/openssl.cnf"

# CA config, matches what's in the config file.
CA_DIR = "/etc/pycopia/ssl/CA"
CAKEY = "cakey.pem"
CAREQ = "careq.pem"
CACERT = "cacert.pem"
CADAYS = 1095


class Error(Exception):
    pass

class SSLExecError(Error):
    pass

class SSLConfigError(Error):
    pass


# TODO: other config file
CA_ENV = {
    "CA_PASSWORD": "pycopia",
    "CA_COUNTRY": "US",
    "DEFAULT_COUNTRY": "US",
    "CA_STATE": "California",
    "DEFAULT_STATE": "California",
    "CA_LOCALITY": "Mountain View",
    "CA_ORG": "Pycopia",
    "DEFAULT_ORG": "Pycopia",
    "CA_OU": "QA",
    "DEFAULT_OU": "QA",
    "CA_NAME": "Keith Dart",
    "CA_EMAIL": "keith@pycopia.org",
    "CHALLENGE_PASSWORD": "challenge",
}

# To test config file in shells
def write_env_file():
    with open("/tmp/ssl_ca_env.sh", "w") as fo:
        fo.write("""#!/bin/sh

export CA_PASSWORD="{CA_PASSWORD}"
export CA_COUNTRY="{CA_COUNTRY}"
export DEFAULT_COUNTRY="{DEFAULT_COUNTRY}"
export CA_STATE="{CA_STATE}"
export DEFAULT_STATE="{DEFAULT_STATE}"
export CA_LOCALITY="{CA_LOCALITY}"
export CA_ORG="{CA_ORG}"
export DEFAULT_ORG="{DEFAULT_ORG}"
export CA_OU="{CA_OU}"
export DEFAULT_OU="{DEFAULT_OU}"
export CA_NAME="{CA_NAME}"
export CA_EMAIL="{CA_EMAIL}"
export CHALLENGE_PASSWORD="{CHALLENGE_PASSWORD}"
""".format(**CA_ENV))


def run_openssl(config, app, *args, **kwargs):
    orig = os.getcwd()
    os.chdir(CA_DIR)
    env = environ.Environ()
    env.inherit()
    env.update(CA_ENV)
    try:
        cmd = ["{} {} -config {}".format(OPENSSL, app, config)]
        if kwargs:
            for name, value in kwargs.items():
                if name.endswith("_"):
                    name = name[:-1]
                if value is None:
                    cmd.append("-{}".format(name))
                else:
                    cmd.append("-{} {}".format(name, value))
        if args:
            for arg in args:
                if type(arg) is tuple:
                    name, value = arg
                    cmd.append("-{} {}".format(name, value))
                else:
                    cmd.append(str(arg))
        cmd = " ".join(cmd)
        exitstatus, out = proctools.getstatusoutput(cmd, env=env)
        if not exitstatus:
            raise SSLExecError(exitstatus)
    finally:
        os.chdir(orig)

def _make_ca_dir(name, mode=0777):
    try:
        os.mkdir(os.path.join(CA_DIR, name), mode)
    except OSError as oserr:
        if oserr[0] == errno.EEXIST:
            pass
        else:
            raise

class CAManager(object):

    def __init__(self, conf=None):
        self._config = conf or SSL_CONFIG
        if not os.path.exists(self._config):
            raise SSLConfigError("Config file does not exist: {}".format(self._config))

    def new_ca(self):
        if not os.path.exists(os.path.join(CA_DIR, "serial")):
            try:
                os.makedirs(CA_DIR, 0777)
            except OSError as oserr:
                if oserr[0] == errno.EEXIST:
                    pass
                else:
                    raise
            _make_ca_dir("certs")
            _make_ca_dir("crl")
            _make_ca_dir("newcerts")
            _make_ca_dir("private", 0700)
            open(os.path.join(CA_DIR, "index.txt"), "w").close() # equivalent to "touch"
            crlfile = os.path.join(CA_DIR, "crlnumber")
            if not os.path.exists(crlfile):
                with open(crlfile, "w+") as crlnumber:
                    crlnumber.write("01\n")
            serfile = os.path.join(CA_DIR, "serial")
            if not os.path.exists(serfile):
                with open(serfile, "w+") as serial:
                    serial.write("01\n")
            # Make CA certificate
            run_openssl(self._config, "req",
                    new=None,
                    keyout=os.path.join(CA_DIR, "private", CAKEY),
                    out=os.path.join(CA_DIR, CAREQ))
            # self-sign
            run_openssl(self._config, "ca",
                    ("infiles", os.path.join(CA_DIR, CAREQ)),
                    create_serial=None,
                    out=os.path.join(CA_DIR, CACERT),
                    days=CADAYS,
                    passin="env:CA_PASSWORD",
                    batch=None,
                    keyfile=os.path.join(CA_DIR, "private", CAKEY),
                    selfsign=None,
                    extensions="v3_ca",
                )

    def pkcs12(self, certname="newcert", keyname="newkey", comment="My Certificate"):
        newcert=certname+".p12"
        run_openssl(self._config, "pkcs12",
                in_=certname+".pem",
                inkey=keyname+".pem",
                certfile=os.path.join(CA_DIR, CACERT),
                out=newcert,
                export=None,
                name=comment)
        return newcert

    def xsign(self, infiles):
        run_openssl(self._config, "ca",
                ("infiles", " ".join(infiles)),
                policy="policy_anything",
            )

    def sign(self, out="newcert.pem", infile="newreq.pem"):
        run_openssl(self._config, "ca",
                ("infiles", infile),
                policy="policy_anything",
                out=out
            )

    def sign_ca(self, out="newcert.pem", infile="newreq.pem"):
        run_openssl(self._config, "ca",
                ("infiles", infile),
                policy="policy_anything",
                out=out,
                extensions="v3_ca",
            )

    def sign_cert(self, out="newcert.pem", infile="newreq.pem"):
        run_openssl(self._config, "x509",
                x509toreq=None,
                in_=infiles,
                signkey=infile,
                out="tmp.pem")
        self.sign(out=out, infiles="tmp.pem")

    def verify(self, cert="newcert.pem"):
        run_openssl(self._config, "verify", cert,
                CAfile=os.path.join(CA_DIR, CACERT),
            )


def get_manager(conf=None):
    return CAManager(conf)


def _test(argv):
    from pycopia import autodebug
    write_env_file()
    print("Shell environ in: /tmp/ssl_ca_env.sh")
    mgr = get_manager()
    mgr.new_ca()
    return mgr

if __name__ == "__main__":
    import sys
    mgr = _test(sys.argv)

