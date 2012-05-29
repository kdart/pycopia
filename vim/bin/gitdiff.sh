#!/bin/sh

# shell wrapper to enable vimdiff and meld as the subversion diff.

# set up your ~/.gitconfig like this to use it:

#[diff]
#	external = gitdiff.sh
#
#[pager]
#	diff =
#	ndiff = less
#
#[alias]
#	ndiff = diff --no-ext-diff

# The ndiff alias is the "normal diff" in case you don't want to use vimdiff some times.

DIFF="/usr/bin/vimdiff -R"

LEFT=${2}
RIGHT=${5}

exec $DIFF $LEFT $RIGHT
