#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
#
#    Copyright (C) 2009  Keith Dart <keith@kdart.com>
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
Defines database ORM objects.

"""

import warnings
from datetime import datetime, timedelta
from pytz import timezone
from hashlib import sha1
import cPickle as pickle

from sqlalchemy import create_engine, and_, select

from sqlalchemy.orm import (sessionmaker, mapper, relation, class_mapper,
        backref, column_property, synonym, _mapper_registry)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.properties import ColumnProperty, RelationProperty

from sqlalchemy.ext.associationproxy import association_proxy

from pycopia.aid import hexdigest, unhexdigest, Enums
from pycopia.db import tables


UTC = timezone('UTC')

# type codes
OBJECT=0; STRING=1; UNICODE=2; INTEGER=3; FLOAT=4; BOOLEAN=5

# The base types that an AttributeType may have.
VALUETYPES = Enums("object", "string", "unicode", 
                    "integer", "float", "boolean")

# Test result types - these objects may report a result
OBJECTTYPES = Enums("module", "TestSuite", "Test", "TestRunner", "unknown")
[MODULE, SUITE, TEST, RUNNER, UNKNOWN] = OBJECTTYPES

# results a test case can produce.
TESTRESULTS = Enums(PASSED=1, FAILED=0, INCOMPLETE=-1, ABORT=-2, NA=-3, EXPECTED_FAIL=-4)
TESTRESULTS.sort()
[EXPECTED_FAIL, NA, ABORT, INCOMPLETE, FAILED, PASSED] = TESTRESULTS


# Set password encryption key for the site.
def _get_secret():
    global SECRET_KEY
    from pycopia import basicconfig
    try:
        cf = basicconfig.get_config("auth.conf")
        SECRET_KEY = cf.SECRET_KEY
    except basicconfig.ConfigReadError:
        warnings.warn("User encryption key not found for auth app, using default.")
        SECRET_KEY = "Testkey"
_get_secret()
del _get_secret



def create_session(addr):
    db = create_engine(addr)
    tables.metadata.bind = db
    return sessionmaker(bind=db)


def get_session(url=None):
    if url is None:
        from pycopia import basicconfig
        cf = basicconfig.get_config("storage.conf")
        url = cf["database"]
    session_class = create_session(url)
    return session_class()


#######################################
# Basic address book table. This table originally mapped to
# StarOffice Addresses database and is here just for nostalgia. ;-)

class AddressBookEntry(object):
    pass
mapper(AddressBookEntry, tables.addressbook)


#######################################
# User management for AAA for web applications.

class Permission(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Permission(%r, %r)" % (self.name, self.description)

mapper(Permission, tables.auth_permission)


class Group(object):
    ROW_DISPLAY = ("name", "permissions")
    def __init__(self, name):
        self.name = str(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Group(%r)" % (self.name,)

mapper(Group, tables.auth_group,
    properties={
        "permissions": relation(Permission, lazy=True, secondary=tables.auth_group_permissions),
    }
)


class User(object):
    ROW_DISPLAY = ("username", "first_name", "last_name", "email")

    def __init__(self, username=None, first_name=None, last_name=None, email=None, authservice="local",
            is_staff=True, is_active=True, is_superuser=False, last_login=None, date_joined=None):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_staff = is_staff
        self.is_active = is_active
        self.last_login = last_login
        self.date_joined = date_joined
        self.is_superuser = is_superuser
        self.authservice = authservice

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.username)

    # Passwords are stored in the database encrypted.
    def _set_password(self, passwd):
        # pycrypto package.  http://www.amk.ca/python/code/crypto
        from Crypto.Cipher import AES
        eng = AES.new(get_key(), AES.MODE_ECB)
        self._password = hexdigest(eng.encrypt((passwd + "\0"*(16 - len(passwd)))[:16]))

    def _get_password(self):
        from Crypto.Cipher import AES
        eng = AES.new(get_key(), AES.MODE_ECB)
        return eng.decrypt(unhexdigest(self._password)).strip("\0")

    password = property(_get_password, _set_password)

    def set_last_login(self):
            self.last_login = datetime.now(UTC)

    def get_session_key(self):
        h = sha1()
        h.update(str(self.id))
        h.update(self.username)
        h.update(str(self.last_login))
        return h.hexdigest()


def get_key():
    h = sha1()
    h.update(SECRET_KEY)
    h.update("ifucnrdthsurtoocls")
    return h.digest()[:16]


mapper(User, tables.auth_user,
    properties={
        "permissions": relation(Permission, lazy=True, secondary=tables.auth_user_user_permissions),
        "groups": relation(Group, lazy=True, secondary=tables.auth_user_groups),
        "password": synonym('_password', map_column=True),
        "full_name": column_property( (tables.auth_user.c.first_name + " " +
                tables.auth_user.c.last_name).label('full_name') ),
    })



def create_user(session, pwent):
    """Create a new user with a default password and name taken from the
    password entry (from the passwd module). 
    """
    now = datetime.now(UTC)
    fullname = pwent.gecos
    if fullname.find(",") > 0:
        [last, first] = fullname.split(",", 1)
    else:
        fnparts = fullname.split(None, 1)
        if len(fnparts) == 2:
            [first, last] = fnparts
        else:
            first, last = pwent.name, fnparts[0]
    grp = session.query(Group).filter(Group.name=="tester").one() # should already exist
    user = User(username=pwent.name, first_name=first, last_name=last, authservice="system",
            is_staff=True, is_active=True, last_login=now, date_joined=now)
    user.password = pwent.name + "123" # default, temporary password
    user.groups = [grp]
    session.add(user)
    session.commit()
    return user


class UserMessage(object):
    ROW_DISPLAY = ("user", "message")
    def __unicode__(self):
        return self.message

mapper(UserMessage, tables.auth_message,
    properties={
        "user": relation(User, backref="messages"),
    }
)


# end USERS
#######################################

class Cookie(object):
    pass
mapper(Cookie, tables.cookies)

#######################################
# SESSIONS for web server sessions

class Session(object):
    def __init__(self, user, lifetime=48):
        self.session_key = user.get_session_key()
        self.expire_date = user.last_login + timedelta(hours=lifetime)
        self.session_data = pickle.dumps({
            "username": user.username,
            })

    def _get_data(self):
        return pickle.loads(self.session_data)

    def _set_data(self, d):
        self.session_data = pickle.dumps(d)

    data = property(_get_data, _set_data)

    def __getitem__(self, key):
        return self._get_data()[key]

    def __setitem__(self, key, value):
        d = self._get_data()
        d[key] = value
        self._set_data(d)

    def __delitem__(self, key):
        d = self._get_data()
        del d[key]
        self._set_data(d)

    def is_expired(self):
        return datetime.now(UTC) >= self.expire_date


mapper(Session, tables.client_session)

# end SESSIONS
#######################################


class Country(object):
    def __init__(self, name, isocode):
        self.name = name
        self.isocode = isocode

    def __str__(self):
        return "%s(%s)" % (self.name, self.isocode)

mapper(Country, tables.country_codes)


class CountrySet(object):
    pass

mapper(CountrySet, tables.country_sets,
    properties={
        "countries": relation(Country, lazy=True, secondary=tables.country_sets_countries),
    }
)


#######################################
# Misc

class LoginAccount(object):
    pass

mapper(LoginAccount, tables.account_ids)


class Language(object):
    def __init__(self, name, isocode):
        self.name = name
        self.isocode = isocode

    def __str__(self):
        return "%s(%s)" % (self.name, self.isocode)

mapper(Language, tables.language_codes)


class LanguageSet(object):
    pass

mapper(LanguageSet, tables.language_sets, 
    properties={
        "languages": relation(Language, lazy=True, secondary=tables.language_sets_languages),
    }
)

class Address(object):
    ROW_DISPLAY = ("address", "address2", "city", "stateprov", "postalcode")

    def __init__(self, address, address2, city, stateprov, postalcode, country=None):
        self.address = address
        self.address2 = address2
        self.city = city
        self.stateprov = stateprov
        self.postalcode = postalcode
        self.country = country

    def __str__(self):
        return "%s, %s, %s %s" % (self.address, self.city, self.stateprov, self.postalcode)

mapper(Address, tables.addresses,
    properties={
        "country": relation(Country),
    }
)


class Contact(object):
    ROW_DISPLAY = ("prefix", "firstname", "middlename", "lastname")

    def __init__(self, firstname, lastname, middlename=None, prefix=None, title=None, position=None, 
            phonehome=None, phoneoffice=None, phoneother=None, phonework=None, phonemobile=None,
            pager=None, fax=None, email=None, note=None):
        self.prefix = prefix
        self.firstname = firstname
        self.middlename = middlename
        self.lastname = lastname
        self.title = title
        self.position = position
        self.phonehome = phonehome
        self.phoneoffice = phoneoffice
        self.phoneother = phoneother
        self.phonework = phonework
        self.phonemobile = phonemobile
        self.pager = pager
        self.fax = fax
        self.email = email
        self.note = note

    def __str__(self):
        return "%s %s" % (self.firstname, self.lastname)

mapper(Contact, tables.contacts,
    properties={
        "address": relation(Address),
        "user": relation(User),
    }
)


class Schedule(object):
    ROW_DISPLAY = ("name", "user", "minute", "hour", "day_of_month", "month", "day_of_week")
    def __init__(self, name, minute="*", hour="*", day_of_month="*", month="*", day_of_week="*", 
                user=None):
        self.name = name
        self.minute = minute
        self.hour = hour
        self.day_of_month = day_of_month
        self.month = month
        self.day_of_week = day_of_week
        if user is not None:
            self.user_id = user.id
        else:
            self.user_id = None

    def __str__(self):
        return "%s: %s %s %s %s %s" % (self.name, self.minute, self.hour,
                self.day_of_month, self.month, self.day_of_week)

mapper(Schedule, tables.schedule,
    properties={
        "user": relation(User),
    }
)


class Location(object):
    ROW_DISPLAY = ("locationcode",)

mapper(Location, tables.location,
    properties={
        "address": relation(Address),
        "contact": relation(User),
    }
)

#######################################
# capabilities and attributes

class CapabilityGroup(object):
    pass

mapper(CapabilityGroup, tables.capability_group)


class CapabilityType(object):
    ROW_DISPLAY = ("name", "value_type", "description", "group")

    value_type = property(lambda s: VALUETYPES.find(s.value_type_c),
        lambda s, v: setattr(s, "value_type_c", int(v)))

mapper(CapabilityType, tables.capability_type,
    properties={
        "group": relation(CapabilityGroup),
    }
)



class Capability(object):
    ROW_DISPLAY = ("type", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

mapper(Capability, tables.capability,
)


class AttributeType(object):
    ROW_DISPLAY = ("name", "value_type", "description")
    def __init__(self, name, vtype, description):
        self.name = name
        self.value_type_c = int(vtype)
        self.description = description

    value_type = property(lambda s: VALUETYPES.find(s.value_type_c),
        lambda s, v: setattr(s, "value_type_c", int(v)))

    def __str__(self):
        return "%s(%s)" % (self.name, VALUETYPES.find(s.value_type_c), self.description)

mapper(AttributeType, tables.attribute_type)


# deal consistently with the value_type_c field.

#def get_value_type_enum(obj):
#    return VALUETYPES.find(obj.value_type_c)
#
#def set_value_type_from_enum(obj, val):
#        setattr(obj, "value_type_c", int(val))



#######################################
# projects

class ProjectCategory(object):
    ROW_DISPLAY = ("name",)
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

mapper(ProjectCategory, tables.project_category)


class FunctionalArea(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name

    def __repr__(self):
        return "FunctionalArea(%r, %r)" % (self.name, self.description)


mapper(FunctionalArea, tables.functional_area)


class Component(object):
    ROW_DISPLAY = ("name", "description", "created")
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.created = datetime.now(UTC)

    def __str__(self):
        return self.name

mapper(Component, tables.components)


class Project(object):
    ROW_DISPLAY = ("name", "category", "description")

    def __init__(self, name, description, leader=None):
        self.name = name
        self.description = description
        self.leader = leader
        self.created = datetime.now(UTC)

    def __str__(self):
        return self.name

mapper(Project, tables.projects,
    properties={
        "components": relation(Component, lazy=True, secondary=tables.projects_components),
        "category": relation(ProjectCategory, backref="projects"),
        "leader": relation(User),
    }
)

class ProjectVersion(object):
    ROW_DISPLAY = ("project", "major", "minor", "subminor", "build")

    def __init__(self, project, major=1, minor=0, subminor=0, build=0):
        self.project = project
        self.major = major
        self.minor = minor
        self.subminor = subminor
        self.build = build

    def __str__(self):
        return "%s %s.%s.%s-%s" % (self.project, self.major, self.minor,
                self.subminor, self.build)

mapper(ProjectVersion, tables.project_versions, 
    properties={
        "project": relation(Project),
    }
)


#######################################
# Corporations

class CorporateAttributeType(object):
    ROW_DISPLAY = ("name", "value_type", "description")

    value_type = property(lambda s: VALUETYPES.find(s.value_type_c),
        lambda s, v: setattr(s, "value_type_c", int(v)))

mapper(CorporateAttributeType, tables.corp_attribute_type)



class Corporation(object):
    ROW_DISPLAY = ("name",)

    def __str__(self):
        return self.name

mapper(Corporation, tables.corporations,
    properties={
        "services": relation(FunctionalArea, lazy=True, secondary=tables.corporations_services),
        "address": relation(Address),
        "contact": relation(Contact),
        "country": relation(Country),
    }
)


class CorporateAttribute(object):
    ROW_DISPLAY = ("type", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

mapper(CorporateAttribute, tables.corp_attributes,
    properties={
        "type": relation(CorporateAttributeType),
        "corporation": relation(Corporation, backref="attributes"),
    }
)


#######################################
# Software model

# should also be called role or function
class SoftwareCategory(object):
    ROW_DISPLAY = ("name", "description")

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name

mapper(SoftwareCategory, tables.software_category)


class SoftwareVariant(object):
    ROW_DISPLAY = ("name", "country", "language", "encoding")
    def __init__(self, name, encoding, country=None, language=None):
        self.name = name
        self.encoding = encoding
        self.country = country
        self.language = language

    def __str__(self):
        return "%s(%s)" % (self.name, self.encoding)

mapper(SoftwareVariant, tables.software_variant,
    properties={
        "language": relation(Language),
        "country": relation(Country),
    }
)


class Software(object):
    ROW_DISPLAY = ("name", "category", "manufacturer", "vendor")

mapper (Software, tables.software,
    properties={
        "variants": relation(SoftwareVariant, lazy=True, secondary=tables.software_variants),
        "category": relation(SoftwareCategory),
        "vendor": relation(Corporation, 
                primaryjoin=tables.software.c.vendor_id==tables.corporations.c.id),
        "manufacturer": relation(Corporation, 
                primaryjoin=tables.software.c.manufacturer_id==tables.corporations.c.id),
    }
)

class SoftwareAttribute(object):

    ROW_DISPLAY = ("type", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

mapper(SoftwareAttribute, tables.software_attributes,
    properties={
            "software": relation(Software, backref="attributes"),
            "type": relation(AttributeType),
    },
)



#######################################
# Equipment model

# similar to ENTITY-MIB::PhysicalClass
class EquipmentCategory(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "%s(%d)" % (self.name, self.id + 1)

mapper(EquipmentCategory, tables.equipment_category)

# IANAifType, minus obsolete and deprecated.
class InterfaceType(object):
    def __init__(self, name, enum):
        self.name = name
        self.enumeration = enum

    def __str__(self):
        return "%s(%d)" % (self.name, self.enumeration)

mapper(InterfaceType, tables.interface_type)

class Network(object):
    ROW_DISPLAY = ("name", "bridgeid", "ipnetwork", "notes")
    def __init__(self, name, ipnetwork=None, bridgeid=None, notes=None):
        self.name = name
        self.ipnetwork = ipnetwork.CIDR
        self.bridgeid = bridgeid
        self.notes = notes

    def __str__(self):
        if self.ipnetwork is not None:
            return "Net: %s (%s)" % (self.name, self.ipnetwork)
        elif bridgeid is not None:
            return "Net: %s: %s" % (self.name, self.bridgeid)
        else:
            return "Net: %s" % (self.name,)

mapper(Network, tables.networks)


class EquipmentModel(object):
    ROW_DISPLAY = ("manufacturer", "name", "category")

    def __str__(self):
        return self.name

mapper(EquipmentModel, tables.equipment_model,
    properties={
        "embeddedsoftware": relation(Software, secondary=tables.equipment_model_embeddedsoftware),
        "category": relation(EquipmentCategory, order_by=tables.equipment_category.c.id),
        "manufacturer": relation(Corporation, order_by=tables.corporations.c.id),
    }
)


class EquipmentModelAttribute(object):
    ROW_DISPLAY = ("type", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

    def __str__(self):
        return "%s = %s" % (self.name, self.value)

mapper(EquipmentModelAttribute, tables.equipment_model_attributes,
    properties={
            "equipmentmodel": relation(EquipmentModel, backref="attributes"),
            "type": relation(AttributeType),
    },

)


class Equipment(object):
    ROW_DISPLAY = ("name", "model", "serno")

    def __str__(self):
        return self.name

mapper(Equipment, tables.equipment,
    properties={
        "model": relation(EquipmentModel),
        "subcomponents": relation(Equipment, 
                backref=backref('parent', remote_side=[tables.equipment.c.id])),
        "software": relation(Software, lazy=True, secondary=tables.equipment_software),
    },
)


class EquipmentAttribute(object):
    ROW_DISPLAY = ("name", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

    def __str__(self):
        return "%s = %s" % (self.name, self.value)

mapper(EquipmentAttribute, tables.equipment_attributes,
    properties={
            "equipment": relation(Equipment, backref="attributes"),
    },
)



class Interface(object):
    ROW_DISPLAY = ("name", "ifindex", "interface_type", "equipment", "macaddr", "ipaddr", "network")
    def __init__(self, name, alias=None, ifindex=None, description=None,
            macaddr=None, vlan=0, ipaddr=None, mtu=None, speed=None,
            status=0, iftype=None, equipment=None, network=None):
        self.name = name
        self.alias = alias
        self.ifindex = ifindex
        self.description = description
        self.macaddr = macaddr
        self.vlan = vlan
        self.ipaddr = ipaddr
        self.mtu = mtu
        self.speed = speed
        self.status = status

    def __str__(self):
        return "%s (%s)" % (self.name, self.ipaddr)

mapper(Interface, tables.interfaces,
    properties = {
        "interface_type": relation(InterfaceType, order_by=tables.interfaces.c.id),
        "parent": relation(Interface, backref=backref("subinterface",
                                remote_side=[tables.interfaces.c.id])),
        "network": relation(Network, backref="interfaces", order_by=tables.networks.c.id),
        "equipment": relation(Equipment, backref="interfaces"),
    }
)


### environments

class EnvironmentAttributeType(object):
    ROW_DISPLAY = ("name", "value_type", "description")
    def __init__(self, name, vtype, description):
        self.name = name
        self.value_type_c = int(vtype)
        self.description = description

    value_type = property(lambda s: VALUETYPES.find(s.value_type_c),
        lambda s, v: setattr(s, "value_type_c", int(v)))

    def __str__(self):
        return "%s(%s)" % (self.name, VALUETYPES.find(s.value_type_c))

mapper(EnvironmentAttributeType, tables.environmentattribute_type,
)


class Environment(object):
    ROW_DISPLAY = ("name", "owner")
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    equipment = association_proxy('testequipment', 'equipment')


mapper(Environment, tables.environments,
    properties={
        "owner": relation(User),
        "countries": relation(CountrySet),
        "languages": relation(LanguageSet),
        "project": relation(Project),
#        "DUT": column_property(
#                and_(tables.testequipment.c.environment_id==tables.environments.c.id,
#                    tables.testequipment.c.UUT==True).label("DUT"),
#               ),

    },
)

class TestEquipment(object):
    """Binds equipment and a test environment.
    Also specifies the unit under test.
    """
    ROW_DISPLAY = ("equipment", "UUT")

mapper(TestEquipment, tables.testequipment,
    properties={
        "roles": relation(SoftwareCategory, secondary=tables.testequipment_roles),
        "equipment": relation(Equipment),
        "environment": relation(Environment, backref="testequipment"),
    },
)


class EnvironmentAttribute(object):
    ROW_DISPLAY = ("type", "value")

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _del_value(self):
        self._set_value(None)

    value = property(_get_value, _set_value, _del_value)

    def __str__(self):
        return "%s = %s" % (self.type, self.value)

mapper(EnvironmentAttribute, tables.environment_attributes,
    properties={
            "environment": relation(Environment, backref="attributes"),
            "type": relation(EnvironmentAttributeType),
    },
)



#######################################
# trap storage

class Trap(object):
    ROW_DISPLAY = ("timestamp", "value")
    def _get_value(self):
        return pickle.loads(self.pickle)

    def _set_value(self, obj):
        self.pickle = pickle.dumps(obj)

    value = property(_get_value, _set_value)


mapper(Trap, tables.traps)


#######################################

#######################################
# Test relations and results

class TestCase(object):
    ROW_DISPLAY = ("name", "purpose", "testimplementation")

    def __str__(self):
        return self.name

mapper(TestCase, tables.test_cases,
    properties={
        "functionalarea": relation(FunctionalArea, secondary=tables.test_cases_areas),
    },
)


class TestSuite(object):
    ROW_DISPLAY = ("name", "suiteimplementation")

mapper(TestSuite, tables.test_suites,
    properties={
        "testcases": relation(TestCase, secondary=tables.test_suites_testcases, backref="suite"),
        "components": relation(Component, secondary=tables.components_suites, backref="suites"),
        "subsuites": relation(TestSuite, secondary=tables.test_suites_suites, 
            primaryjoin=tables.test_suites.c.id==tables.test_suites_suites.c.from_testsuite_id,
            secondaryjoin=tables.test_suites_suites.c.to_testsuite_id==tables.test_suites.c.id,
            backref="suite"),
    },
)


class TestJob(object):
    ROW_DISPLAY = ("name", "schedule")

mapper(TestJob, tables.test_jobs,
    properties = {
        "user": relation(User),
        "environment": relation(Environment, order_by=tables.environments.c.name),
        "suite": relation(TestSuite),
        "schedule": relation(Schedule),
    }
)


class TestResultData(object):
    def __init__(self, data, note=None):
        self.pickle = pickle.dumps(data)
        self.note = note

    def _get_data(self):
        return pickle.loads(self.pickle)

    def _set_data(self, obj):
        self.pickle = pickle.dumps(obj)

    data = property(_get_data, _set_data)


mapper(TestResultData, tables.test_results_data)


class TestResult(object):
    ROW_DISPLAY = ("testcase", "testimplementation", "tester", "testresult", "resultslocation")
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
             setattr(self, name, value)

    testresult = property(lambda self: TESTRESULTS.find(int(self.result)))
    objecttype = property(lambda self: OBJECTTYPES.find(int(self.objecttype_c)))


mapper(TestResult, tables.test_results,
    properties = {
        "tester": relation(User),
        "data": relation(TestResultData, backref="testresult"),
        "environment": relation(Environment, order_by=tables.environments.c.name),
        "testcase": relation(TestCase),
        "subresults": relation(TestResult, backref=backref("parent",
                                remote_side=[tables.test_results.c.id])),
    }
)


#######################################
# configuration data

class Config(object):
    ROW_DISPLAY = ("name", "value", "user", "testcase", "testsuite")

    def __init__(self, name, value, container=None, testcase=None,
            testsuite=None, user=None):
        self.name = name
        self._set_value(value)
        self.parent_id = container.id
        self.testcase = testcase
        self.testsuite = testsuite
        self.user = user

    def _set_value(self, value):
        self.pickle = pickle.dumps(value)

    def _get_value(self):
        return pickle.loads(self.pickle)

    def _del_value(self):
        self.pickle = pickle.dumps(None)

    value = property(_get_value, _set_value, _del_value)

    def __str__(self):
        return "%s=%r" % (self.name, self.value)

    def add_container(self, name):
        return Config(name, None, container=self, user=self.user,
            testcase=self.testcase, testsuite=self.testsuite)

    def get_container(self, name, session):
        c = session.query(Config).filter(
                Config.name==name, Config.parent_id==self.id, Config.user==self.user).one()
        return ConfigWrapper(session, c)


mapper(Config, tables.config, 
    properties={
        'children': relation(Config, cascade="all", 
            backref=backref("container", remote_side=[tables.config.c.id, tables.config.c.user_id])),
        'testcase': relation(TestCase),
        'testsuite': relation(TestSuite),
        'user': relation(User),
    }
)


class ConfigWrapper(object):
    """Make a relational table quack like a dictionary."""
    def __init__(self, session, config):
        self.session = session
        self.node = config

    def __setitem__(self, name, value):
        new = Config(name, value, container=self.node, user=self.node.user,
            testcase=self.node.testcase, testsuite=self.node.testsuite)
        self.session.add(new)
        self.session.commit()

    def __getitem__(self, name):
        return self.session.query(Config).filter(and_(Config.parent_id==self.node.id,
                Config.name==name)).one()

    def __delitem__(self, name):
        try:
            o = self.__getitem__(name)
        except NoResultFound:
            return
        self.session.delete(o)

    def keys(self):
        for name, in self.session.query(Config.name).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield name

    def items(self):
        for name, value in self.session.query(Config.name, Config.pickle).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield name, pickle.loads(value)

    def values(self):
        for value, in self.session.query(Config.pickle).filter(and_(
            Config.parent_id==self.node.id, 
            Config.user==self.node.user, 
            Config.testcase==self.node.testcase, 
            Config.testsuite==self.node.testsuite)):
            yield pickle.loads(value)


#######################################

#######################################


def class_names():
    for mapper in _mapper_registry:
        yield mapper._identity_class.__name__


def get_metadata(class_):
    rv = [("Column Name", "ColumnType", "Default")]
    for prop in class_mapper(class_).iterate_properties:
        proptype = type(prop)
        if prop.key.startswith("_") or prop.key == "id":
            continue
        name = prop.key
        if proptype is ColumnProperty:
            coltype = type(prop.columns[0].type).__name__
            try:
                default = prop.columns[0].default
            except AttributeError:
                default = None
        elif proptype is RelationProperty:
            coltype = RelationProperty.__name__
            default = None
        else:
            continue
        rv.append((name, coltype, default))
    return rv


def get_rowdisplay(class_):
    return getattr(class_, "ROW_DISPLAY", None) or [t[0] for t in get_metadata(class_)[1:]]


if __name__ == "__main__":
    from pycopia import autodebug
    print get_metadata(Location)


