#!/usr/bin/python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# ASCII text classified into named sets.

lowercase = 'abcdefghijklmnopqrstuvwxyz'
uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
hexdigits = '0123456789ABCDEF'
letters = lowercase + uppercase
alphanumeric = lowercase + uppercase + digits
whitespace = ' \t\n\r\v\f'
punctuation = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
printable = digits + letters + punctuation + whitespace
control = "".join(map(chr, range(32))) + chr(127)
ascii = control + " " + digits + letters + punctuation

CR   = "\r"
LF   = "\n"
CRLF   = CR + LF
ESCAPE = chr(27)
DEL = chr(127)
