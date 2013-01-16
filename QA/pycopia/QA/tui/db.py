#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
Database access helper objects and functions. All database accesses for the TUI
go through here.

"""
from pycopia.db import models
from pycopia.QA import config


# lazy, implicit constructor. This avoides side effects if the module is simply imported.
class _Session_builder(object):
    def __getattr__(self, name):
        global _session
        if isinstance(_session, _Session_builder):
            _session = models.get_session()
        return getattr(_session, name)

_session = _Session_builder()


class _Config_getter(object):
    def __getattr__(self, name):
        global _config
        if isinstance(_config, _Config_getter):
            _config = config.get_config(session=_session)
        return getattr(_config, name)

_config = _Config_getter()


def get_environment_names():
    """Return a list of defined environment names, with user preference first."""
    envlist =  [r[0] for r in _session.query(models.Environment.name).order_by(models.Environment.name).all()]
    # move user preference to top of list
    userenvname = _config.userconfig.get("environmentname", u"default")
    envlist.remove(userenvname)
    envlist.insert(0, userenvname)
    return envlist


def get_report_names():
    """Get list of defined reports, but try to filter out those that write to stdout,
    or otherwise don't make sense in this UI.
    """
    rlist = _config.reports.keys()
    for notneeded in ("remote", "plain", "default", "ansi"):
        try:
            rlist.remove(notneeded)
        except ValueError:
            pass
    return rlist

def get_job_list():
    return _session.query(models.TestJob).order_by(models.TestJob.name).all()


if __name__ == "__main__":
    from pycopia import autodebug
    #print(get_environment_names())
    #print(get_report_names())
    print(get_job_list())
    pass
