/*
 * straps.c --
 *
 * A simple SNMP trap-sink. Mainly for scotty's snmp code, but also
 * usable by other clients. The straps demon listens to the snmp-trap
 * port 162/udp and forwards the received event to connected clients
 * (like scotty). Because the port 162 needs root access and the port
 * can be opened only once, the use of a simple forwarding demon is
 * a good choice.
 *
 * The client can connect to the AF_UNIX domain stream socket
 * /tmp/.straps-<port> and will get the trap-packets in raw binary form:
 *
 *	4 bytes ip-address (in network-byte-order) of the sender
 *	2 bytes port-number (in network-byte-order) of the sender
 *	4 bytes data-length (in host-byte-order) followed by the 
 *	n data-bytes of the packet.
 *
 * Copyright (c) 1994-1996 Technical University of Braunschweig.
 *
 * See the file "license.terms" for information on usage and redistribution
 * of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 */

#include <config.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/un.h>
#include <sys/stat.h>

#ifdef HAVE_UNISTD_H
#include <unistd.h>
#endif

#ifdef HAVE_SYS_SELECT_H
#include <sys/select.h>
#endif

#ifndef FD_SETSIZE
#define FD_SETSIZE 32
#endif

/*
 * Default values for the SNMP trap port number, the name of 
 * the UNIX domain socket and the IP multicast address.
 */

#define SNMP_TRAP_PORT	162
#define SNMP_TRAP_NAME	"snmp-trap"
#define SNMP_TRAP_PATH	"/tmp/.straps"
#define SNMP_TRAP_MCIP	"234.0.0.1"

/*
 * A signal handler which basically ignores all SIGPIPE signals.
 * It re-installs itself for all the bozo's outside.
 */

#ifdef SIGPIPE
static void
ign_pipe(dummy)
    int dummy;
{
    signal(SIGPIPE, ign_pipe);
}
#endif


int
main(argc, argv)
    int argc;
    char *argv[];
{
    struct servent *se;
    struct sockaddr_in taddr, laddr;
    struct sockaddr_un saddr, daddr;
    int trap_s, serv_s, slen, dlen, llen, rc, i;
    fd_set fds;
    static int cl_addr [FD_SETSIZE];
    char buf[2048], path[1024];
    int go_on;
    int mcast_s = -1;
    char *name;
    int port;
    
    /* 
     * Check the number of arguments. We accept an optional argument
     * which specifies the port number we are listening on.
     */

    if (argc > 2) {
	fprintf(stderr, "usage:  straps [port]\n");
	exit(1);
    }

    if (argc == 2) {
	name = argv[1];
	port = atoi(argv[1]);
    } else {
	name = SNMP_TRAP_NAME;
	port = SNMP_TRAP_PORT;
    }
    
    /*
     * Get the port that we are going to listen to. Check that
     * we do not try to open a priviledged port number, with
     * the exception of the SNMP trap port.
     */

    if ((se = getservbyname(name, "udp"))) {
	port = ntohs(se->s_port);
    }

    if (port != SNMP_TRAP_PORT && port < 1024) {
	fprintf(stderr, "straps: access to port %d denied\n", port);
	exit(1);
    }

    /*
     * Close any "leftover" FDs from the parent.  There is a relatively
     * high probability that the parent will be scotty, and that the client
     * side of the scotty-straps connection is among the open FDs.  This
     * is bad news if the parent scotty goes away, since this will eventually
     * cause straps to "block against itself" in the "forward data to client"
     * write() calls below, since straps itself is not consuming data from
     * the client side of the leftover open socket.
     */

    for (i = 3; i < FD_SETSIZE; i++) {
	(void) close(i);
    }

    /*
     * Open and bind the normal trap socket:
     */

    if ((trap_s = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
	perror("straps: unable to open trap socket");
	exit(1);
    }
    
    taddr.sin_family = AF_INET;
    taddr.sin_port = htons(port);
    taddr.sin_addr.s_addr = INADDR_ANY;

    if (bind(trap_s, (struct sockaddr *) &taddr, sizeof(taddr)) < 0) {
	perror("straps: unable to bind trap socket");
	exit(1);
    }

#ifdef HAVE_MULTICAST
    if ((mcast_s = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
	perror("straps: unable to open multicast trap socket");
    }

    if (mcast_s > 0) {
        struct ip_mreq mreq;
        mreq.imr_multiaddr.s_addr = inet_addr(SNMP_TRAP_MCIP);
	mreq.imr_interface.s_addr = htonl(INADDR_ANY);
	if (setsockopt(mcast_s, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*) &mreq,
		       sizeof(mreq)) == -1) {
	    perror("straps: unable to join multicast group");
	    close(mcast_s);
	    mcast_s = -1;
	}
    }

#ifdef SO_REUSEADDR

    /* 
     * Allow others to bind to the same UDP port. 
     */

    if (mcast_s > 0) {
        int on = 1;
	setsockopt(mcast_s, SOL_SOCKET, SO_REUSEADDR, 
		   (char *) &on, sizeof(on));
    }
#endif

    if (mcast_s > 0) {
        struct sockaddr_in maddr;
        maddr.sin_family = AF_INET;
	maddr.sin_port = htons(port);
	maddr.sin_addr.s_addr = htonl(INADDR_ANY);
	if (bind(mcast_s, (struct sockaddr*) &maddr, sizeof(maddr)) == -1) {
	    perror("straps: unable to bind multicast trap socket");
	    close(mcast_s);
	    mcast_s = -1;
	}
    }
#endif

    /*
     * Open the client socket. First unlink the name and set the umask
     * to 0. This should not make any problems and it makes security
     * people happy. (Suggested by David Keeney <keeney@zk3.dec.com>)
     */

    sprintf(path, "%s-%d", SNMP_TRAP_PATH, port);
    unlink(path);
    umask(0);

    if ((serv_s = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
	perror("straps: unable to open server socket");
	exit(1);
    }

    memset((char *) &saddr, 0, sizeof(saddr));
    
    saddr.sun_family = AF_UNIX;
    strcpy(saddr.sun_path, path);
    slen = sizeof(saddr) - sizeof(saddr.sun_path) + strlen(saddr.sun_path);

    if (bind(serv_s, (struct sockaddr *) &saddr, slen) < 0) {
	perror("straps: unable to bind server socket");
	exit(1);
    }
    
    if (listen(serv_s, 5) < 0) {
	perror("straps: unable to listen on server socket");
	exit(1);
    }

#ifdef SIGPIPE
    signal(SIGPIPE, ign_pipe);
#endif
    
    /*
     * Fine everything is ready; lets listen for events: 
     * the for(;;) loop aborts, if the last client went away.
     */

    for (go_on = 1; go_on; ) {

	  FD_ZERO(&fds);
	  FD_SET(trap_s, &fds);
	  FD_SET(serv_s, &fds);
	  if (mcast_s > 0) {
	      FD_SET(mcast_s, &fds);
	  }

	  /* fd's connected from clients. listen for EOF's: */
	  for (i = 0; i < FD_SETSIZE; i++) {
	      if (cl_addr [i] > 0) FD_SET(i, &fds);
	  }

	  rc = select(FD_SETSIZE, &fds, (fd_set *) 0, (fd_set *) 0, 
		       (struct timeval *) 0);
	  if (rc < 0) {
	      if (errno == EINTR || errno == EAGAIN) continue;
	      perror("straps: select failed");
	  }
	  
	  if (FD_ISSET(trap_s, &fds)) {
	      /* read trap message and forward to clients: */
	      llen = sizeof(laddr);
	      if ((rc = recvfrom(trap_s, buf, sizeof(buf), 0, 
				 (struct sockaddr *) &laddr, &llen)) < 0) {
		  perror("straps: recvfrom failed");
		  continue;
	      }
	      
	      for (i = 0; i < FD_SETSIZE; i++) {
		  if (cl_addr [i] > 0) {
		      /* XXX: check writeability */
		      if (write(i, (char *) 
				 &laddr.sin_addr.s_addr, 4) != 4
			  || write(i, (char *) &laddr.sin_port, 2) != 2
			  || write(i, (char *) &rc, 4) != 4
			  || write(i, buf, rc) != rc)
			{
			    cl_addr [i] = 0;
				close(i);
			}
		  }
	      }
	      
	      /* should we go on ? */
	      for (go_on = 0, i = 0; i < FD_SETSIZE; i++) {
		  go_on += cl_addr [i] > 0;
	      }

	  } else if (mcast_s > 0 && FD_ISSET(mcast_s, &fds)) {
	      /* read trap message and forward to clients: */
	      llen = sizeof(laddr);
	      if ((rc = recvfrom(mcast_s, buf, sizeof(buf), 0, 
				 (struct sockaddr *) &laddr, &llen)) < 0) {
		  perror("straps: recvfrom failed");
		  continue;
	      }
	      
	      for (i = 0; i < FD_SETSIZE; i++) {
		  if (cl_addr [i] > 0) {
		      /* XXX: check writeability */
		      if (write(i, (char *) &laddr.sin_addr.s_addr, 4) != 4
			  || write(i, (char *) &laddr.sin_port, 2) != 2
			  || write(i, (char *) &rc, 4) != 4
			  || write(i, buf, rc) != rc)
			{
			    cl_addr [i] = 0;
				close(i);
			}
		  }
	      }
	      
	      /* should we go on ? */
	      for (go_on = 0, i = 0; i < FD_SETSIZE; i++) {
		  go_on += cl_addr [i] > 0;
	      }

	  } else if (FD_ISSET(serv_s, &fds)) {
	      /* accept a new client: */
	      memset((char *) &daddr, 0, sizeof(daddr));
	      dlen = sizeof(daddr);
	      
	      rc = accept(serv_s, (struct sockaddr *) &daddr, &dlen);
	      if (rc < 0) {
		  perror("straps: accept failed");
		  continue;
	      }
	      cl_addr [rc] = 1;

	  } else {
	      /* fd's connected from clients. (XXX: should check for EOF): */
	      for (i = 0; i < FD_SETSIZE; i++) {
		  if (cl_addr [i] > 0 && FD_ISSET(i, &fds)) {
		      cl_addr [i] = 0;
		      close(i);
		  }
	      }
	      
	      /* should we go on ? */
	      for (go_on = 0, i = 0; i < FD_SETSIZE; i++) {
		  go_on += cl_addr [i] > 0;
	      }
	  }
	  
      } /* end for (;;) */

    unlink(path);

    return 0;
}
