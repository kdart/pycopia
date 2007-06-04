/*
 * pyntping.c:						Jan 2000
 * based on:
 * ntping.c:						Jan 1993
 * (schoenfr@gaertner.de)				Sep 1997
 *
 * Copyright (c) 1993-1997 by Erik Schoenfelder and Juergen Schoenwaelder 
 * TU Braunschweig, Germany, Institute for Operating Systems 
 * and Computer Networks.
 *
 * This is ping/traceroute for scotty; it allows processing 
 * parallel probes.
 * Modified for Python by Keith Dart <kdart@cosinecom.com>, mostly so I don't have to
 * parse the curly brace output. ;-)
 */

#define PROGNAME	"pyntping"		/* my name */

static char *version = "pyntping  1.0  Jan 2000";

#ifdef HAVE_CONFIG_H
# include <config.h>
#endif

#include <stdio.h>
#ifdef HAVE_STDLIB_H
# include <stdlib.h>
#endif
#include <signal.h>
#include <string.h>
# include <sys/time.h>
# include <sys/types.h>
# ifdef HAVE_SYS_SELECT_H
#  include <sys/select.h>
# endif
#include <errno.h>
#if defined(pyr) || (defined(MACH) && defined (MTXINU))
/* should make into the configure script... */
extern int errno;
#endif
#ifdef HAVE_UNISTD_H
# include <unistd.h>
#endif
#ifdef HAVE_MALLOC_H
# include <malloc.h>
#endif
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#ifdef HAVE__RES
# include <arpa/nameser.h>
# include <resolv.h>
#endif
#ifdef DB_MALLOC
# include <dbmalloc.h>
#endif

#ifdef __alpha
/* 
 * thanks to <mosedale@genome.stanford.edu> Dan Mosedale for the DEC
 * Alpha patches and <grunwald@foobar.cs.colorado.edu> Dirk Grunwald 
 * for his help.
 */
typedef unsigned int ipaddr_t;
#else /* ! __alpha */
typedef unsigned long ipaddr_t;
#endif /* ! __alpha */
typedef unsigned int int32;


/* aix failes to use IP_TTL correct: */
#ifndef _AIX
# if defined(IP_TTL) && ! defined(USE_DLPI)
/*
 * with USE_DLPI we will not send our own handmade ip (udp) packets.
 * instead we open a ordinariy udp socket and set the ttl via
 * setsockopt with IP_TTL. 
 * This is at least needed for HP-UX and SVR4-boxes.
 */
#  define USE_DLPI
# endif /* IP_TTL && ! USE_DLPI */
#endif /* ! _AIX */


/*
 * provide header due to other naming of fields or unavailibility: 
 */
# ifdef WORDS_BIGENDIAN
#  define FIRST_IP_BYTE  u_char  ip_v:4, ip_hl:4 
# else
#  define FIRST_IP_BYTE  u_char  ip_hl:4, ip_v:4 
# endif

/*
 * this is for linux around 0.99.15 and above:
 * (seems to be helpful for windows too...)
 */
struct ip { FIRST_IP_BYTE; u_char ip_tos; short ip_len; 
	    u_short ip_id; short ip_off; u_char ip_ttl; u_char ip_p; 
	    u_short ip_sum; struct in_addr ip_src,ip_dst;
};
struct icmp { u_char  icmp_type; u_char icmp_code; u_short icmp_cksum;
	      u_short icmp_id, icmp_seq; char icmp_data [1];
};
struct udphdr { u_short uh_sport, uh_dport; short uh_ulen; u_short uh_sum; };

# define ICMP_MINLEN     	8
# define ICMP_ECHO       	8
# define ICMP_ECHOREPLY       	0
# define ICMP_UNREACH    	3
# define ICMP_SOURCEQUENCH	4
# define ICMP_TIMXCEED   	11
# define ICMP_TSTAMP		13
# define ICMP_TSTAMPREPLY	14
# define ICMP_MASKREQ    	17
# define ICMP_MASKREPLY  	18
# define ICMP_UNREACH_PORT	3
# define ICMP_TIMXCEED_INTRANS	0


/* #include <linux/wait.h> */
#include <netdb.h>

/* some simple macros: */
#define mis_dig(c)  ((c) >= '0' && (c) <= '9')
/* time differences (time is handled in millisecons) */
#define timediff2(t1,t2)  (((t2).tv_sec - (t1).tv_sec) * 1000 \
	+ ((t2).tv_usec - (t1).tv_usec) / 1000)
#define time_diff(t1,t2)  (timediff2(t1,t2) <= 0 ? 1 : timediff2(t1,t2))
/* fetch gettimofday: */
#define gettime(tv,dofail)	\
	if (gettimeofday (tv, (struct timezone *) 0) < 0)	\
	  { dperror ("pyntping: gettimeofday failed; reason"); dofail; }
/* simple debug help: */

#define dprintf		if (do_debug) fprintf
#define dperror		if (do_debug) perror


#define printf0		printf
#define printf1		printf
#define printf2		printf

/*
 * things we may do: 
 */
enum job_type { unknown, ping, trace, mask, tstamp };

/* length of the data space of a ping packet: */
#define DEFAULT_DATALEN		44

/* max data size we are sending (seems to work on most systems): */
#define MAX_DATALEN		2020

/* default base port for ttl probes: */
#define BASE_PORT		50000
#define MAX_BASE_PORT		60000

/* default number of retries (means 5 probes are sent): */
#define DEFAULT_RETRIES		4

/* timeout in s before giving up (overall timeout): */
#define DEFAULT_TIMEOUT		5

/* ident counter for the ping packets: */
static unsigned short icmp_ident;

/* emit debug messages: */
static int do_debug = 0;

/* number of retries: */
static int retries = DEFAULT_RETRIES;

/* default waittime before giving up: */
static int timeout = DEFAULT_TIMEOUT;

/* time in ms to wait between retries: */
static int wait_time = (1000 * DEFAULT_TIMEOUT) / (DEFAULT_RETRIES + 1);

/* the sockets: */
static int icsock = -1;				/* icmp */
static int ipsock = -1;				/* ip/udp */

#ifdef USE_DLPI
/* port # our udp-socket is bound to: */
static unsigned short src_port;

/* second ip-socket (for switched byte-sex problems): */
static int ipsock2 = -1;
#endif

/* datalen of the ping-pkt: */
static int data_len = DEFAULT_DATALEN;

/* milli-seconds to sleep if we have sent a packet: */
static int delay_time = 0;			/* default: don't sleep */

/* base port for ttl probes: */
static int base_port = BASE_PORT;

/* read hostnames from stdin: */
static int interactive = 0;

/* run in scotty (formerly bones) mode: */
static int scotty = 0;

/* reply the string given for the trace-target, if target reached: */
static int reply_same = 0;

/* sigh - check for bytesex in unreach/exceed icmp's too. 
   some synoptics are dumb enough to reply wrong packets: */
static int check_sex = 1;

/* what we should do: */
static enum job_type type_todo;

/* in the case of a trace, the hop-count: */
static int ttl_opt;

/*
 * the use of these fileds is somewhat confusing. some are used for
 * ping's others for ttl-probes. this needs surely a clean-up.
 */
typedef struct _a_job {
    enum job_type type;			/* ping, ttl or ... ? */
    int done;				/* this job is done (error flag) */
    int job_no;				/* sequence number */
    int probe_cnt;			/* # of probes sent */
    char *hname;			/* hostname */
    struct sockaddr_in sa;		/* hosts ip-address */
    unsigned short id;			/* unique icmp id */
    union {
	struct {
	    int ttl;			/* hops for traceroute */
	    int tdone;			/* was it the final hop ? */
	    unsigned short port;	/* dest port for traceroute */
	    struct sockaddr_in hop;	/* hop's ip-address */
	    struct timeval tv;		/* time ttl probe sent. */
	    int tim;			/* time of result in ms */
	} trace;
	ipaddr_t mask;			/* mask return val */
	long tstamp;			/* time stamp return val */
	int ping_tim;			/* time in ms */
    } u;
    struct _a_job *next;		/* next togo or done */
} a_job;

/* jobs to go: */
static a_job *job_list = 0;

/*
 * udp ttl packet:
 */
typedef struct _a_pkt {
#ifndef USE_DLPI
    /* 
     * we are sending simple udp packets; no additional headers are
     * needed.
     */
    struct ip ip;
    struct udphdr udph;
#endif
    /* arg: no additional bytes are replied by icmp - this is nonsense. */
    char seq;
    char ttl;
    struct timeval tv;
    char buf [1];
} a_pkt;


/* forward: */
static void receive_pkt ();


/*
 * save-malloc: aborts on error.
 */
#define TALLOC(T)	((T *) xmalloc (sizeof (T)))
#define xstrdup(s)	strcpy (xmalloc (strlen (s) + 1), s)
#define xfree(s)	free ((char *) s)

#ifdef DB_MALLOC
# define xmalloc	malloc
# define xrealloc	realloc
#else /* ! DB_MALLOC */
static char *
xmalloc (n)
int n;
{
    char *nnew;
    int i;
    
    for (i = 0; ! (nnew = (char *) malloc ((unsigned) n)) && i < 10; i++) {
	sleep (6);
    }
    if (! nnew) {
	fprintf (stderr, "pyntping: out of mem... aborting.\n");
	exit (1);
    }
    return nnew;
}

static char *
xrealloc (p, n)
char *p;
int n;
{
    char *nnew;
    int i;
    
    for (i = 0; ! (nnew = (char *) realloc (p, (unsigned) n)) && i < 10;
	 i++) {
        sleep (6);
    }
    if (! nnew) {
	fprintf (stderr, "pyntping: out of mem... aborting.\n");
	exit (1);
    }
    return nnew;
}
#endif /* ! DB_MALLOC */


/* 
 * make a.b.c.d string; returns static buffer space.
 */

static char *
fmt_addr (addr)
ipaddr_t addr;
{
	static char buf [80];
	sprintf (buf, "%d.%d.%d.%d", (int) (addr >> 24) & 0xff, 
		 (int) (addr >> 16) & 0xff, (int) (addr >> 8) & 0xff, 
		 (int) addr & 0xff);
	return buf;
}


/* swap a short: */
static int sexy (x)
unsigned x;
{
	return ((x & 0xff) << 8) | ((x & 0xff00) >> 8);
}


#ifndef _oldport

/*
 * return next useable port for a trace destination;
 * avoid use of port, which is byte swapped is use.
 */

static unsigned short
next_port ()
{  
    a_job *j;
    int rego;

    /* set to nect hopefully free port: */
    base_port++;
    if (base_port > MAX_BASE_PORT) {
      base_port = BASE_PORT;
    }
    
    /* 
     * no check, if this port is ok, or in use, or bad:
     * XXX: this looks like an expensive loop; check via profiler...
     */

    do {

      rego = 0;

      for (j = job_list; j; j = j->next) {
	
	if (j->type == trace) {
	  
	  if (j->u.trace.port == base_port ||
	      j->u.trace.port == sexy (base_port)) {

	    dprintf (stderr,
		     "** looking for next port -- clash: 0x%x vs. 0x%x\n",
		     j->u.trace.port, base_port);

	    base_port++;
	    if (base_port > MAX_BASE_PORT) {
	      base_port = BASE_PORT;
	    }

	    rego = 1;

	  }
	}
      }
    } while (rego);

    return base_port;
}
#endif


/*
 * return 0 if no more jobs are waiting, or 1 else.
 */

static int
jobs_to_go ()
{
    a_job *j;

    for (j = job_list; j; j = j->next)
      if (! j->done)
	return 1;
    return 0;
}


/*
 * fetch and process incoming pkts; if we are not done, spend at least
 * wtim milliseconds. if flag is set, ignore the fact, that all jobs
 * are done.
 */

static void
do_receive_pending (wtim, flag)
int wtim;
int flag;
{
    fd_set fds;
    struct timeval tv, time_mark, now;
    long tdiff;
    int rc;

    /* we should not wait longer than time_mark + wtim: */
    if (wtim > 0)
      gettime(&time_mark, /* ignore */ );
    
    do {
	/* don't spend time, if we are done: */
	if (wtim > 0 && ! jobs_to_go () && ! flag)
	  return;
	
	/* wait for a ready icmp socket, or timeout: */
	do {
	    FD_ZERO (&fds);
	    FD_SET (icsock, &fds);

	    if (wtim > 0)
	      tv.tv_usec = (wtim * 1000) % 1000000,
	      tv.tv_sec = (wtim * 1000) / 1000000;
	    else
	      tv.tv_sec = tv.tv_usec = 0;

	    rc = select (icsock + 1, &fds, (fd_set *) 0, (fd_set *) 0, &tv);
	    
	    if (rc < 0 && errno != EINTR && errno != EAGAIN)
	      {
		  perror ("pyntping: select failed; reason");
		  exit (1);
	      }
	} while (rc < 0);
	
	/* if timeout we are done: */
	if (! rc)
	  return;

	/* icmp socket is ready: */
	receive_pkt ();
	
	/* at least poll, until the queue is empty: */
	if (wtim <= 0)
	  {
	      wtim = 0;
	      continue;
	  }

	/* recalculate the remaining waittime we have to spend: */
	gettime(&now, return);
	tdiff = time_diff(time_mark, now);
	dprintf (stderr, "** timediff to spend: %ld\n", tdiff);
	/* time to leave ? */
	if (tdiff > wtim)
	  return;
	
	time_mark = now;
	wtim -= tdiff;

    } while (wtim >= 0);
}


/*
 * search for a specific job.
 * the id is either the src-port of our own udp-packet (== job->id) or
 * for the dlpi udp-packet the static src_port.
 */

static a_job *
find_job_port (ip, udph)
struct ip *ip;
struct udphdr *udph;
{
    unsigned short id = ntohs (udph->uh_sport);
    unsigned short port = ntohs (udph->uh_dport);
    a_job *job;
    
    dprintf (stderr, "* looking for src %u (0x%lx)  dest %u (0x%lx) ...", 
	       (unsigned) id, (int) id, (unsigned) port, (int) port);

    for (job = job_list; job; job = job->next)
      {
	  unsigned short src;
	  int got_it = 0;

#ifndef USE_DLPI
	  src = job->id;
#else
	  src = src_port;
#endif

#ifndef USE_DLPI
	  dprintf (stderr, " %u", src);
#else
	  dprintf (stderr, "  %u (0x%lx)", (unsigned) job->u.trace.port, 
		     (int) job->u.trace.port);
#endif
	  
	  if (job->u.trace.port == port && src == id)
	    got_it = 1;
	  
	  if (! got_it && check_sex)
	    {
		if ((job->u.trace.port == sexy (port) && src == sexy (id))
		    || (job->u.trace.port == port && src == sexy (id))
		    || (job->u.trace.port == sexy (port) && src == id))
		  {
		      got_it = 1;
		      dprintf (stderr,
"pyntping: warning: got icmp-reply from 0x%08lx with byte-swapped port in the reply\n", 
			       ntohl (ip->ip_src.s_addr));
		  }
	    }
	  
	  if (got_it)
	    {
		dprintf (stderr, " got it.\n");
		return job;
	    }
      }

    dprintf (stderr, " nope...\n");

    return (a_job *) 0;
}


static a_job *
find_job_id (id)
unsigned short id;
{
	a_job *job;

	dprintf (stderr, "* looking for job id %u ...", (unsigned) id);

	for (job = job_list; job; job = job->next)
	{
	    dprintf (stderr, " %u", (unsigned) job->id);
	    if (job->id == id)
	      {
		  dprintf (stderr, " got it.\n");
		  return job;
	      }
	}

	dprintf (stderr, " nope...\n");
	return (a_job *) 0;
}


/*
 * fill in sockaddr_in from given hname (decimal or name);
 * return 0 on error.
 */

static int
make_addr (addr, hname)
struct sockaddr_in *addr;
char *hname;
{
    memset ((char *) addr, 0, sizeof (struct sockaddr_in));
    if (*hname >= '0' && *hname  <= '9')
      {
	  int a, b, c, d;
	  ipaddr_t naddr;
	  
	  if (4 == sscanf (hname, "%d.%d.%d.%d", &a, &b, &c, &d))
	    {
		naddr = (a << 24) | (b << 16) | (c << 8) | d;
		naddr = ntohl (naddr);
		/** XXX hack alert - but what the heck ;-) **/
		addr->sin_family = AF_INET;
		addr->sin_addr.s_addr = naddr;
		return 1;
	    }
      }
    else {
	char tmp [512];
	struct hostent *hp;
	strcpy (tmp, hname);
#ifdef HAVE__RES
	/* try to spend no longer than some seconds: */
	_res.retrans = 1, _res.retry = 3;
#endif
	if ((hp = gethostbyname (tmp)))
	  {
	      addr->sin_family = hp->h_addrtype;
	      memcpy ((char *) &(addr->sin_addr), (char *) hp->h_addr,
		      hp->h_length);
	      return 1;
	  }
    }
    
    dprintf (stderr, "pyntping: cannot resolve `%s'\n", hname);
    
    return 0;
}



/*
 * beeeep - an icmp packet arrived; fetch and process:
 */

static void
receive_pkt ()
{
    char packet [MAX_DATALEN + 128];
    int len = sizeof (packet);
    struct ip *ip = (struct ip *) packet;
    struct icmp *icp;			/* for pings */
    struct udphdr *udph;		/* for ttl's */
    struct timeval tp1, tp2;
    struct sockaddr_in sfrom;
    int fromlen = sizeof (sfrom);
    int hlen = 0, cc, ttl_is_done = 0;
    enum job_type type = unknown;
    a_job *job = 0;

    cc = recvfrom (icsock, (char *) packet, len, 0,
		   (struct sockaddr *) &sfrom, &fromlen);
    
    if (cc < 0 && errno != EINTR && errno != EAGAIN)
      {
	  dperror ("pyntping: warning: recvfrom");
	  return;
      }

    gettime(&tp2, return);
    
    dprintf (stderr, "... recv got: rc %d\n", cc);

    /*
     * raw-socket with icmp-protocol (send and) receive
     * ip packets with complete header:
     */
    hlen = ip->ip_hl << 2;
    
    if (cc < hlen + ICMP_MINLEN)
      {
	  dprintf (stderr, "... short packet - ignored\n");
	  return;
      }
    
    icp = (struct icmp *) (packet + hlen);
    udph = (struct udphdr *) (icp->icmp_data + sizeof (struct ip));
    
    dprintf (stderr,
	     "... got icmp type %d  code %d  id %u (0x%x)\n", 
	     icp->icmp_type, icp->icmp_code,
	     (unsigned) icp->icmp_id,
	     (unsigned) icp->icmp_id);
    
    switch (icp->icmp_type) {
      case ICMP_ECHOREPLY:
	type = ping;
	break;
      case ICMP_MASKREPLY:
	type = mask;
	break;
      case ICMP_TSTAMPREPLY:
	type = tstamp;
	break;
      case ICMP_UNREACH:
	if (icp->icmp_code != ICMP_UNREACH_PORT)
	  {
	      dprintf (stderr, "* bad icmp code - discarded.\n");
	      return;
	  }
	type = trace;
	ttl_is_done = 1;
	break;
      case ICMP_TIMXCEED:
	if (icp->icmp_code != ICMP_TIMXCEED_INTRANS)
	  {
	      dprintf (stderr, "* bad icmp code - discarded.\n");
	      return;
	  }
	type = trace;
	break;
      default:
	dprintf (stderr, "* unknown icmp type discarded.\n");
	return;
    }
    
    if ((type != trace && ! (job = find_job_id (icp->icmp_id)))
	|| (type == trace && ! (job = find_job_port (ip, udph))))
      {
	  dprintf (stderr, "* unknown packet id discarded.\n");
	  return;
      }
    
    /* this one is still done: */
    if (job->done)
      {
	  dprintf (stderr, "* still done :-)\n");
	  return;
      }

    dprintf (stderr, "* .. got host %s .. ", job->hname);
    
    switch (type) 
      {
	case ping:
	  tp1 = job->u.trace.tv;		/* time sent */
	  memcpy ((char *) &tp1, (char *) icp->icmp_data,
		  sizeof (struct timeval)); 
	  job->u.ping_tim = time_diff(tp1, tp2);
	  dprintf (stderr, "ping with tim %d\n", job->u.ping_tim);
	  break;
	case mask:
	  job->u.mask = ntohl (* (ipaddr_t *) icp->icmp_data);
	  dprintf (stderr, "mask with val 0x%lx\n", (long) job->u.mask);
	  break;
	case tstamp:
	  job->u.tstamp = ntohl (((int32 *) icp->icmp_data) [1]) -
			  ntohl (((int32 *) icp->icmp_data) [0]);
	  dprintf (stderr, "* tstamp with diff %ld\n", (long) job->u.tstamp);
	  break;
	case trace:
	  tp1 = job->u.trace.tv;		/* time sent */
	  job->u.trace.tim = time_diff(tp1, tp2);
	  job->u.trace.hop = sfrom;
	  job->u.trace.tdone = ttl_is_done;
	  dprintf (stderr, "ttl hop is %s (0x%lx) and final_flag %d\n", 
		   fmt_addr (ntohl(sfrom.sin_addr.s_addr)),
		   (long) sfrom.sin_addr.s_addr, ttl_is_done);
	  break;
	default:
	  dprintf (stderr, "* unknown type - ignored ... \n");
	  return;
      }

    /* fine: */
    job->done = 1;
}


/* 
 * make checksum:
 */

static int 
in_cksum (buf, n)
unsigned short *buf;
int n;
{
	int sum = 0, nleft = n;
	unsigned short ret, *ptr = buf, odd_byte = 0;

	while (nleft > 1)
		sum += *ptr++, nleft -= 2;

	if (nleft == 1)
		*(unsigned char *) (&odd_byte) = *(unsigned char *) ptr,
		sum += odd_byte;

	sum = (sum >> 16) + (sum & 0xffff);
	sum += (sum >> 16);
	ret = ~sum;

	return ret;
}


/*
 * send a ttl probe pkt:
 */

static void
send_ttl (job)
a_job *job;
{
    char *datap, outpack [2048];
    a_pkt *pkt = (a_pkt *) outpack;
#ifndef USE_DLPI
    struct ip *ip = &pkt->ip;
    struct udphdr *udph = &pkt->udph;
#endif /* ! USE_DLPI */
    struct sockaddr_in *sto = &job->sa;
    int i, j;
	
    if (job->done)
      return;

#ifndef USE_DLPI
    ip->ip_hl = sizeof (struct ip) / sizeof (int32);
    ip->ip_v = 4;			/* take this - live and in color */
    ip->ip_tos = 0;
    ip->ip_id = job->id;		/* ??? */
    ip->ip_sum = 0;
    /* fixed by Jan L. Peterson (jlp@math.byu.edu): */
    ip->ip_src.s_addr = 0;		/* jlp */
    
    ip->ip_off = 0;
    ip->ip_p = IPPROTO_UDP;
    ip->ip_len = data_len;
    ip->ip_ttl = job->u.trace.ttl;
    ip->ip_dst = sto->sin_addr;	       /* needed for linux (no bind) */
    
    udph->uh_sport = htons (job->id);
#if 1
    /* job->port is set to (base_port + ttl) - same pkt for retries: */
    udph->uh_dport = htons (job->u.trace.port);
#else
    udph->uh_dport = htons (job->port + job->cur_seq); /* karl +job_no */
#endif
    udph->uh_ulen = htons ((u_short) (data_len - sizeof (struct ip)));
    udph->uh_sum = 0;
    
#else /* USE_DLPI */
    sto->sin_port = htons (job->u.trace.port);
#endif /* USE_DLPI */
    
    pkt->seq = job->probe_cnt++;
    pkt->ttl = job->u.trace.ttl;	
    /* set and save time: */
    gettime(&pkt->tv, return);
    job->u.trace.tv = pkt->tv;
    
    datap = pkt->buf;
    for (i = sizeof (struct timeval) + 2, j = 'A'; i < data_len; i++, j++)
      datap [i] = j;

    /*
     * may be simply: #ifdef IP_TTL  (eventually wrapped around a USE_DLPI) ?
     */
#ifdef USE_DLPI
    { int opt_ttl = job->u.trace.ttl;
      int opt_ttl_len = sizeof (opt_ttl);
      
      if (setsockopt(ipsock, IPPROTO_IP, IP_TTL, 
		     (char *) &opt_ttl, opt_ttl_len) < 0)
	  perror ("pyntping: setsockopt: cannot set ttl; reason");
      
      if (getsockopt(ipsock, IPPROTO_IP, IP_TTL,
		     (char *) &opt_ttl, &opt_ttl_len) < 0)
	  perror ("pyntping: getsockopt: ttl not set; reason");
      else if (job->u.trace.ttl != opt_ttl)
	  fprintf (stderr, "pyntping: dlpi: cannot set ttl - ouch...\n");
    }
#endif
    /* fprintf(stderr, "data_len %d\n", data_len); */	/* karl */

  resend:
    i = sendto (ipsock, (char *) outpack, data_len, 0, 
		(struct sockaddr *) sto, sizeof (struct sockaddr_in));
	
    /* at least linux has the irritating behavior, to return an
       error on the next sento call, if the previous one got an
       port unreable, with returning conn. refused. 
       so we will work around... */

#ifndef ECONNREFUSED
/* Windows sucks: */
# define ECONNREFUSED 0xdeadbeef
#endif
    
    if (i < 0 && errno == ECONNREFUSED)
      {
	  dperror ("** sendto failed; reason");
	  dprintf (stderr, "** retrying sento ...\n");
	  goto resend;
      }
    
    if (i < 0 || i != (data_len))  
      dperror ("pyntping: sendto");
    else
      dprintf (stderr, "* ttl %d sent to %s  port %u (0x%x)...\n",
	       job->u.trace.ttl, job->hname, (unsigned) job->u.trace.port,
	       (unsigned) job->u.trace.port);
}




/*
 * guess the pingtime: */

static void
send_icmp (job)
a_job *job;
{
    char outpack [MAX_DATALEN + 128];
    struct icmp *icp = (struct icmp *) outpack;
    char *datap = icp->icmp_data;
    int i, data_offset;
    struct sockaddr_in *sto = &job->sa;
    struct timeval tv;
    
    if (job->done)
      return;
    
    icp->icmp_type = type_todo == mask ? ICMP_MASKREQ : 
	      (type_todo == tstamp ? ICMP_TSTAMP : ICMP_ECHO);
    icp->icmp_code = 0;
    icp->icmp_cksum = 0;
    icp->icmp_seq = job->probe_cnt++;
    icp->icmp_id = job->id;
    
    if (type_todo != mask)
      gettime(&tv, return);
	
    if (type_todo == tstamp)
      {
	  * (int32 *) datap = htonl ((tv.tv_sec % 86400) * 1000
				     + (tv.tv_usec / 1000));
	  data_offset = sizeof (int32);
      }
    else if (type_todo == mask)
      data_offset = 0;
    else 
      {    /* ping: */
	  * (struct timeval *) datap = tv;
	  data_offset = sizeof (struct timeval);
      }
    
    for (i = data_offset; i < data_len; i++)
      datap [i] = i;
	
    /* icmp checksum: */
    icp->icmp_cksum = in_cksum ((unsigned short *) icp, data_len);

    i = sendto (icsock, (char *) outpack, data_len, 0, 
		(struct sockaddr *) sto, sizeof (struct sockaddr_in));

    /* without debug, simply ignore any error: */
    if (i < 0 || i != data_len)  
      dperror ("pyntping: sendto");
    else
      dprintf (stderr, "* %s ping %d sent to %s...\n",
	       type_todo == mask ? "mask" : 
	       (type_todo == tstamp ? "tstamp" : "regular"),
	       job->probe_cnt - 1, job->hname);
}


static void
send_pending ()
{
    a_job *job;
    
    /* cleanup: */
    do_receive_pending (0, 0);
    
    for (job = job_list; job; job = job->next)
      {
	  if (! job->done && job->probe_cnt <= retries + 1)
	    {
		if (job->type == trace)
		  send_ttl (job);
		else /* ping, mask, tstamp */
		  send_icmp (job);
		
		/* fetch avail answers, spending at least
		   delay_time milliseconds: */
		do_receive_pending (delay_time, 0);
	    }
      }
}


/*
 * parse options, the options are same as cmd-line options:
 * return a ptr to the remaining string:
 */

static char *
scan_options (buf)
char *buf;
{
    int n;

#define skip_white(s)		while (*s == ' ' || *s == '\t') s++;
#define skip_non_white(s)	while (*s && *s != ' ' && *s != '\t') s++;

    /* default is a ping: */
    type_todo = ping;

    skip_white (buf);
    while (*buf == '-')
      {
	  if (1 == sscanf (buf, "-ttl %d", &n)
	      || 1 == sscanf (buf, "-trace %d", &n))
	    {
		type_todo = trace;
		reply_same = ! strncmp (buf, "-trace", 6);
		
		if (n <= 0)
		  {
		      dprintf (stderr, "* bad ttl %d\n", n);
		  }
		else {
		    dprintf (stderr, "* ttl = %d\n", n);
		    ttl_opt = n;
		}
		skip_non_white (buf);
		skip_white (buf);
		skip_non_white (buf);
	    }
	  else if (! strncmp (buf, "-mask", strlen ("-mask"))
		   || ! strncmp (buf, "-m", strlen ("-m")))
	    {
		type_todo = mask;
		skip_non_white (buf);
	    }
	  else if (! strncmp (buf, "-timestamp", strlen ("-timestamp"))
		   || ! strncmp (buf, "-tstamp", strlen ("-tstamp")))
	    {
		type_todo = tstamp;
		skip_non_white (buf);
	    }
	  else if (1 == sscanf (buf, "-size %d", &n)
		   || 1 == sscanf (buf, "-s %d", &n))
	    {
		if (n < DEFAULT_DATALEN || n > MAX_DATALEN)
		  {
		      dprintf (stderr, "* bad size %d\n", n);
		      if (n < DEFAULT_DATALEN)
			n = DEFAULT_DATALEN;
		      else if (n > MAX_DATALEN)
			n = MAX_DATALEN;
		  }
		dprintf (stderr, "* size = %d\n", n);
		data_len = n;
		
		skip_non_white (buf);
		skip_white (buf);
		skip_non_white (buf);
	    }
	  else if (1 == sscanf (buf, "-delay %d", &n)
		   || 1 == sscanf (buf, "-d %d", &n))
	    {
		if (n < 0)
		  {
		      dprintf (stderr, "* bad delay %d\n", n);
		      delay_time = 0;
		  }
		else {
		    dprintf (stderr, "* delay = %d\n", n);
		    delay_time = n;
		}
		skip_non_white (buf);
		skip_white (buf);
		skip_non_white (buf);
	    }
	  else if (1 == sscanf (buf, "-retries %d", &n)
		   || 1 == sscanf (buf, "-r %d", &n))
	    {
		if (n < 0)
		  {
		      dprintf (stderr, "* bad retr %d\n", n);
		      retries = 0;
		  }
		else {
		    dprintf (stderr, "* retr = %d\n", n);
		    retries = n;
		}
		wait_time = (1000 * timeout) / (retries + 1);
		skip_non_white (buf);
		skip_white (buf);
		skip_non_white (buf);
	    }
	  else if (1 == sscanf (buf, "-timeout %d", &n)
		   || 1 == sscanf (buf, "-t %d", &n))
	    {
		if (n <= 0)
		  {
		      dprintf (stderr, "* bad timo %d\n", n);
		      timeout = 1;
		  }
		else {
		    dprintf (stderr, "* timo = %d\n", n);
		    timeout = n;
		}
		wait_time = (1000 * timeout) / (retries + 1);
		skip_non_white (buf);
		skip_white (buf);
		skip_non_white (buf);
	    }
	  else if (! strncmp (buf, "-same", strlen ("-same")))
	    {
		reply_same = 1;
		skip_non_white (buf);
	    }
	  else if (! strncmp (buf, "-nocheckswap", strlen ("-nocheckswap")))
	    {
		check_sex = 0;
		skip_non_white (buf);
	    }
	  else if (! strncmp (buf, "-checkswap", strlen ("-checkswap")))
	    {
		check_sex = 1;
		skip_non_white (buf);
	    }
	  else {
	      fprintf (stderr, "pyntping: bad option in `%s'\n", buf);
	      break;
	  }
	  skip_white (buf);
      }
    
    return buf;
}


/*
 * print one result:
 */

static void
print_one_result (job)
a_job *job;
{
    switch (job->type) 
      {
	case ping:
	  if (scotty) {
	      printf2 ("('%s', %d), ", job->hname, job->done == 1 
		       ? job->u.ping_tim : -1);
	  } else if (job->done == 1) {
	      printf2 ("%s %5d ms  ", job->hname, job->u.ping_tim);
	  } else {
	      printf2 ("%s %5s  ", job->hname, "* ");
	  }
	  break;
	case mask:
	  if (scotty) {
	      printf2 ("('%s', '%s'), ", job->hname, job->done == 1 ?
		       fmt_addr (job->u.mask) : "0.0.0.0");
	  } else if (job->done == 1) {
	      printf2 ("%s %s  ", job->hname, fmt_addr (job->u.mask));
	  } else {
	      printf2 ("%s %5s  ", job->hname, "* ");
	  }
	  break;
	case tstamp:
	  /* on error write an empty list-element for python: */
	  if (scotty && job->done == 1) {
	      printf2 ("('%s', %ld), ", job->hname, job->u.tstamp);
	  } else if (scotty && job->done != 1) {
	      printf1 ("('%s', -1), ", job->hname);
	  } else if (job->done == 1) {
	      printf2 ("%s %5ld ms  ", job->hname, job->u.tstamp);
	  } else {
	      printf2 ("%s %5s  ", job->hname, "* ");
	  }
	  break;
	case trace:
	  if (scotty) {
	      printf2 ("('%s', %d), ", job->u.trace.tdone && reply_same
		       && mis_dig (job->hname[0]) ? job->hname : 
		       fmt_addr (ntohl(job->u.trace.hop.sin_addr.s_addr)),
		       job->done == 1 ? job->u.trace.tim : -1);
	  } else if (job->done == 1) {
	      printf2 ("%s %5d ms  ", job->u.trace.tdone && reply_same 
		       && mis_dig (job->hname[0]) ? job->hname : 
		       fmt_addr (ntohl(job->u.trace.hop.sin_addr.s_addr)), 
		       job->u.trace.tim);
	  } else {
	      printf2 ("%s %5s  ", job->u.trace.tdone && reply_same
		       && mis_dig (job->hname[0]) ? job->hname : 
		       fmt_addr (ntohl(job->u.trace.hop.sin_addr.s_addr)), 
		       "* ");
	  }
	  break;
	default:
	  printf0 ("(), ");
	  fprintf (stderr, "oops - unknown type (tell schoenfr@ibr.cs.tu-bs.de)\n");
	  break;
      }
}


/*
 * if all jobs are done, print the results and discard all jobs.
 */

static void
print_result ()
{
    int i;

    for (i = 0; job_list; i++)
      {
	  a_job *j, **job;

	  /* jump to job #i: */
	  for (job = &job_list; *job && (*job)->job_no != i; 
	       job = &(*job)->next);
	  
	  if (! (j = *job))
	    {
		fprintf (stderr, "pyntping: internal error - tell schoenfr@ibr.cs.tu-bs.de\n");
		exit (1);
	    }

	  print_one_result (j);
	  
	  dprintf (stderr, "* job `%d' no %d  %s discarded\n", j->id, 
		   j->job_no, j->hname);

	  /* remove this job: */
	  *job = (*job)->next;
	  if (j->hname) 
	    xfree (j->hname);
	  xfree (j);
      }
    
    printf ("\n");
    fflush (stdout);
}


/*
 * create a new job (or jobs) and make an job entry.
 * return 1 on success, 0 on failure.
 */

static int
make_job (hname)
char *hname;
{			
    a_job *job = TALLOC (a_job);
    int rc = 1, len;

    /*
     * remove leading/trailing whites:
     */
    while (*hname == ' ')
      hname++;
    while ((len = strlen (hname)) > 0
	   && (hname [len - 1] == '\n' || hname [len - 1] == ' '))
      hname [len - 1] = '\0';
	
    dprintf (stderr, "* examining `%s'\n", hname);
	
    if (type_todo == trace)
      dprintf (stderr, "* got ttl order: %d `%s'\n", ttl_opt, hname);
	
    job->done = 0;
    job->probe_cnt = 0;

    if (! make_addr (&job->sa, hname))
      rc = 0;					/* mark for termination */

    job->type = type_todo;
    job->hname = xstrdup (hname);
    job->id = icmp_ident++;

    if (type_todo == trace) 
      {
	  job->u.trace.tim = -1;
	  job->u.trace.ttl = ttl_opt;
	  job->u.trace.tdone = 0;
	  job->u.trace.hop.sin_addr.s_addr = 0;		/* clear */
#ifdef _oldport
	  job->u.trace.port = base_port + ttl_opt;
#else
	  job->u.trace.port = next_port ();
#endif

#ifdef _oldport
	  /* give some space to the next one: */
	  base_port += 30;
	  if (base_port > MAX_BASE_PORT)
	    base_port = BASE_PORT;
#endif
      }

    dprintf (stderr, "* made job: `%s'  tag %d\n", hname, type_todo);

    job->next = job_list;
    job_list = job;

    return rc;
}


/*
 * split this line into a bones job-list:
 */

static void
make_jobs (buf)
char *buf;
{
    char *ptr = buf, *sep = " \t\r\n\f{}";
    int i;
    
    ptr = strtok (buf, sep);
    
    for (i = 0; ptr && *ptr; i++)
      {
	  /* make_job() queues to head of job_list: */
	  if (! make_job (ptr))
	    job_list->done = 2, job_list->probe_cnt = retries + 1;
	  job_list->job_no = i;
	  
	  ptr = strtok ((char *) 0, sep);
      }
}


/*
 * split the command into jobs and do the processing:
 */

static void
work_for_one_cmd (cmd)
char *cmd;
{
    char *ptr = cmd;
    int i;
    
    dprintf (stderr, "* do_one_job ``%s''\n", cmd);
	  
    make_jobs (ptr);

    for (i = 0; jobs_to_go () && i < retries + 1; i++)
      {
	  struct timeval tv_start, tv_now;
	  gettime(&tv_start, /* ignore */ );

	  dprintf (stderr, "** sendloop %d\n", i);
	  send_pending ();

	  /* in case we are not done, wait the remaining time 
	     for the next try: */
	  if (jobs_to_go ())
	    {
		int tdiff;
		gettime(&tv_now, continue);
		dprintf (stderr, "** timediff: %d > %d\n", wait_time,
			 time_diff(tv_start, tv_now));
		if (wait_time > (tdiff = time_diff(tv_start, tv_now)))
		  do_receive_pending (wait_time - tdiff, 0);
	    }
      }

    print_result ();

    dprintf (stderr, "* done.\n");
}
    
/*
 * here we are entering the interactive part. read a list of
 * names from stdin and process as a chunk.
 */

static void
do_interactive ()
{
    static char *line = 0;
    static int line_len;
    int len_inc = 2, read_len;
    char *ptr;

    dprintf (stderr, "* do_interactive...\n");
    interactive = 1;

    if (! line)
      line = xmalloc (line_len = len_inc);

    for (;;) 
      {
	  char *rc;

	  ptr = line;
	  read_len = line_len;
	  
	  while (ptr == (rc = fgets (ptr, read_len, stdin)))
	    {
		int len = strlen (line);
		if (len > 0)
		  {
		      if (line [len - 1] != '\n')
			{
			    line = xrealloc (line, line_len += len_inc);
			    ptr = line + strlen (line);
			    read_len = len_inc;
			}
		      else
			{
			    line [len - 1] = 0;
			    break;
			}
		  }
	    }
	
	  /* end of file ? */
	  if (! rc)
	    break;
  
	  dprintf (stderr, "got '%s'\n", line);		/* karl */
	  
	  ptr = scan_options (line);
	  work_for_one_cmd (ptr);
      }
    
    dprintf (stderr, "* done.\n");
}


/*
 * commandline order -- aye aye: loop endless for ping, ... but do a
 * traceroute for ttl's: 
 */

static void
do_cmdline (cmd)
char *cmd;
{
    int i, n = 0;

    /* when tracerouting via commandline, tell more: */
    if (type_todo == trace)
      {
	  printf ("traceroute result:\n");
	  n = ttl_opt;
      }
    
    for (i = 1; i <= n || type_todo != trace; i++)
      {
	  char *ptr = xstrdup (cmd);
	  struct timeval tvs, tve;
	  if (type_todo != trace)	  
	    { gettime(&tvs, exit(1)); }
	  else
	    ttl_opt = i;
	  /* print counter: */
	  printf ("%3d: ", i);
	  work_for_one_cmd (ptr);
	  xfree (ptr);
	  if (type_todo != trace)
	    {
		gettime(&tve, exit(1));
		/* spend at least timeout secs, if we loop: */
		do_receive_pending (timeout * 1000 - time_diff(tvs, tve), 1);
	    }
      }
}

/*
 * get an icmp socket and an ip_raw socket:
 */

static int
init_socks ()
{
    struct protoent *proto;
    int icmp_proto = 1;			/* Capt'n Default */
    struct sockaddr_in maddr;
#ifndef linux
#ifdef IP_HDRINCL
    int on = 1;				/* karl */
#endif
#endif
#ifdef USE_DLPI
    struct sockaddr_in tmp_addr;
    int ta_len = sizeof (tmp_addr);
#endif
    int max_data_len;
    
    /*
     * sanity: don't tell about cannot open the socket, if no root
     * permissions are avail. check uid by hand.
     */
    if (geteuid ())
      {
	  fprintf (stderr,
 "pyntping: warning: running with euid %d -- not with root permissions.\n",
		   geteuid ());
	  fprintf (stderr,
 "pyntping: warning: expect missing permissions getting the icmp socket.\n");
      }

    if ((proto = getprotobyname ("icmp")) == NULL) 
      { /* perror ("pyntping: icmp protocol unknown; reason"); */ }
    else
      icmp_proto = proto->p_proto;
    
    if ((icsock = socket (AF_INET, SOCK_RAW, icmp_proto)) == -1) 
      {
	  perror ("pyntping: cannot get icmp socket; reason");
	  return 0;
      }
#ifdef USE_DLPI
    /*
     * My mom told me: if it hurts don't do it ...
     * but this looks quite useable.
     */
    if ((ipsock = socket (AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) 
      {
	  perror ("pyntping: cannot get udp socket; reason");
	  return 0;
      }
#else /* ! USE_DLPI */
    if ((ipsock = socket (AF_INET, SOCK_RAW, IPPROTO_RAW)) < 0) 
      {
	  perror ("pyntping: cannot get raw ip socket; reason");
	  return 0;
      }
#endif /* ! USE_DLPI */
    /*
     * SO_SNDBUF and IP_HDRINCL fix from karl@sugar.NeoSoft.COM:
     * seems to be neccesary for 386bsd and others.
     */
#if defined(SO_SNDBUF)
    /* we can have varying sizes (at least in interactive mode): */
    max_data_len = MAX_DATALEN + sizeof (struct ip);
    if (setsockopt(ipsock, SOL_SOCKET, SO_SNDBUF, (char *) &max_data_len,
		   sizeof(max_data_len)) < 0) {
	perror("pyntping: SO_SNDBUF");
	exit(1);
    }
#endif /* SO_SNDBUF */
    
#if !defined(nec_ews) && !defined(linux) && !defined(USE_DLPI)
#ifdef IP_HDRINCL
    if (setsockopt(ipsock, IPPROTO_IP, IP_HDRINCL, (char *) &on,
		   sizeof(on)) < 0) {
	perror("pyntping: warning: IP_HDRINCL");
	fprintf (stderr, "pyntping: trying to continue - please tell");
	fprintf (stderr, "schoenfr@gaertner.de about this warning\n");
    }
#endif /* IP_HDRINCL */
#endif /* ! nec_ews && ! linux && ! USE_DLPI */
    
    memset ((char *) &maddr, 0, sizeof (maddr));
    maddr.sin_family = AF_INET;
    maddr.sin_addr.s_addr = INADDR_ANY;
    maddr.sin_port = 0;
#if defined(linux) && ! defined(USE_DLPI)
    /* linux pukes on bind, but seems to do the tracing stuff.
     * try it on your own risk.... */
#else
    if (bind (ipsock, (struct sockaddr *) &maddr, sizeof (maddr)) < 0)
      {
	  perror ("pyntping: cannot bind socket; reason");
	  return 0;
      }
#endif
    
#ifdef USE_DLPI
    /*
     * we cannot send a datagramm with a src-port of our own 
     * choice - too bad.
     * therefore we connot identfify the icmp-port-unreachable 
     * with our homebrewed id. save the original port and check about:
     */
    
    if (getsockname (ipsock, (struct sockaddr *) &tmp_addr, &ta_len) < 0)
      {
	  perror ("pyntping: cannot get sockname; reason");
	  return 0;
      }
    src_port = ntohs (tmp_addr.sin_port);
    dprintf (stderr, "* dlpi: my port is %d (0x%lx)\n", (int) src_port,
	     (int) src_port);
    
    /*
     * let's try to work around a funny bug: open the complement
     * port, to allow reception of icmp-answers with byte-swapped
     * src-port field.  if we cannot get this port, silently
     * ignore and continue normal.
     */
    
    if ((ipsock2 = socket (AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) 
      {
	  dperror ("* cannot get udp socket #2; reason");
	  ipsock2 = -1;
      }
    else 
      {
	  struct sockaddr_in maddr2;
	  
	  memset ((char *) &maddr2, 0, sizeof (maddr2));
	  maddr2.sin_family = AF_INET;
	  maddr2.sin_addr.s_addr = INADDR_ANY;
	  maddr2.sin_port = htons (sexy (src_port));
	  
	  if (bind (ipsock2, (struct sockaddr *) &maddr2, 
		    sizeof (maddr2)) < 0)
	    {
		dperror ("* cannot bind socket #2; reason");
		ipsock2 = -1;
	    }
      }
    
    if (ipsock2 != -1)
      dprintf (stderr, "* got the second port # %d (0x%lx)\n", sexy (src_port),
	       sexy (src_port));
    
#endif /* USE_DLPI */
    
    /* everything is fine: */
    return 1;
}


/*
 * what we are willing to manage ?
 */

static void
usage ()
{
    fprintf (stderr, "\nUse : pyntping [<options>] [<hosts>] ");
    fprintf (stderr, "\noptions are:\n");
    fprintf (stderr, "\t-V              show version and exit.\n");
    /*	fprintf (stderr, "\t-D              give verbose debug output.\n"); */
    fprintf (stderr, "\t-b(ones)        run in `scotty' mode.\n");
    fprintf (stderr, 
	  "options which may be specified on stdin or the cmdline:\n");
    fprintf (stderr, "\t-s(ize) <n>     set size of packets.\n");
    fprintf (stderr, "\t-r(etries) <n>  set # of retries.\n");
    fprintf (stderr, "\t-t(imeout) <n>  set timeout for an answer.\n");
    fprintf (stderr, "\t-d(elay) <n>    set the send delay to <n> ms.\n");
    fprintf (stderr, 
	  "\t-ttl <n>        trace a hop with time-to-live set to n.\n");
    fprintf (stderr, 
	  "\t-trace <n>      same as -ttl, but the destination is returned\n");
    fprintf (stderr, 
	  "\t                for the last hop, if it is a dotted number.\n");
    fprintf (stderr, "\t-mask           send an icmp-mask request.\n");
    fprintf (stderr, "\t-tstamp         send a icmp-timestamp request.\n");
    fprintf (stderr, "\n");
    
    exit (1);
}


/*
 * scan options; copy unown and remaing to commandbuffer; 
 * commandbuffer is returned, or 0.
 */

static char *
examine_arguments (argc, argv)
int argc;
char *argv[];
{
    char *cmd = 0;
    int cmdbuflen = 0, cmdlen = 0;

    /*
     * parse the given options and override the default, if given;
     */
    
    while (++argv, --argc > 0)
      {
	  if (! strcmp ("-help", *argv) || ! strcmp ("-h", *argv))
	    usage ();
	  else if (! strcmp ("-D", *argv))
	    do_debug = 1;
	  else if (! strcmp ("-V", *argv) || ! strcmp ("-v", *argv))
	    {
		fprintf (stderr, "Version:  %s\n", version);
		exit (0);
	    }
	  else if (! strcmp ("-bones", *argv) || ! strcmp ("-b", *argv)
		   || ! strcmp ("-scotty", *argv))
	    scotty = 1;
	  else 
	    { /* any other arg is copied and scanned later: */
		int len = strlen (*argv);
		if (! cmdbuflen)
		  cmd = xmalloc (cmdbuflen = len + 5);
		else if (len + cmdlen >= cmdbuflen)
		  cmd = xrealloc (cmd, cmdbuflen = cmdlen + len + 5);
		sprintf (cmd + cmdlen, "%s%s", cmdlen ? " " : "", *argv);
		cmdlen += len + (cmdlen > 0);
	    }
      }
    
    dprintf (stderr, "* remaning cmdline: ``%s''\n", cmd ? cmd : "none");
    
    return cmd;
}


/*
 * 	M A I N :
 */

int
main (argc, argv)
int argc;
char *argv[];
{
    char *cmd;

    /* we will need the id urgently... */
    icmp_ident = (getpid () & 0xff) << 8;
    
    /* now have a look: aye aye sir! */
    cmd = examine_arguments (argc, argv);

    /* scan valid commandline options: */
    if (cmd)
      cmd = scan_options (cmd);
    
    /* fetch and initialize the icmp and the ip sockets: */
    if (! init_socks ())
      return 1;

    /* back to normal rights: */
    setuid (getuid ());

    if (cmd)
      /* work for the command line: */
      do_cmdline (cmd);
    else
      /* nope ? process from stdin: */
      do_interactive ();

    return 0;
}

/* end of pyntping.c */
