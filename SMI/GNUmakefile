# $Id: GNUmakefile,v 1.1 2005/07/25 21:25:18 kdart Exp $

all: build

libsmi_wrap.c: libsmi.i
	swig -no_default -python libsmi.i

build: libsmi_wrap.c
	python setup.py build

install: libsmi_wrap.c
	python setup.py install

clean:
	rm -rf build/

distclean: clean
	rm -f libsmi.py libsmi.pyc
	rm -f *_wrap.*
