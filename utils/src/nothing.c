/* does nothing except return exit code.
 */

#include <stdlib.h>

main(int argc, char *argv[])
{
	int arg;

	if (argc > 1) 
		arg = (int) strtol(argv[1], NULL, 10);
	else 
		arg = 0;

	return (arg);

}


