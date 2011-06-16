#!/usr/bin/python2
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2010 Keith Dart <keith@dartworks.biz>
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
Simple HTML5 top-level boilerplate generator.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


# Currenty using this subset of HTML5 features shared by both FF 3.6.x and Chrome 10
BROWSER_FEATURES = ['applicationcache', 'backgroundsize', 'borderimage', 'borderradius',
        'boxshadow', 'canvas', 'canvastext', 'csscolumns', 'cssgradients',
        'csstransforms', 'draganddrop', 'flexbox', 'fontface', 'geolocation',
        'hashchange', 'hsla', 'js', 'localstorage', 'multiplebgs', 'opacity',
        'postmessage', 'rgba', 'sessionstorage', 'svg', 'svgclippaths', 'textshadow',
        'webworkers']

NO_BROWSER_FEATURES = ['no-audio', 'no-cssanimations', 'no-cssreflections',
        'no-csstransforms3d', 'no-csstransitions', 'no-history', 'no-indexeddb',
        'no-inlinesvg', 'no-smil', 'no-touch', 'no-video', 'no-webgl', 'no-websockets',
        'no-websqldatabase']

FEATURE_CLASS = " ".join(BROWSER_FEATURES) + " " + " ".join(NO_BROWSER_FEATURES)



#### simple templates for use by mostly client-side apps.
SIMPLE_TEMPLATE = """<?xml version="1.0" encoding="{charset}"?>
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" class="{features}">
  <head>
    <meta charset="{charset}" /> 
    <meta name="robots" content="noindex" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>{title}</title>
    <link href="/media/css/{appname}.css" type="text/css" rel="stylesheet" />
    <!-- <script src="/media/js/modernizr-1.7.min.js" type="text/javascript"></script> -->
    <script src="/media/js/packed.js" type="text/javascript"></script>
    <script src="/media/js/{appname}.js" type="text/javascript"></script>
  </head>
  <body>
  {body}
  </body>
</html>
"""

def new_simple_document(appname, title, charset="utf-8", body=""):
    return SIMPLE_TEMPLATE.format(
        charset=charset,
        features=FEATURE_CLASS,
        appname=appname,
        title=title,
        body=body,
        )


if __name__ == "__main__":
    docs = new_simple_document("myapp", "MyApp", "utf-8")
    print (docs)


