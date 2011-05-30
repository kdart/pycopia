# Makefile to make builds and installation more familiar for some.

PYTHON = python2
SUBPACKAGES_DEV = aid utils core CLI debugger process SMI SNMP storage net audio XML WWW QA vim

.PHONY: build install rpms install_data develop develophome pytags

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  install       to install from this workspace."
	@echo "  build         to just build the packages."
	@echo "  install_data  to install only data files, such as html, css, and javascript."
	@echo "  rpms          to build RPMs on systems that can build RPMs"
	@echo "  develop       to set up global develop mode (imports from this workspace)."
	@echo "  develophome   to set up private devlop mode (in $HOME/.local)."
	@echo "  squash        to squash (flatten) all named sub-packages into single tree."
	@echo "  pytags        to make ctags of python source files."

build:
	$(PYTHON) setup.py build

install: build
	$(PYTHON) setup.py install

rpms:
	$(PYTHON) setup.py rpms

install_data:
	$(PYTHON) setup.py install_data core process storage XML WWW QA 

develop:
	$(PYTHON) setup.py develop

develophome:
	$(PYTHON) setup.py develophome

squash:
	$(PYTHON) setup.py squash

pytags:
	find $(SUBPACKAGES_DEV) -name "*.py" \! -path "*/build/*" \! -path  "*/dtds/*"| ctags -L -

