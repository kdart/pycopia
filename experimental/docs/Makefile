all:	Manual.html

Manual.html:	Manual.htm
	htmlpp Manual.htm

html:
	@(cd $(PYNMS_HOME)/docs/html ; pydoc -w $(PYNMS_HOME)/lib)

