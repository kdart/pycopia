"""
================
pycopia_testcase
================

Sphinx extension that handles docstrings in the Pycopia TestCase standard format

"""

#import os
#import inspect

import textwrap

#from docutils import nodes
from sphinx.util.docstrings import prepare_docstring

def mangle_docstrings(app, what, name, obj, options, lines, reference_offset):
    if what == 'module':
        pass

#def initialize(app):
#    app.connect('autodoc-process-signature', mangle_signature)

def setup(app):

    app.add_directive('testmodule', TestModuleDirective)
    app.add_directive('testcase', TestCaseDirective)

def purge_todos(app, env, docname):
    if not hasattr(env, 'todo_all_todos'):
        return
    env.todo_all_todos = [todo for todo in env.todo_all_todos if todo['docname'] != docname]

    textwrap.dedent(obj.__doc__)
#    app.connect('builder-inited', initialize)
#    app.connect('autodoc-process-docstring', mangle_docstrings)


