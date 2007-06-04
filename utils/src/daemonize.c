/*
 * 'daemonize' can "daemonize" any program.
 * Usage:
 *     daemonize [-f logfile] [-a] [-v] <program>
 * Where:
 * 	-f specifies a log file that stdout and stderr will be directed to.
 * 	-v be more verbose
 * 	-a append to log file rather than truncate it.
 * 	<program> is the program to run detached from controlling terminal.
 * Keith Dart <kdart@cosinecom.com>
 */

#include <stdio.h>
#include <fcntl.h>

main(ac, av)
int ac;
char **av;
{
	int pid;
	char *file;
	int vflag, fflag;
	int mode;

	if (ac < 2) { 
		printf("Usage: %s [-f logfile] [-a] [-v] <program>\n", av[0]);
		exit(1);
	}
	close(0); open("/dev/null", 0);
	close(1);

	file = "daemonize.out";
	mode = O_TRUNC;
	vflag = 0;
	fflag = 0;

	while(**++av == '-') {
		while(*++*av) {
			switch(**av) {
				case 'f':
					fflag = 1;
					if(*++*av)
						file = *av;
					else
						file = *++av;
					goto next_arg;
				case 'v':
					vflag++;
					break;
				case 'a':
					mode = O_APPEND;
					break;
			}
		}
next_arg:	;
	}

	if (fflag) {
			if(open(file, O_WRONLY|mode|O_CREAT, 0666) < 0) {
				perror(file);
				exit(1);
			}
	} 
	else {
			if(open("/dev/null", O_WRONLY) < 0) {
				perror("/dev/null");
				exit(1);
			}
	}


	switch(pid = fork()) {
		case -1:
			perror(av[0]);
			exit(1);
			break;
		case 0:
			if(vflag) {
				char **p = av;

				printf("# %d", getpid());
				while(*p)
					printf(" %s", *p++);
				putchar('\n');
			}
			fflush(stdout);
			close(2); dup(1);
			setpgrp();
			setsid();
			execv(av[0], av);
			execvp(av[0], av);
			perror(av[0]);
			_exit(1);
			break;
		default:
			if(vflag) {
				fprintf(stderr, "# %d", pid);
				while(*av)
					fprintf(stderr, " %s", *av++);
				fputc('\n', stderr);
			}
			exit(0);
			break;
	}
}
