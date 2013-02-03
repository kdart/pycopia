# make file for wrapper only

all: build

libsmi_wrap.c: libsmi.i
	swig -nodefaultctor -nodefaultdtor -python -modern -py3 -fastunpack libsmi.i

build: libsmi_wrap.c
	python setup.py build

install: libsmi_wrap.c
	python setup.py install

clean:
	rm -rf build/

distclean: clean
	rm -f libsmi.py libsmi.pyc
	rm -f *_wrap.*
