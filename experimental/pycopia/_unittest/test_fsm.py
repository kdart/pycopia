#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Unit test the fsm module.

"""

# $Id$


import qatest
from fsm import FSM, ANY


###################################################################
# The following is a test of the FSM
#
# This is not a real XML validator. It ignores character sets,
# entity and character references, and attributes.
# But it does check the tree structure and
# can tell if the XML input is generally well formed or not.
####################################################################
XML_TEST_DATA = '''<?xml version="1.0"?>
<graph>
  <att name="directed" value="1" />
  <att name="mode" value="FA" />
  <att name="start" value="q0" />
    <node id="0" label="q0">
      <graphics x="-172.0" y="13.0" z="0.0" />
    </node>
    <node id="1" label="q1">
      <graphics type="hexagon"  x="10.0" y="74.0" z="-0.0"/>
    </node>
    <node id="2" label="q2" accept="1">
      <graphics x="169.0" y="-5.0" z="-0.0" />
    </node>
    <node id="3" label="q3" >
      <graphics x="19.0" y="8.0" z="-0.0" />
    </node>
    <node id="4" label="q4">
      <graphics  x="18.0" y="-74.0" z="-0.0" />
    </node>
    <edge source="0" target="1" label="ab"/>
    <edge source="1" target="2" label="aa"/>
    <edge source="2" target="2" label="c"/>
    <edge source="0" target="3" label="ba"/>
    <edge source="3" target="2" label="aa"/>
    <edge source="0" target="4" label="a"/>
    <edge source="4" target="2" label="c" />
    <edge source="2" target="4" label="ab" />
</graph>
'''
def Error (input_symbol, fsm):
    print 'UNDEFINED: %s -- RESETTING' % (input_symbol,)
    fsm.reset()
def StartBuildTag (input_symbol, fsm):
    fsm.push (input_symbol)
def BuildTag (input_symbol, fsm):
    s = fsm.pop ()
    s = s + input_symbol
    fsm.push (s)
def DoneBuildTag (input_symbol, fsm):
    pass
def DoneEmptyElement (input_symbol, fsm):
    s = fsm.pop()
    print s
def StartBuildEndTag (input_symbol, fsm):
    fsm.push (input_symbol)
def BuildEndTag (input_symbol, fsm):
    s = fsm.pop ()
    s = s + input_symbol
    fsm.push (s)
def DoneBuildEndTag (input_symbol, fsm):
    s1 = fsm.pop ()
    s2 = fsm.pop ()
    if s1 == s2:
        print s1
    else:
        print 'Not valid XML.'

def test():
    f = FSM('INIT')
    f.add_default_transition (Error, 'INIT')
    f.add_transition ('<', 'INIT', None, 'TAG')
    f.add_transition (ANY, 'INIT', None, 'INIT') # Ignore white space between tags

    f.add_transition ('?', 'TAG', None, 'XML_DECLARATION')
    f.add_transition (ANY, 'XML_DECLARATION', None, 'XML_DECLARATION')
    f.add_transition ('?', 'XML_DECLARATION', None, 'XML_DECLARATION_END')
    f.add_transition ('>', 'XML_DECLARATION_END', None, 'INIT')

    # Handle building tags
    f.add_transition (ANY, 'TAG', StartBuildTag, 'BUILD_TAG')
    f.add_transition (ANY, 'BUILD_TAG', BuildTag, 'BUILD_TAG')
    f.add_transition (' ', 'BUILD_TAG', None, 'ELEMENT_PARAMETERS')
    f.add_transition ('/', 'TAG', None, 'END_TAG')
    f.add_transition ('/', 'BUILD_TAG', None, 'EMPTY_ELEMENT')
    f.add_transition ('>', 'BUILD_TAG', DoneBuildTag, 'INIT')

    # Handle element parameters
    f.add_transition ('>', 'ELEMENT_PARAMETERS', DoneBuildTag, 'INIT')
    f.add_transition ('/', 'ELEMENT_PARAMETERS', None, 'EMPTY_ELEMENT')
    f.add_transition ('"', 'ELEMENT_PARAMETERS', None, 'DOUBLE_QUOTE')
    f.add_transition (ANY, 'ELEMENT_PARAMETERS', None, 'ELEMENT_PARAMETERS')

    # Handle quoting inside of parameter lists
    f.add_transition (ANY, 'DOUBLE_QUOTE', None, 'DOUBLE_QUOTE')
    f.add_transition ('"', 'DOUBLE_QUOTE', None, 'ELEMENT_PARAMETERS')

    # Handle empty element tags
    f.add_transition ('>', 'EMPTY_ELEMENT', DoneEmptyElement, 'INIT')

    # Handle end tags
    f.add_transition (ANY, 'END_TAG', StartBuildEndTag, 'BUILD_END_TAG')
    f.add_transition (ANY, 'BUILD_END_TAG', BuildEndTag, 'BUILD_END_TAG')
    f.add_transition ('>', 'BUILD_END_TAG', DoneBuildEndTag, 'INIT')

    f.process_string (XML_TEST_DATA)
    
    return len(f.stack)

class FSMTest(qatest.Test):
    def test_method(self):
        rv = test()
        if rv == 0:
            return self.passed("tested XML parser appears valid")
        else:
            return self.failed("tested XML failed")


class FSMSuite(qatest.TestSuite):
    pass

def get_suite(cf):
    suite = FSMSuite(cf)
    suite.add_test(FSMTest)
    return suite

def run(cf):
    suite = get_suite(cf)
    suite()

