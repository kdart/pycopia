#!/usr/bin/python2.5
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
#
#    NOTE: Most of Pycopia is licensed under the LGPL license. This module is
#    licenced under the GPL licence due to nmap license requirements. It
#    parses the nmap XML output and is thus considered a derivitive work.
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.


"""
Import nmap XML output into the network model.

Even though nmap reports discovered hosts as hosts, they are actually
interfaces. This importer creates unattached interfaces. A
user/administrator will have to go and assign created interfaces to hosts.

"""


import xml
if hasattr(xml, "use_pyxml"):
    xml.use_pyxml()
import xml.sax.sax2exts
import xml.sax.handler

from pycopia.logging import warn
from pycopia import ipv4
from pycopia.db import models



# States the XML host scanner can be in
NOTINTERESTED = 0
INTERESTED = 1

INTERFACE_TYPE_ID = 6 # ethernetCsmacd
INTERFACE_TYPE = None

def get_network(session, ipnet):
    """Returns a Network model object. Creates one if necessary."""
    q = session.query(models.Network).filter(models.Network.ipnetwork==ipnet.CIDR)
    try:
        net = q.one()
    except models.NoResultFound:
        args = dict(name=ipnet.CIDR, ipnetwork=ipnet.CIDR, layer=3)
        net = models.create(models.Network, **args)
        session.add(net)
        session.commit()
    return net


def get_equipment(session, hostname):
    q = session.query(models.Equipment).filter(models.Equipment.name==hostname)
    try:
        host = q.one()
    except models.NoResultFound:
        return get_unknown_equipment(session, hostname)
    else:
        return host


def get_unknown_equipment(session, hostname):
    model = get_unknown_equipment_model(session)
    eq = models.create(models.Equipment, name=hostname, model=model, comment="Added by nmap importer.")
    session.add(eq)
    session.commit()
    return eq


def get_unknown_equipment_model(session):
    cat = session.query(models.EquipmentCategory).filter(models.EquipmentCategory.name=="unknown").one()
    q = session.query(models.EquipmentModel).filter(models.and_(
                models.EquipmentModel.name=="Unknown",
                models.EquipmentModel.category==cat)
                )
    try:
        model = q.one()
    except models.NoResultFound:
        manu = session.query(models.Corporation).filter(models.Corporation.name=="Custom").one()
        model = models.create(models.EquipmentModel, name="Unknown", category=cat, manufacturer=manu)
        session.add(model)
        session.commit()
    return model


def get_interface_type(session, enumeration=INTERFACE_TYPE_ID):
    global INTERFACE_TYPE
    if INTERFACE_TYPE is None:
        q = session.query(models.InterfaceType).filter(
                models.InterfaceType.enumeration==enumeration,
                )
        INTERFACE_TYPE = q.one()
    return INTERFACE_TYPE


def add_interface(session, attribs):
    """Add new interface, don't duplicate existing one.
    Also try connecting to equipment if possible.
    """
    network = attribs.get("network")
    ipaddr = attribs["ipaddr"]
    attribs["interface_type"] = get_interface_type(session)
    q = session.query(models.Interface).filter(models.and_(
                models.Interface.network==network,
                models.Interface.ipaddr==ipaddr)
                )
    # try to find equipment by matching name.
    hostname = attribs.get("description")
    if hostname:
        eq = get_equipment(session, hostname)
        del attribs["description"]
    else:
        eq = None
    attribs["equipment"] = eq

    try:
        intf = q.one()
    except models.NoResultFound:
        intf = models.create(models.Interface, **attribs)
        session.add(intf)
        session.commit()
    else:
        models.update(intf, **attribs)
        session.commit()





class ContentHandler(object):
    """SAX content handler.

    Manages state and adds interface records when enough host data is collected.
    """
    def __init__(self):
        self._state = NOTINTERESTED
        self.network = None
        self.session = None
        self._locator = None
        self._current_interface = None

    def startDocument(self):
        self.session = models.get_session()

    def endDocument(self):
        sess = self.session
        self.session = None
        self.network = None
        sess.commit()
        sess.close()

    def startElement(self, name, attribs):
        if name == "nmaprun":
            cidr = attribs["args"].split()[-1] # assumes one network scanned
            net = ipv4.IPv4(str(cidr)) # cidr would be unicode
            self.network = get_network(self.session, net)
            return
        elif name == "host":
            self._state = INTERESTED
            self._current_interface = dict(name="unknown")
        elif self._state == NOTINTERESTED:
            return
        elif name == "status":
            if attribs["state"] == "down":
                self._state = NOTINTERESTED
                self._current_interface = None
        elif name == "address":
            if attribs["addrtype"] == "ipv4":
                intf = self._current_interface
                intf["ipaddr"] = str(attribs["addr"])
                intf["layer"] = 3
                intf["network"] = self.network
            elif attribs["addrtype"] == "mac":
                self._current_interface["macaddr"] = str(attribs["addr"])
        elif name == "hostnames": # strange that namp treats hostnames and addresses differently.
            pass
        elif name == "hostname":
            # stuff name in description since we can't tell what host this
            # is attached to yet. User can later use this to map to host.
            # Keep only the last one.
            self._current_interface["description"] = str(attribs["name"])


    def endElement(self, name):
        if name == "host":
            if self._state == INTERESTED:
                intf = self._current_interface
                self._current_interface = None
                add_interface(self.session, intf)
            self._state = NOTINTERESTED

    def setDocumentLocator(self, locator):
        self._locator = locator

    def characters(self, text):
        pass

    def processingInstruction(self, target, data):
        'handle: xml version="1.0" encoding="ISO-8859-1"?'
        pass

    def startPrefixMapping(self, prefix, uri):
        warn("!!! Unhandled prefix: %r" % (prefix,))

    def endPrefixMapping(self, prefix):
        pass

    def skippedEntity(self, name):
        warn("unhandled ignorableWhitespace: %r" % (whitespace,))

    def ignorableWhitespace(self, whitespace):
        warn("unhandled ignorableWhitespace: %r" % (whitespace,))

    def startElementNS(self, cooked_name, name, atts):
        pass

    def endElementNS(self, name, rawname):
        pass

    # DTDHandler interface
    def notationDecl(self, name, publicId, systemId):
        """Handle a notation declaration event."""
        warn("unhandled notationDecl: %r %r %r" % ( name, publicId, systemId))

    def unparsedEntityDecl(self, name, publicId, systemId, ndata):
        warn("unhandled unparsedEntityDecl: %r %r %r %r" % ( name, publicId, systemId, ndata))

    # entity resolver interface
    def resolveEntity(self, publicId, systemId):
        pass


class ErrorHandler(object):
    def __init__(self, logfile=None):
        self._lf = logfile

    def error(self, exception):
        "Handle a recoverable error."
        #raise exception
        warn("XML error: %s" % (exception,))

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        #raise exception
        warn("XML fatalError: %s" % (exception,))

    def warning(self, exception):
        "Handle a warning."
        warn("XML Warning: %s" % (exception,))



def get_parser(logfile=None, namespaces=0, validate=0, external_ges=0):
    handler = ContentHandler()
    # create parser
    parser = xml.sax.sax2exts.XMLParserFactory.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, namespaces)
    parser.setFeature(xml.sax.handler.feature_validation, validate)
    parser.setFeature(xml.sax.handler.feature_external_ges, external_ges)
    parser.setFeature(xml.sax.handler.feature_external_pes, 0)
    parser.setFeature(xml.sax.handler.feature_string_interning, 1)
    # set handlers
    parser.setContentHandler(handler)
    parser.setDTDHandler(handler)
    parser.setEntityResolver(handler)
    parser.setErrorHandler(ErrorHandler(logfile))
    return parser


def import_nmap(filename):
    parser = get_parser()
    parser.parse(filename)



if __name__ == "__main__":
    import sys
    from pycopia import autodebug
    import_nmap("/home/keith/tmp/10-223-1-0.xml")
