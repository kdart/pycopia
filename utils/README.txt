Pycopia utilities.

Opening the syslog, SNMP, and ICMP sockets require root privileges. This
presents a problem since most of Pycopia should be run as non-root. This
package contains a few "helpers". Small programs that are SUID to root that
act as proxies to forward the privileged ports to a local unix socket where
the non-root script can read from.

This package builds the following binaries:

- daemonize  
- pyntping  
- slogsink  
- straps

daemonize
	utility that can turn any program into a daemon (server).

pyntping
	SUID helper that opens ICMP socket and performs ICMP functions.

slogsink
	SUID helper that opens the syslog socket and relays syslog messages to
	a local port.

straps
	SUID helper that opens the SNMP trap port and forwards to a local socket.

You don't normally use these directly. The Python modules invoke them as
needed.

This module also provides a couple of patched standard extension modules that
fix a bug in each. 
