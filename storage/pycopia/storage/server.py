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
The Pycopia persistent storage server.

"""


import sys, os

from durus.storage_server import DEFAULT_PORT, DEFAULT_HOST, StorageServer
from durus.file_storage import FileStorage, TempFileStorage
from durus.logger import log, logger, direct_output



def start_durus(host, port, logfilename, dbfilename):
    logfile = open(logfilename, 'a+')
    direct_output(logfile)
    logger.setLevel(9)
    storage = FileStorage(dbfilename, repair=False, readonly=False)
    log(20, 'Storage file=%s host=%s port=%s', storage.fp.name, host, port)
    StorageServer(storage, host=host, port=port).serve()


def storaged(argv):
    """The Pycopia storage server.
    storaged [-h <serverhost>] [-p <serverport>] [-d <databasefile>] [-l <logfile>]
           [-n] [-?]

    where:

        -h is the server hostname to bind to.
        -p is the TCP port to use (other than the default)
        -d specifies the Durus file to use for the database.
        -l Log file name to use for logging.
        -n Do NOT become a daemon, stay in foreground (for debugging)
        -? This help screen.

    """
    import getopt
    from pycopia import basicconfig

    cf = basicconfig.get_config("storage.conf")
    host = cf.get("host", DEFAULT_HOST)
    port = cf.get("port", DEFAULT_PORT)
    DBFILE = os.path.expandvars(cf.get("dbfile"))
    LOGFILE = os.path.expandvars(cf.get("dblog"))
    del cf
    do_daemon = True

    try:
        optlist, args = getopt.getopt(argv[1:], "d:l:h:p:n?")
    except getopt.GetoptError:
        print storaged.__doc__
        sys.exit(2)

    for opt, optarg in optlist:
        if opt == "-d":
            DBFILE = optarg
        elif opt == "-l":
            LOGFILE = optarg
        elif  opt == "-h":
            host = optarg
        elif opt == "-p":
            port = int(optarg)
        elif opt == "-n":
            do_daemon = False
        elif opt == "-?":
            print storaged.__doc__
            return 2

    if do_daemon:
        from pycopia import daemonize
        daemonize.daemonize()
    try:
        start_durus(host, port, LOGFILE, DBFILE)
    except KeyboardInterrupt:
        return

