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
Some canned graphs using biggles.

"""

import sys


import proctools

# Currently, this is a proof of concept.

def makeplot(args):
    import sys
    import biggles
    from biggles.libplot import renderer
    #import math, Numeric
    x = range(10)
    y = range(10)
    g = biggles.FramedPlot()
    pts = biggles.Points( x, y)
    g.add( pts )
    # render to response
    device = renderer.ImageRenderer( "PNG", 640, 480, sys.stdout)
    g.page_compose(device)
    device.delete()



def testplot(request):
    """This is a web framework handler."""
    from WWW.framework import HttpResponse
    args = (1,)
    proc = proctools.coprocess(makeplot, args)
    out = proc.read()
    proc.wait()
    # render to response
    return HttpResponse(out, mimetype="image/png")




