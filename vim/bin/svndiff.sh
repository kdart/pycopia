#!/bin/sh

# shell wrapper to enable vimdiff and meld as the subversion diff.

if [ -z "$DISPLAY" ] ; then
	DIFF="/usr/bin/vimdiff"
else
        DIFF="/usr/bin/meld"
fi

LEFT=${6}
RIGHT=${7}

exec $DIFF $LEFT $RIGHT
