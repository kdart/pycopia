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

from hashlib import sha1
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import (sessionmaker, mapper, relation, 
        backref, column_property, synonym)
from sqlalchemy.orm.exc import NoResultFound

from pycopia.aid import hexdigest, unhexdigest
from pycopia.db import tables


def _get_secret():
    global SECRET_KEY
    from pycopia import basicconfig
    cf = basicconfig.get_config("auth.conf")
    SECRET_KEY = cf.SECRET_KEY
_get_secret()
del _get_secret



def create_session(addr):
    db = create_engine(addr)
    tables.metadata.bind = db
    return sessionmaker(bind=db)


#######################################
# basic address book table. Table columns originally mapped to
# StarOffice Addresses database.

class AddressBookEntry(object):
    pass
mapper(AddressBookEntry, tables.addressbook)


#######################################
# USERS for ownership and web server authentication.

# maps generic authservice names in the DB to actual PAM service profiles
# provided by pycopia.
_SERVICEMAP = {
    None: "pycopia", # default
    "system": "pycopia",
    "ldap": "pycopia_ldap",
    "local": None,
}


class Permission(object):
    pass

mapper(Permission, tables.auth_permission)


class Group(object):
    pass

mapper(Group, tables.auth_group,
    properties={
        "permissions": relation(Permission, lazy=True, secondary=tables.auth_group_permissions),
    }
)


class UserMessage(object):
    def __unicode__(self):
        return self.message

mapper(UserMessage, tables.auth_message)


class User(object):

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

def get_key():
    h = sha1()
    h.update(SECRET_KEY)
    h.update("ifucnrdthsurtoocls")
    return h.digest()[:16]

mapper(User, tables.auth_user,
    properties={
        "permissions": relation(Permission, lazy=True, secondary=tables.auth_user_user_permissions),
        "groups": relation(Group, lazy=True, secondary=tables.auth_user_groups),
        "messages": relation(UserMessage),
        "password": synonym('_password', map_column=True),
        "full_name": column_property( (tables.auth_user.c.first_name + " " + 
                tables.auth_user.c.last_name).label('full_name') ),
    })


# end USERS
#######################################

#######################################
# SESSIONS for web server sessions

class Cookie(object):
    pass

class Session(object):
    pass


mapper(Cookie, tables.cookies)
mapper(Session, tables.client_session)


# end SESSIONS
#######################################


class Config(object):
    pass

mapper(Config, tables.config, properties={
    'children': relation(Config, backref=backref('parent', remote_side=[tables.config.c.id]))
    })


"""
project_category
contacts
corp_attribute_type
corp_attributes
account_ids
addresses
capability_group
capability_type
capability
location
attribute_type
software_attributes
environmentattribute_type
environment_attributes
test_jobs
schedule
test_results_data
test_results
traps
components_suites
components_subcomponents
projects
projects_components
components
test_cases_areas
test_cases_prerequisites
testcase_prerequisites
test_plan
test_plan_testcases
test_cases
test_suites
test_suites_testcases
country_codes
test_suites_suites
country_sets
country_sets_countries
language_sets
language_sets_languages
corporations_services
functional_area
software_variants
software_variant
language_codes
equipment
equipment_attributes
equipment_model_attributes
equipment_subcomponents
equipment_software
equipment_category
equipment_model
equipment_model_embeddedsoftware
software
equipment_supported_projects
equipment_unsupported_projects
project_versions
corporations
environments
environments_partners
testequipment
testequipment_roles
software_category
"""


