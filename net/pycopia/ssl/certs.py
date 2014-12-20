#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
#
# LICENSE: Apache 2 due to use of pyOpenSSL module (This is a derived work).
#
#       Licensed to the Apache Software Foundation (ASF) under one
#       or more contributor license agreements.  See the NOTICE file
#       distributed with this work for additional information
#       regarding copyright ownership.  The ASF licenses this file
#       to you under the Apache License, Version 2.0 (the
#       "License"); you may not use this file except in compliance
#       with the License.  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#       Unless required by applicable law or agreed to in writing,
#       software distributed under the License is distributed on an
#       "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#       KIND, either express or implied.  See the License for the
#       specific language governing permissions and limitations
#       under the License.

"""
SSL certificate management, including CA functionality.

Implemented using pyOpenSSL. This module presents a more Pythonic interface,
using more common Python data types and interfaces. Encapsulates the RFC2459
rules and recommendations so you don't have to deal with that.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import re
import pytz
from datetime import datetime

from OpenSSL import crypto


_FILETYPES = {
    "pem": crypto.FILETYPE_PEM,
    "crt": crypto.FILETYPE_PEM,
    "der": crypto.FILETYPE_ASN1,
    "asn1": crypto.FILETYPE_ASN1,
}

VERSION_1 = 1
VERSION_2 = 2
VERSION_3 = 3


class CertError(Exception):
    pass


class ExtensionEncodingError(CertError):
    pass


class CertificateRequest(object):

    def __init__(self, country=None, state=None, locality=None,
                 organization=None, organization_unit=None,
                 name=None, email=None, digest="sha1", filename=None):
        if filename is None:
            req = crypto.X509Req()
            subject = req.get_subject()
            if country:
                subject.C = country
            if state:
                subject.ST = state
            if locality:
                subject.L = locality
            if organization:
                subject.O = organization
            if organization_unit:
                subject.OU = organization_unit
            if name:
                subject.CN = name
            if email:
                subject.emailAddress = email
        else:
            ftype, text = get_type_and_text(filename)
            req = crypto.load_certificate_request(ftype, text)
        self._req = req

    def __str__(self):
        return "CertificateRequest: {}".format(self._get_subject())

    def _get_version(self):
        return self._req.get_version()

    def _set_version(self, ver):
        self._req.set_version(ver)

    version = property(_get_version, _set_version)

    def _get_subject(self):
        return DistinguishedName(_dn=self._req.get_subject())

    subject = property(_get_subject)

    def _get_pubkey(self):
        return PrivateKey(_key=self._req.get_pubkey())

    def _set_pubkey(self, pkey):
        if isinstance(pkey, PrivateKey):
            pkey = pkey._key
        self._req.set_pubkey(pkey)

    pubkey = property(_get_pubkey, _set_pubkey)

    def _set_extensions(self, extlist):
        nx = []
        for ext in extlist:
            if isinstance(ext, Extension):
                nx.append(ext._ext)
            elif isinstance(ext, crypto.X509ExtensionType):
                nx.append(ext)
        self._req.add_extensions(nx)
        self._req.set_version(VERSION_3)

    extensions = property(None, _set_extensions)

    def sign(self, pkey, digest="sha1"):
        return self._req.sign(pkey._key, digest)

    def verify(self, pubkey):
        return self._req.verify(pubkey._key)

    def emit(self, fo, filetype="pem"):
        fo.write(crypto.dump_certificate_request(_FILETYPES[filetype],
                 self._req))

    def get_pem(self):
        return crypto.dump_certificate_request(crypto.FILETYPE_PEM, self._req)


class PrivateKey(object):
    def __init__(self, filename=None, text=None, passphrase=None,
                 filetype="pem", bits=2048, _key=None):
        self.__passphrase = passphrase  # can also be a callable
        if _key is not None:
            key = _key
        else:
            ftype = _FILETYPES[filetype]
            if filename is not None:
                ftype, text = get_type_and_text(filename)
            if text is not None:
                if passphrase is not None:
                    key = crypto.load_privatekey(ftype, text, passphrase)
                else:
                    key = crypto.load_privatekey(ftype, text)
            else:
                key = crypto.PKey()
                key.generate_key(crypto.TYPE_RSA, bits)
        key.check()
        self._key = key

    bits = property(lambda self: self._key.bits())
    type = property(lambda self: {6: "RSA", 116: "DSA"}[self._key.type()])

    def check(self):
        self._key.check()

    def _set_pw(self, pw):
        self.__passphrase = str(pw)

    def _del_pw(self):
        self.__passphrase = None

    passphrase = property(None, _set_pw, _del_pw,
                          doc="The passphrase (write only attribute).")

    def encrypt(self, passphrase):
        self._key.check()
        text = crypto.dump_privatekey(crypto.FILETYPE_PEM, self._key,
                                      'aes-256-cbc', passphrase)
        return text

    def emit(self, fo, filetype="pem"):
        if self.__passphrase is not None:
            text = self.encrypt(self.__passphrase)
        else:
            text = crypto.dump_privatekey(crypto.FILETYPE_PEM, self._key)
        fo.write(text)

    def get_pem(self):
        return crypto.dump_privatekey(crypto.FILETYPE_PEM, self._key)


class Certificate(object):
    def __init__(self, filename=None, _cert=None):
        if _cert is not None:
            cert = _cert
        elif filename is not None:
            ftype, text = get_type_and_text(filename)
            cert = crypto.load_certificate(ftype, text)
        else:
            cert = crypto.X509()
        self._cert = cert

    def _get_subject(self):
        return DistinguishedName(_dn=self._cert.get_subject())

    def _set_subject(self, subj):
        self._cert.set_subject(subj)

    subject = property(_get_subject, _set_subject)

    def _get_issuer(self):
        return DistinguishedName(_dn=self._cert.get_issuer())

    def _set_issuer(self, issuer):
        self._cert.set_issuer(issuer)

    issuer = property(_get_issuer, _set_issuer)

    def _get_serial(self):
        return self._cert.get_serial_number()

    def _set_serial(self, num):
        return self._cert.set_serial_number(num)

    serial = property(_get_serial, _set_serial)

    def _get_not_before(self):
        return get_datetime(self._cert.get_notBefore())

    def _set_not_before(self, when):
        self._cert.set_notBefore(get_asn1time(when))

    notbefore = property(_get_not_before, _set_not_before)

    def _get_not_after(self):
        return get_datetime(self._cert.get_notAfter())

    def _set_not_after(self, when):
        self._cert.set_notAfter(get_asn1time(when))

    notafter = property(_get_not_after, _set_not_after)

    def _get_extensions(self):
        count = self._cert.get_extension_count()
        i = 0
        while i < count:
            yield Extension(_ext=self._cert.get_extension(i))
            i += 1

    def _set_extensions(self, extlist):
        nx = []
        for ext in extlist:
            if isinstance(ext, Extension):
                nx.append(ext._ext)
            elif isinstance(ext, crypto.X509ExtensionType):
                nx.append(ext)
        self._req.set_version(VERSION_3)
        self._cert.add_extensions(nx)

    extensions = property(_get_extensions, _set_extensions)

    def _get_version(self):
        return self._cert.get_version()

    def _set_version(self, ver):
        return self._cert.set_version(ver)

    version = property(_get_version, _set_version)

    def _get_pubkey(self):
        return PrivateKey(_key=self._cert.get_pubkey())

    def _set_pubkey(self, pubkey):
        if isinstance(pubkey, PrivateKey):
            pubkey = pubkey._key
        self._cert.set_pubkey(pubkey)

    pubkey = property(_get_pubkey, _set_pubkey)

    expired = property(lambda self: bool(self._cert.has_expired()))
    signature_algorithm = property(
        lambda self: self._cert.get_signature_algorithm())
    subject_name_hash = property(lambda self: self._cert.subject_name_hash())

    def digest(self, digest_name):
        return self._cert.digest(digest_name)

    def sign(self, pkey, digest_name):
        if isinstance(pkey, PrivateKey):
            pkey = pkey._key
        return self._cert.sign(pkey, digest_name)

    def emit(self, fo, filetype="pem"):
        fo.write(crypto.dump_certificate(_FILETYPES[filetype], self._cert))

    def get_pem(self):
        return crypto.dump_certificate(crypto.FILETYPE_PEM, self._cert)


class DistinguishedName(object):
    def __init__(self, country=None, state=None, locality=None,
                 organization=None, organization_unit=None,
                 name=None, email=None, _dn=None):
        if _dn is None:
            dn = crypto.X509Req().get_subject()
            if country:
                dn.C = country
            if state:
                dn.ST = state
            if locality:
                dn.L = locality
            if organization:
                dn.O = organization
            if organization_unit:
                dn.OU = organization_unit
            if name:
                dn.CN = name
            if email:
                dn.emailAddress = email
        else:
            dn = _dn
        self.__dict__["_dn"] = dn

    der = property(lambda self: self._dn.der())
    hash = property(lambda self: self._dn.hash())
    componenents = property(lambda self: self._dn.get_components())

    def __getattr__(self, name):
        return getattr(self.__dict__["_dn"], name)

    def __setattr__(self, name, value):
        return setattr(self._dn, name, value)

    def __str__(self):
        s = ["DN:"]
        for pn in ("C", "ST", "L", "O", "OU", "CN", "emailAddress"):
            val = getattr(self._dn, pn, None)
            if val:
                s.append("{}={}".format(pn, val))
        return "/".join(s)


class Extension(object):
    """Wrap an X509Extension.

    The wrapped class is a weird class: there is no method to get the value,
    but stringify it gets the value, but not the name. There is a getter method
    to get the name, but not the value. You can't pass None/null values for
    issuer or subject. You can't easily see if it's critical.

    So this wraps all that and presents a more Python calling signature and
    more informative string representation.
    """
    def __init__(self, typename=None, critical=None, value=None,
                 subject=None, issuer=None, _ext=None):
        if _ext is not None:
            ext = _ext
        # The following is necessary due to the nature of the
        # underlying C implementation.
        elif subject is None and issuer is None:
            ext = crypto.X509Extension(typename, critical, value)
        elif subject is not None and issuer is None:
            subject = subject._cert
            ext = crypto.X509Extension(typename, critical, value,
                                       subject=subject)
        elif subject is None and issuer is not None:
            issuer = issuer._cert
            ext = crypto.X509Extension(typename, critical, value,
                                       issuer=issuer)
        elif subject is not None and issuer is not None:
            issuer = issuer._cert
            ext = crypto.X509Extension(typename, critical, value,
                                       subject=subject, issuer=issuer)
        self._ext = ext

    critical = property(lambda self: self._ext.get_critical())
    short_name = property(lambda self: self._ext.get_short_name())
    der = property(lambda self: self._ext.get_data())
    value = property(lambda self: str(self._ext))

    def __str__(self):
        ext = self._ext
        return "{} = {}{}".format(
            ext.get_short_name(),
            "critical," if self._ext.get_critical() else "",
            str(ext).strip())

    def _der_(self):
        return self._ext.get_data()


# The following are specialized extensions with appropriate constructors.

class BasicConstraints(Extension):
    def __init__(self, is_ca=False, critical=False, pathlen=None):
        if is_ca:
            value = "CA:TRUE"
        else:
            value = "CA:FALSE"
        if pathlen is not None:
            value += ", pathlen:{:d}".format(pathlen)
        super(BasicConstraints, self).__init__("basicConstraints", critical,
                                               value)


class KeyUsage(Extension):
    """keyUsage extension.

    Values can be one or more of:
        "digitalSignature",
        "nonRepudiation",
        "keyEncipherment",
        "dataEncipherment",
        "keyAgreement",
        "keyCertSign",
        "cRLSign",
        "encipherOnly",
        "decipherOnly",
    in a list.
    """
    def __init__(self, values, critical=False):
        assert len(values) > 0, "Need at least one value."
        super(KeyUsage, self).__init__("keyUsage", critical, ", ".join(values))


class ExtendedKeyUsage(Extension):
    """ExtendedkeyUsage extension.

    Value can be one or more of (first column):
     serverAuth             SSL/TLS Web Server Authentication.
     clientAuth             SSL/TLS Web Client Authentication.
     codeSigning            Code signing.
     emailProtection        E-mail Protection (S/MIME).
     timeStamping           Trusted Timestamping
     msCodeInd              Microsoft Individual Code Signing (authenticode)
     msCodeCom              Microsoft Commercial Code Signing (authenticode)
     msCTLSign              Microsoft Trust List Signing
     msSGC                  Microsoft Server Gated Crypto
     msEFS                  Microsoft Encrypted File System
     nsSGC                  Netscape Server Gated Crypto
    in a list.
    """
    def __init__(self, values, critical=False):
        assert len(values) > 0, "Need at least one value."
        super(ExtendedKeyUsage, self).__init__("extendedKeyUsage", critical,
                                               ", ".join(values))


class AuthorityKeyIdentifier(Extension):
    def __init__(self, issuer, critical=False):
        super(AuthorityKeyIdentifier, self).__init__(
            "authorityKeyIdentifier", critical, "keyid,issuer",
            issuer=issuer)


class SubjectKeyIdentifier(Extension):
    def __init__(self, subject, critical=False):
        super(SubjectKeyIdentifier, self).__init__(
            "subjectKeyIdentifier", critical, "hash", subject=subject)


class SubjectAltName(Extension):
    """The subject alternative name extension allows various literal values to
    be included in the certificate.

    These include email (an email address) URI a uniform resource indicator,
    DNS (a DNS domain name), RID (a registered ID: OBJECT IDENTIFIER), IP (an
    IP address), dirName (a distinguished name) and otherName.

    Examples
    --------
     SubjectAltName(["my@other.address", "http://my.url.here/"])
     SubjectAltName(["192.168.7.1"])
     SubjectAltName(["13::17"])
     SubjectAltName(["www.mydomain.com", "*.mydomain.com"])
    """

    def __init__(self, values, critical=False):
        assert len(values) > 0, "Need at least one value."
        new = []
        for value in values:
            pre = guess_altname_prefix(value)
            new.append("{}:{}".format(pre, value))
        super(SubjectAltName, self).__init__("subjectAltName", critical,
                                             ",".join(new))


class IssuerAltName(Extension):
    def __init__(self, values, critical=False):
        assert len(values) > 0, "Need at least one value."
        new = []
        for value in values:
            if isinstance(value, Certificate):
                super(IssuerAltName, self).__init__(
                    "issuerAltName", critical, "issuer:copy", issuer=value)
                break
            elif isinstance(value, crypto.X509):
                super(IssuerAltName, self).__init__(
                    "issuerAltName", critical, "issuer:copy",
                    issuer=Certificate(_cert=value))
                break
            pre = guess_altname_prefix(value)
            new.append("{}:{}".format(pre, value))
        else:
            super(IssuerAltName, self).__init__("issuerAltName", critical,
                                                ",".join(new))


class AuthorityInfoAccess(Extension):
    """The authority information access extension gives details about how to
    access certain information relating to the CA.

    Examples
    --------
    AuthorityInfoAccess(ocsp="http://ocsp.my.host/")
    AuthorityInfoAccess(caissuers="http://my.ca/ca.html")
    AuthorityInfoAccess(ocsp="http://ocsp.my.host/",
        caissuers="http://my.ca/ca.html")
    """
    def __init__(self, ocsp=None, caissuers=None, critical=False):
        new = []
        if ocsp is not None:
            pre = guess_altname_prefix(ocsp)
            new.append("OCSP;{}:{}".format(pre, ocsp))
        if caissuers is not None:
            pre = guess_altname_prefix(caissuers)
            new.append("caIssuers;{}:{}".format(pre, caissuers))
        if not new:
            raise ValueError("You must supply at least ocsp or caissuers")
        super(AuthorityInfoAccess, self).__init__(
            "authorityInfoAccess", critical, ",".join(new))


class CrlDistributionPoints(Extension):
    """A CRL distribution point.
    """
    def __init__(self, values, critical=False):
        assert len(values) > 0, "Need at least one value."
        new = []
        for value in values:
            pre = guess_altname_prefix(value)
            new.append("{}:{}".format(pre, value))
        super(CrlDistributionPoints, self).__init__("crlDistributionPoints",
                                                    critical, ",".join(new))


class PolicyConstraints(Extension):
    """A Policy constraint.
    requireExplicitPolicy or inhibitPolicyMapping

    """
    def __init__(self, requireexplicitpolicy=None, inhibitpolicymapping=None,
                 critical=False):
        new = []
        if requireexplicitpolicy is not None:
            new.append("requireExplicitPolicy:{:d}".format(
                requireexplicitpolicy))
        if inhibitpolicymapping is not None:
            new.append("inhibitPolicyMapping:{:d}".format(
                inhibitpolicymapping))
        if not new:
            raise ValueError(
                "You must supply at least one of "
                "inhibitpolicymapping or requireexplicitpolicy")
        super(PolicyConstraints, self).__init__("policyConstraints", critical,
                                                ",".join(new))


class InhibitAnyPolicy(Extension):
    """Inhibit Any Policy.

    Value is a non-negative integer.
    """
    def __init__(self, value, critical=False):
        super(InhibitAnyPolicy, self).__init__("inhibitAnyPolicy", critical,
                                               str(value))


class NameConstraints(Extension):
    """Named constraints.
    """
    def __init__(self, permitted=None, excluded=None, critical=False):
        new = []
        if permitted is not None:
            pre = guess_altname_prefix(permitted)
            new.append("permitted;{}:{}".format(pre, permitted))
        if excluded is not None:
            pre = guess_altname_prefix(excluded)
            new.append("excluded;{}:{}".format(pre, excluded))
        super(NameConstraints, self).__init__("nameConstraints", critical,
                                              ",".join(new))


class OCSPNoCheck(Extension):
    """Don't check OCSP.
    """
    def __init__(self, critical=False):
        super(OCSPNoCheck, self).__init__("noCheck", critical, "ignored")


def guess_altname_prefix(string):
    if "@" in string:
        return "email"
    elif "://" in string:
        return "URI"
    elif "::" in string:
        return "IP"  # ipv6
    elif re.search(br"(?:\D+\.)+\D{1,4}", string, re.I):
        return "DNS"
    elif re.search(br"(?:[0-9]{1,3}\.)+\d{1,3}", string):
        return "IP"
    else:
        raise ValueError("Unabled to determine altname type")


def create_rsa_keypair(bits=2048):
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, bits)
    return PrivateKey(_key=pkey)


def create_dsa_keypair(bits=2048):
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_DSA, bits)
    return PrivateKey(_key=pkey)


def now_utc():
    return datetime.now(pytz.utc)


def get_asn1time(when):
    """Return an ASN1 normalized time from a datetime object or ISO 8601
    string.
    """
    if when is None:
        when = now_utc()
    if isinstance(when, str):
        import iso8601
        when = iso8601.parse_date(when)
    assert type(when) is datetime
    return when.strftime("%Y%m%d%H%M%S%z")


def get_datetime(when):
    """Return datetime object (UTC) from ASN1 time string."""
    dt = datetime.strptime(when, "%Y%m%d%H%M%SZ")
    return dt.replace(tzinfo=pytz.utc)


def get_type_and_text(filename):
    ftype = _FILETYPES[filename[-3:]]
    text = open(filename).read()
    return ftype, text


def der(obj):
    try:
        return obj._der_()
    except AttributeError:
        raise ExtensionEncodingError(
            "Not an extension object: {!r}".format(obj))


if __name__ == "__main__":
    import sys
    from pycopia import autodebug

    req = CertificateRequest(country="US",
                             state="California",
                             locality="Mountain View",
                             organization="Acme Labs Inc.",
                             name="www.acmeacme.com")
    req.emit(sys.stdout)

    pw = PrivateKey()
    ektext = pw.encrypt("secret")
    print(repr(ektext))
    npw = PrivateKey(text=ektext, passphrase="secret")
    # npw.emit(sys.stdout)

    cert = Certificate()
    dt = now_utc()
    print(get_asn1time(now_utc().isoformat()))
    cert = Certificate(filename="/var/tmp/google.pem")
    print(cert.subject)
    print(cert.notafter)
    for gext in cert.extensions:
        print(gext)
        print('----------')

    # cacert = Certificate(filename="/etc/pycopia/ssl/CA/cacert.pem")

    cert = Certificate(filename="/var/tmp/github.pem")
    print(cert.subject)
    print(cert.issuer)
    print(cert.notafter)

    print("\n== Extensions :")
    rawext = crypto.X509Extension("keyUsage", False,
                                  "digitalSignature, nonRepudiation")
    ext = Extension(_ext=rawext)
    print(ext)
    print(KeyUsage(["digitalSignature", "keyEncipherment"]))
    print(BasicConstraints(is_ca=True))
    print(BasicConstraints(is_ca=True, critical=True))
    print(BasicConstraints(is_ca=True, critical=True, pathlen=0))
    print(BasicConstraints(is_ca=False))
    print(ExtendedKeyUsage(["serverAuth", "clientAuth"]))
    print(SubjectKeyIdentifier(cert))
    # print( AuthorityKeyIdentifier(cacert))
    print(SubjectAltName(["my@other.address", "http://my.url.here/"]))
    print(SubjectAltName(["192.168.7.1"]))
    print(SubjectAltName(["13::17"]))
    print(SubjectAltName(["www.mydomain.com", "*.mydomain.com"]))
    print(IssuerAltName([cert]))
    print(IssuerAltName(["issuer.com"]))
    print(AuthorityInfoAccess(ocsp="http://ocsp.my.host/"))
    print(AuthorityInfoAccess(caissuers="http://my.ca/ca.html"))
    print(AuthorityInfoAccess(ocsp="http://ocsp.my.host/",
          caissuers="http://my.ca/ca.html"))
    print(CrlDistributionPoints(["http://myhost.com/myca.crl"]))
    print(PolicyConstraints(requireexplicitpolicy=3))
    print(PolicyConstraints(inhibitpolicymapping=3))
    print(InhibitAnyPolicy(3))
    print(NameConstraints(permitted="192.168.0.0/255.255.0.0"))
    print(NameConstraints(excluded="172.16.0.0/255.255.0.0"))
    print(OCSPNoCheck())
    print(OCSPNoCheck(critical=True))

    dn = DistinguishedName(country="US", state="California",
                           organization="myCA")
    print(dn)

    # example of creating a more complex req with extensions.
    req = CertificateRequest(
        country="US",
        state="California",
        locality="Mountain View",
        organization="Acme Labs Inc.",
        organization_unit="Slaves",
        name="www.foo.com",
        )
    req.extensions = [
        BasicConstraints(is_ca=False),
        KeyUsage(["nonRepudiation", "digitalSignature",
                  "keyEncipherment"]),
        SubjectAltName(["www.foo.com", "www.bar.com"]),
        ]
    req.pubkey = npw
    req.sign(npw)
    with open("/tmp/testreq.pem", "w+") as fo:
        req.emit(fo)
    with open("/tmp/testreq.key", "w+") as fo:
        npw.emit(fo)
