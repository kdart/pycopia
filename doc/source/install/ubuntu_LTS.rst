.. Copyright 2012, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Installing on Ubuntu LTS (10.04)
================================


Prerequisites
-------------

Installation requires having some additional build-time dependencies installed
first.

Primarily, you need Python 2.7. In addition, some other third-party modules are
also required.

For each of the packages listed below, run this command: `apt-get install <pkgname>`

(Say `Y` to install dependencies also)

+----------------------------------+
| Package Name                     |
+==================================+
| vim                              |
+----------------------------------+
| subversion                       |
+----------------------------------+
| lighttpd                         |
+----------------------------------+
| libreadline-dev                  |
+----------------------------------+
| libsqlite3-dev                   |
+----------------------------------+
| libsmi2-dev                      |
+----------------------------------+
| openssl                          |
+----------------------------------+
| postgresql                       |
+----------------------------------+
| postgresql-client                |
+----------------------------------+
| libpq-dev                        |
+----------------------------------+

Install Source
--------------

Python 2.7 is not the version that LTS provides, so it has to be built from source.

Require packages
++++++++++++++++

Log in or sudo to _root_ account.

Download Python source distribution::

    cd ~
    wget http://www.python.org/ftp/python/2.7.3/Python-2.7.3.tar.bz2

Perform the following steps to build and install Python 2.7. ::

    # mkdir build
    # cd build
    # tar xjv ../Python-2.7.3.tar.bz2
    # cd Python-2.7.3
    # ./configure prefix=/usr --enable-shared --with-signal-module --with-threads
    # make
    # make altinstall
    # cd ..

Note: that is _altinstall_ NOT _install_. That will prevent the installation
      from overwriting the distributions packaged Python version.

Now the remaining third party modules must be obtained from the Python package index.

Get the _Distribute_ package. This one has to be _bootstrapped_ this way. ::

    # wget -q http://python-distribute.org/distribute_setup.py
    # python2.7 distribute_setup.py

And get the _pip_ tool. ::

    # wget -q https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    # python2.7 get-pip.py

Now you can get the remaining packages from the python package index.

For each of the packages listed below, run this command: `pip-2.7 install <pkgname>`

+----------------------------------+
| PIP Package Name                 |
+==================================+
| pyrex                            |
+----------------------------------+
| pyro4                            |
+----------------------------------+
| pyxml                            |
+----------------------------------+
| docutils                         |
+----------------------------------+
| psycopg2                         |
+----------------------------------+
| sqlalchemy                       |
+----------------------------------+
| simplejson                       |
+----------------------------------+
| pytz                             |
+----------------------------------+
| pycrypto                         |
+----------------------------------+


Prepare System
+++++++++++++++

We will add a group named `testers` that anyone that runs tests should be a member of.

We will also add a user named `tester`. This is a regular, non-root user that
can be used to run tests. But you can substitute yourself as this user. Other
users may also be added. New users should be added to the `testers` group.

As root, run the following commands: ::

    # CACHEDIR="/var/cache/pycopia"
    # RESULTSDIR="/var/www/localhost/htdocs/testresults"
    # groupadd testers
    # useradd -c Tester -U -G testers,users,audio,cdrom,dialout,video,games,crontab,messagebus,plugdev -m tester
    # echo "Remember to change password for new user tester."
    # passwd tester
    # mkdir -p $CACHEDIR
    # chown tester $CACHEDIR
    # chgrp testers $CACHEDIR
    # chmod 770 $CACHEDIR
    # mkdir -p $RESULTSDIR
    # chown tester $RESULTSDIR
    # chgrp testers $RESULTSDIR
    # chmod 770 $RESULTSDIR

Don't let the lighttpd server start by itself. ::

    # /etc/init.d/lighttpd stop
    # update-rc.d lighttpd disable

Link the web server document root to own host name. ::

    # ln -s /var/www/localhost /var/www/$(hostname -f)

Note that any new user added to the system should be added with the same `useradd` command line shown above.


Prepare Database
++++++++++++++++

For a full installation, you will need a postgresql database server running. If
you don't need a full installation you can skip this step.

Edit the main configuration file. ::

    # vim /etc/postgresql/8.4/main/postgresql.conf

    Search for line with `listen_addresses`, and uncomment the line. It should read:

    `listen_addresses = 'localhost'`


Edit the authentication configuration file. ::

    # vim /etc/postgresql/8.4/main/pg_hba.conf

    Find the following two lines at the bottom of the file:

    host    all         all         127.0.0.1/32          md5
    host    all         all         ::1/128               md5

    And change them to look like this:

    host    all         all         127.0.0.1/32          trust
    host    all         all         ::1/128               trust


Now restart the server. ::

    # /etc/init.d/postgresql-8.4 restart

Create the user and database. ::

    # su - postgres -c "createuser -D -l -R -S pycopia"
    # su - postgres -c "createdb -E unicode -O pycopia pycopia"


Install Pycopia
---------------

Now Pycopia is ready to be installed. Pycopia does not have a source or package
release. You must get the code repository from subversion and install from that
source tree. ::

    # mkdir ~/src
    # cd ~/src
    # svn checkout http://pycopia.googlecode.com/svn/trunk/ pycopia

    # cd pycopia
    # python2.7 setup.py install
    # mkdir /var/www/localhost/htdocs/testresults

Although this setup.py has the same name as the setuptools/distribute module}
setup file, it's really quite different. BUt you should use this one to install
because it compensates for setuptools file damage. It also lets you selectively
install sub-packages in case you don't want or need every one.


Prepare Database
++++++++++++++++

Create the tables and schema, and add basic data.

    # python2.7 -m pycopia.db.tables postgresql://pycopia@localhost/pycopia
    # python2.7 storage/init_db.py postgresql://pycopia@localhost/pycopia


Configuration
+++++++++++++

Pycopia has a modular set of configuration files kept in /etc/pycopia. Some of
these will need to be initialized. This involves copying and editing. These
configation files are actually Python files as well, so you will need to
maintain valid Python syntax when editing them.

Perform the following. ::

    # cd /etc/pycopia

Edit authentication module file. ::

    # # Copy and edit the auth module configuration.
    # cp auth.conf.example auth.conf
    # vim auth.conf

    # Change the `Admins` variable to yourself, and change the `SECRET_KEY` value.


Copy and edit the database module file.  If you used the instructions above to
install the database you won't have to change this file.  But if you have a
different name or location you should change this to reflect the database URL
that you are using. ::

    # cp database.conf.example database.conf
    # vim database.conf


Copy logging configuration file. This can be left as-is for now. ::

    # cp logging.cfg.dist logging.cfg


Copy Pyro config file. This can be left as-is for now. ::

    # cp pyro4.conf.dist pyro4.conf


Copy storage module configuration file. ::

    # cp storage.conf.example storage.conf
    # vim storage.conf

    ## Change the USERNAME to "www-data"
    ## Change ADMINS to yourself.


Copy website module files.  ::

    # cp website.conf.example website.conf
    # cp icons.conf.example icons.conf
    # vim website.conf

    ## Change the SITEUSER value to "www-data"
    ## Change the SITEOWNER to "tester" or your own account name.
    ## Remove the "myapp" from the list at the bottom.


All of these files can be changed to suit your needs at any time.


Database Setup
--------------

Test the installation. ::

    # dbcli
    db>

You should see the db prompt. Now add the tester user to the database. Just
press Enter to select the default choice for most questions.

|    db> **use User**
|    User> **create tester**
|    is_active?  [Y]>
|    is_staff?  [Y]>
|    is_superuser?  [N]> **y**
|    Choose from list. Enter to end, negative index removes from chosen.
|       1: testers
|    groups> **1**
|    Choose from list. Enter to end, negative index removes from chosen.
|    (You have selected all possible choices.)
|    You have:
|       1: testers
|    groups> **[Press Enter]**
|    Date and time for 'date_joined':  [2012-06-15 18:17:35.254429+00:00]>
|    Date and time for 'last_login':  [2012-06-15 18:17:35.254344+00:00]>
|    authservice? **system**
|    email?
|    first_name? **Mr**
|    last_name? **Tester**
|    middle_name?
|    username? **tester**
|    User> **ls**
|    id    : username                       first_name                     last_name                      email
|    1     : tester                         Mr                             Tester                         None
|    User> **exit**
|    db> **exit**
|    #

Now set some configuration.

|    # su - tester -c dbcli
|    db> **config**
|    Config:root> **mkdir tester**
|    Config:root> **cd tester**
|    Config:root.tester> **owner tester**
|    Config:root.tester> **exit**
|    Config:root> **ls**

You should do the above steps for every user that you add to the system.

You may want to edit the following values:

   - baseurl
   - documentroot
   - resultsdirbase

Changing the "localhost" part to your hosts fully qualified domain name. This is optional.

|    Config:root> **set baseurl 'http://myhost.mydomain.biz'**
|    Config:root> **set documentroot '/var/www/myhost.mydomain.biz'**
|    Config:root> **set resultsdirbase '/var/www/myhost.mydomain.biz/htdocs/testresults'""**
|    Config:root> **exit**


Finish
------

Now to really run tests you need to add a python package having a base name of
`testcases`. The framework scans this package namespace for test modules. You
can add modules adhering to the pycopia.QA.core API, or other test modules.

If you need to use external equipment you will need to populate this database
with Equipment entries, define Environment entries, and other configuration
entries. The test framework database is capable of modeling complex network
topologies. It stores every possible paramter related to the device under test
(DUT) as well as supporting equipment. You can also assign attributes to
eqiupment and environments. This is advanced setup that depends a lot on your
exact environment and test requirements.

Currently the only tool available for this is the `dbcli` tool. A full-featured web
interface is still in development.

What's Next?
------------

Additional code will likely have to be developed, using the Pycopia APIs, to
interface to custom equipment and the DUT. Pycopia provides a remote control
agent (after a minimal installation on the target system), and SNMP, SSH, HTTP,
and other modules to make it quick and easy to interface to a variety of
equipment. At also provides core classes for writing test cases and controller
modules. These are documented elsewhere.


