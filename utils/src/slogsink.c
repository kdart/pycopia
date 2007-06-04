/*
 * slogsink.c --
 *
 * This code is adapted from straps.c program from Technical University of Braunschweig.
 *
 * A simple syslog sink.  The slogsink demon listens to the syslog port 514/udp
 * and forwards the received event to connected clients (like scotty). Because
 * the port 514 needs root access and the port can be opened only once, the use
 * of a simple forwarding demon is a good choice.
 *
 * The client can connect to the AF_UNIX domain stream socket /tmp/.slog-<port>
 * and will get the trap-packets in raw binary form:
 *
 *	4 bytes ip-address (in network-byte-order) of the sender 
 *	2 bytes port-number (in network-byte-order) of the sender 
 *	4 bytes data-length (in host-byte-order) followed by the n 
 *	data-bytes of the packet.
 *
 * This code was originally an SNMP trap forwarder, which is:
 * Copyright (c) 1994-1996 Technical University of Braunschweig.
 *
 * It was modified by Keith Dart <kdart@cosinecom.com> to work with syslog in a
 * similiar fashion.
 *
 * See the file "license.terms" for information on usage and redistribution of
 * this file, and for a DISCLAIMER OF ALL WARRANTIES.
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

#define SYSLOG_PORT	514
#define SYSLOG_NAME	"syslog"
#define UNIX_SOCKET	"/tmp/.slog"

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
    int recv_s, serv_s, slen, dlen, llen, rc, i;
    fd_set fds;
    static int cl_addr [FD_SETSIZE];
    char buf[2048], path[1024];
    int go_on;
    char *name;
    int port;
    
    /* 
     * Check the number of arguments. We accept an optional argument
     * which specifies the port number we are listening on.
     */

    if (argc > 2) {
	fprintf(stderr, "usage:  slogsink [port]\n");
	exit(1);
    }

    if (argc == 2) {
	name = argv[1];
	port = atoi(argv[1]);
    } else {
	name = SYSLOG_NAME;
	port = SYSLOG_PORT;
    }
    
    /*
     * Get the port that we are going to listen to. Check that
     * we do not try to open a priviledged port number, with
     * the exception of the syslog port.
     */

    if ((se = getservbyname(name, "udp"))) {
	port = ntohs(se->s_port);
    }

    if (port != SYSLOG_PORT && port < 1024) {
	fprintf(stderr, "slogsink: access to port %d denied\n", port);
	exit(1);
    }

    /*
     * Close any "leftover" FDs from the parent.  
     */

    for (i = 3; i < FD_SETSIZE; i++) {
	(void) close(i);
    }

    /*
     * Open and bind the normal trap socket:
     */

    if ((recv_s = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
	perror("slogsink: unable to open syslog socket");
	exit(1);
    }
    
    taddr.sin_family = AF_INET;
    taddr.sin_port = htons(port);
    taddr.sin_addr.s_addr = INADDR_ANY;

    if (bind(recv_s, (struct sockaddr *) &taddr, sizeof(taddr)) < 0) {
	perror("slogsink: unable to bind syslog socket");
	exit(1);
    }


    /*
     * Open the client socket. First unlink the name and set the umask
     * to 0. This should not make any problems and it makes security
     * people happy. (Suggested by David Keeney <keeney@zk3.dec.com>)
     */

    sprintf(path, "%s-%d", UNIX_SOCKET, port);
    unlink(path);
    umask(0);

    if ((serv_s = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
	perror("slogsink: unable to open server socket");
	exit(1);
    }

    memset((char *) &saddr, 0, sizeof(saddr));
    
    saddr.sun_family = AF_UNIX;
    strcpy(saddr.sun_path, path);
    slen = sizeof(saddr) - sizeof(saddr.sun_path) + strlen(saddr.sun_path);

    if (bind(serv_s, (struct sockaddr *) &saddr, slen) < 0) {
	perror("slogsink: unable to bind server socket");
	exit(1);
    }
    
    if (listen(serv_s, 5) < 0) {
	perror("slogsink: unable to listen on server socket");
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
	  FD_SET(recv_s, &fds);
	  FD_SET(serv_s, &fds);

	  /* fd's connected from clients. listen for EOF's: */
	  for (i = 0; i < FD_SETSIZE; i++) {
	      if (cl_addr [i] > 0) FD_SET(i, &fds);
	  }

	  rc = select(FD_SETSIZE, &fds, (fd_set *) 0, (fd_set *) 0, 
		       (struct timeval *) 0);
	  if (rc < 0) {
	      if (errno == EINTR || errno == EAGAIN) continue;
	      perror("slogsink: select failed");
	  }
	  
	  if (FD_ISSET(recv_s, &fds)) {
	      /* read syslog message and forward to clients: */
	      llen = sizeof(laddr);
	      if ((rc = recvfrom(recv_s, buf, sizeof(buf), 0, 
				 (struct sockaddr *) &laddr, &llen)) < 0) {
		  perror("slogsink: recvfrom failed");
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
		  perror("slogsink: accept failed");
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
