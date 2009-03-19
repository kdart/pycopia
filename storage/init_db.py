#!/usr/bin/python2.5
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Place initial values in database.

"""

import sys

from pycopia.db import models

from pycopia.ISO import iso639a
from pycopia.ISO import iso3166

# schedules

def do_schedules(session):
    for name, m, h, dom, mon, dow in (
          ("Minutely", "*", "*", "*", "*", "*"),
          ("Hourly", "15", "*", "*", "*", "*"),
          ("Daily", "30", "4", "*", "*", "*"),
          ("TwiceADay", "40", "5,17", "*", "*", "*"),
          ("Weekly", "45", "4", "*", "*", "6"),
          ("BiWeekly", "45", "3", "*", "*", "3,6"),
          ("Monthly", "45", "5", "1", "*", "*"),
          ("Yearly", "55", "6", "1", "12", "*"),
          ):
        session.add(models.Schedule(name, minute=m, hour=h, day_of_month=dom, month=mon, day_of_week=dow))
    session.commit()


def do_functional_areas(session):
    for name, desc in (
            ("System", "System configuration."),
            ("UI", "User interface"),
            ("webUI", "Browser based user interface"),
            ("Network", "Routing, bridging, etc."),
            ):
        session.add(models.FunctionalArea(name, desc))
    session.commit()

def do_attribute_types(session):
    for name, vtype, desc in (
            ("isbase", 5, "Is a base item (don't follow fallback)."),
            ("fallback", 1, "Name of fallback item for more attributes, if any."),
            ("login", 1, "Username to access, if needed by accessmethod."),
            ("password",1, "Password for login, if needed by accessmethod."),
            ("accessmethod",1, 'Method of device access supported by Configurator constructor.'),
            ("initialaccessmethod",1, 'Initial access method to perform basic configure. e.g. "console"'),
            ("snmp_ro_community",1, "SNMP community string for RO access."),
            ("snmp_rw_community",1, "SNMP community string for RW access."),
            ("console_server",0, "Consoler server '(host, port)', if any."),
            ("power_controller",0, "Power controller '(name, socket)', if any."),
            ("monitor_port",0, "Etherswitch port that mirrors primary data interface."),
            ("admin_interface",1, "Name of administrative interface, if any."),
            ("data_interfaces",0, "Comma separated list of data/test interfaces."),
            ("phonenumber",1, "Assigned phone number, if a phone."),
            ("useragent", 1, "If a browser, the user agent."),
            ("wireless", 5, "Is a wireless communication device."),
            ("webenabled", 5, "Is a WWW enabled device."),
            ("url",1, "base URL to access device, if required."),
            ("serviceport", 1, "TCP/UDP/IP service port in the form 'tcp/80'."),
            ("servicepath", 1, "Path part of a URL pointing to service location."),
            ("servicequery", 1, "Mandatory URL query term that is constant."),
            ("protocol", 1, "Internet protocol a software implements."),
            ("hostname", 1, "Name to use as host name. Overrides base name."),
            ):
        session.add(models.AttributeType(name, vtype, desc))
        session.commit()

def do_language(session):
    for code, name in iso639a.LANGUAGECODES.items():
        session.add(models.Language(name=name.encode("utf-8"), isocode=code.strip()))
    session.commit()

def do_country(session):
    for code, name in iso3166.COUNTRYCODES.items():
          name = unicode(name, "ISO-8859-1").title()
          session.add(models.Country(name=name, isocode=code.strip()))
    session.commit()

def do_equipment_category(session):
    for name in (
           "other",
           "unknown",
           "chassis",
           "backplane",
           "container",     # chassis slot or daughter-card holder
           "powerSupply",
           "fan",
           "sensor",
           "module",        # plug-in card or daughter-card
           "port",
           "stack",        # stack of multiple chassis entities
           "cpu"):
        session.add(models.EquipmentCategory(name))
    session.commit()



def init_database(argv):
    try:
        url = argv[1]
    except IndexError:
        from pycopia import basicconfig
        cf = basicconfig.get_config("storage.conf")
        url = cf["database"]
    dbsession = models.get_session(url)
    try:
#        do_schedules(dbsession)
#        do_functional_areas(dbsession)
#        do_attribute_types(dbsession)
#        do_language(dbsession)
#        do_country(dbsession)
#        do_equipment_category(dbsession)
        pass
    finally:
        dbsession.close()


if __name__ == "__main__":
    init_database(sys.argv)

