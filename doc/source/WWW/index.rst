.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.


Pycopia WWW package
===================

Modules for working with the world wide web protocols and documents. This
package contains the web application framework ad various document parsers and
generators.

The primary idea behind this framework is to enable content generation in pure Python. There are no
HTML templates or embedded pseudo-HTML strings in the applications source code. Instead, you
construct pages using the API found in the :ref:`pycopia.WWW.XHTML` module. This pattern is more
like GUI construction using something like Tkinter module. It's primarily intended for highly
dynamic "web" interfaces of dedicated servers or network "appliances".

For database access the framework does not impose ANY special requirements, nor provide its own ORM.
You use what you wish, but would usually be the best-in-class Sqlalchemy_. But you could use the
DBAPI directly if you wish.

The primary use-case that this web framework is targeted for is small-scale web front-end for
administrative webUI of network appliances or services. Primarily for intra-net use (private
networks).

The framework is implemented as a collection of FCGI servers front-ended by the lighttpd_ web server.
Each FCGI server has its own configuration and may be run under a different user account
(non-root). This provides some additional security against server vulnerabilities by limiting the
resources available to it to only what it needs. The underlying user-based OS security model is
used to enforce this.

Each FCGI server is seamlessly mapped into a URL scheme. This scheme is dynamic. The URL path
directs a request to a specific server. When a new FCGI server is added it is accessed by using its
name as the first element in the URL's path.

For example, you configure a server with the name *myservice*. It would then be available under
*http://myhost.mydomain/myservice*/. Further path elements are directed to specific handers in the
server implementation.

The rest of the URL scheme is determined by regular expressions in a configuration file. Each
handler is a bit of Python code.

The framework is also multi-user, and enables tasks to be run on the host with the credentials of
the authenticated user.


.. toctree::
   :maxdepth: 2

Documents
---------

These module provide the API for dynamic construction of XHTML or HTML5 (XML serialization)
documents in pure Python. They also provide parsers to parse XHTML text into an object tree where
you can modify it and then re-serialize it to text.

.. automodule:: pycopia.WWW.XHTML
   :members:
   :undoc-members:

.. automodule:: pycopia.WWW.XHTMLparse
   :members:
   :undoc-members:

.. automodule:: pycopia.WWW.HTML5
   :members:
   :undoc-members:

.. automodule:: pycopia.WWW.HTML5parse
   :members:
   :undoc-members:


Client support
--------------

A web client based on pycurl_ library. Can also perform parallel requests. This can be used for
testing, or automated clients.

.. automodule:: pycopia.WWW.client
   :members:
   :undoc-members:


Application framework
---------------------

This is the server infrastructure, providing the FCGI servers and site controller. It natively
supports virtual hosts (services based on the host name). It also provides a remote API for
Javascript (client side) with JSON serialization.

.. automodule:: pycopia.WWW.framework
   :members:
   :undoc-members:

.. automodule:: pycopia.WWW.website
   :members:

.. automodule:: pycopia.WWW.json
   :members:
   :undoc-members:

.. automodule:: pycopia.WWW.fcgiserver
   :members:
   :undoc-members:


Application middleware
----------------------

Auth module
+++++++++++

This is a primary authentication module for the framework. It implements a custom authentication
scheme not found in other frameworks. It implements a CRAM-SHA1 authentication scheme to provide
secure, password based authentication over a clear channel (plain HTTP). It has both Python and
Javascript parts, so requires Javascript on the browser.

It also authenicates the user to the underlying OS using PAM. Therefore the web service acts as a proxy
for the user account known to the underlying OS.

Upon successful authentication the client is provided a session cookie to be used for future
requests to this server.

This enables reasonable security over plain HTTP. It is intended for intranet usage. It's not 100%
secure, so if more security is needed then use an encrypted channel, SSL (HTTPS). The framework does
provide support, using lighttpd_, for SSL. But using plain HTTP with this authentication scheme
provides reasonable security without the hassle of managing SSL certificates.

One side effect of this scheme is that it requires a clear password to be stored in the servers
database. This password is not actually stored in plaintext, but is encrypted using a master key.
This master key is currently found in the auth.conf configuration file, which should be readable
only by the root user. It should be possible to get this key from a secure source, such as a
smartcard or TPM, but this is not currently implemented.

.. automodule:: pycopia.WWW.middleware.auth
   :members:


.. _lighttpd: http://www.lighttpd.net/
.. _pycurl: http://pycurl.sourceforge.net/
.. _Sqlalchemy: http://www.sqlalchemy.org/

