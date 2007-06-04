# $Id: GNUmakefile,v 1.1.1.1 2002/07/10 00:57:38 kdart Exp $

# You must have the Smartbits smartlib library already installed on your system
# in order for this to compile.

BININSTALLDIR=$(PYNMS_HOME)/lib/
PYINSTALLDIR=$(PYNMS_HOME)/lib/smartbits/

TARGETS=smartbits_funccmodule.so # smartbits_structcmodule.so
PYTARGETS=smartbits_func.py # smartbits_struct.py

all:	$(TARGETS)

Makefile: Setup.in Makefile.pre.in
	make -f Makefile.pre.in boot

smartbits_func_wrap.c: smartbits_func.i
	swig -python smartbits_func.i

smartbits_struct_wrap.c: smartbits_struct.i
	swig -python -shadow -opt smartbits_struct.i
#	perl fix_wrapper.pl smartbits_struct_wrap.c

$(TARGETS): Makefile smartbits_func_wrap.c # smartbits_struct_wrap.c
	make -f Makefile

install: $(TARGETS)
	mkdir -p $(BININSTALLDIR)
	cp -f $(TARGETS) $(BININSTALLDIR)
	mkdir -p $(PYINSTALLDIR)
	cp -f $(PYTARGETS) $(PYINSTALLDIR)


clean:
	rm -f *.o *.pyc *.bak $(TARGETS)
	rm -f $(PYTARGETS)
	rm -f smartbits_func_wrap.c smartbits_struct_wrap.c

distclean: clean
	rm -f Makefile Makefile.pre sedscript config.c Setup
