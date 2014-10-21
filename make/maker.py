#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Almar Klein
# Distributed under the (new) BSD License. 

# Originally developed under the Vispy project.

"""
Convenience tools for developers

    python make command [arg]

"""

from __future__ import division, print_function

import sys
import os
from os import path as op
import time
import webbrowser


# Save where we came frome and where this module lives
START_DIR = op.abspath(os.getcwd())
THIS_DIR = op.abspath(op.dirname(__file__))

# Get root directory of the package, by looking for setup.py
for subdir in ['.', '..']:
    ROOT_DIR = op.abspath(op.join(THIS_DIR, subdir))
    if op.isfile(op.join(ROOT_DIR, 'setup.py')):
        break
else:
    sys.exit('Cannot find root dir')


# Define directories and repos of interest
DOC_DIR = op.join(ROOT_DIR, 'doc')
#
WEBSITE_DIR = op.join(ROOT_DIR, '_website')
WEBSITE_REPO = 'git@github.com:imageio/imageio'
#
PAGES_DIR = op.join(ROOT_DIR, '_gh-pages')
PAGES_REPO = 'git@github.com:imageio/imageio.github.io.git'


class Maker:
    """ Collection of make commands.

    To create a new command, create a method with a short name, give it
    a docstring, and make it do something useful :)

    """

    def __init__(self, argv):
        """ Parse command line arguments. """
        # Get function to call
        if len(argv) == 1:
            func, arg = self.help, ''
        else:
            command = argv[1].strip()
            arg = ' '.join(argv[2:]).strip()
            func = getattr(self, command, None)
        # Call it if we can
        if func is not None:
            func(arg)
        else:
            sys.exit('Invalid command: "%s"' % command)

    def coverage_html(self, arg):
        """Generate html report from .coverage and launch"""
        print('Generating HTML...')
        from coverage import coverage
        cov = coverage(auto_data=False, branch=True, data_suffix=None,
                       source=['imageio'])  # should match testing/_coverage.py
        cov.load()
        cov.html_report()
        print('Done, launching browser.')
        fname = op.join(os.getcwd(), 'htmlcov', 'index.html')
        if not op.isfile(fname):
            raise IOError('Generated file not found: %s' % fname)
        webbrowser.open_new_tab(fname)
    
    def help(self, arg):
        """ Show help message. Use 'help X' to get more help on command X. """
        if arg:
            command = arg
            func = getattr(self, command, None)
            if func is not None:
                doc = getattr(self, command).__doc__.strip()
                print('make %s [arg]\n\n        %s' % (command, doc))
                print()
            else:
                sys.exit('Cannot show help on unknown command: "%s"' % command)

        else:
            print(__doc__.strip() + '\n\nCommands:\n')
            for command in sorted(dir(self)):
                if command.startswith('_'):
                    continue
                preamble = command.ljust(11)  # longest command is 9 or 10
                # doc = getattr(self, command).__doc__.splitlines()[0].strip()
                doc = getattr(self, command).__doc__.strip()
                print(' %s  %s' % (preamble, doc))
            print()
    
    def clean(self, arg):
        """ Clean the repo of .pyc files and __pycache__ directories.
        """
        # Remove files
        for dir, dirnames, filenames in os.walk(ROOT_DIR):
            if dir.startswith('.'):
                continue
            for fname in filenames:
                if fname.endswith('.pyc'):
                    filename = os.path.join(dir, fname)
                    fname_r = os.path.relpath(filename, ROOT_DIR)
                    try:
                        os.remove(filename)
                        print('Removed %r' % fname_r)
                    except Exception as err:
                        print('Could not remove %r: %s' % (fname_r, str(err)))
        # Remove directories
        for dir, dirnames, filenames in os.walk(ROOT_DIR):
            if dir.startswith('.'):
                continue
            for dname in dirnames:
                if dname == '__pycache__':
                    dirname = os.path.join(dir, dname)
                    dname_r = os.path.relpath(dirname, ROOT_DIR)
                    try:
                        os.rmdir(dirname)
                        print('Removed dir %r' % dname_r)
                    except Exception as err:
                        print('Could not remove %r: %s' % (dname_r, str(err)))
        
    def test(self, arg):
        """ Run tests:
                * unit - run unit tests
                * style - flake style testing (PEP8 and more)
        """
        if not arg:
            return self.help('test')
        from imageio import testing
        if arg in ('flake', 'style'):
            try:
                testing.test_style()
            except RuntimeError as err:
                sys.exit(str(err))
        elif arg == 'unit':
            testing.test_unit()
        else:
            raise RuntimeError('Invalid arg for make test: %r' % arg)
    
    def copyright(self, arg):
        """ Update all copyright notices to the current year.
        """
        # Initialize
        TEMPLATE = "# Copyright (c) %i, Imageio Development Team."
        CURYEAR = int(time.strftime('%Y'))
        OLDTEXT = TEMPLATE % (CURYEAR - 1)
        NEWTEXT = TEMPLATE % CURYEAR
        # Initialize counts
        count_ok, count_replaced = 0, 0

        # Processing the whole root directory
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            # Check if we should skip this directory
            reldirpath = op.relpath(dirpath, ROOT_DIR)
            if reldirpath[0] in '._' or reldirpath.endswith('__pycache__'):
                continue
            if op.split(reldirpath)[0] in ('build', 'dist'):
                continue
            # Process files
            for fname in filenames:
                if not fname.endswith('.py'):
                    continue
                # Open and check
                filename = op.join(dirpath, fname)
                text = open(filename, 'rt').read()
                if NEWTEXT in text:
                    count_ok += 1
                elif OLDTEXT in text:
                    text = text.replace(OLDTEXT, NEWTEXT)
                    open(filename, 'wt').write(text)
                    print(
                        '  Update copyright year in %s/%s' %
                        (reldirpath, fname))
                    count_replaced += 1
                elif 'copyright' in text[:200].lower():
                    print(
                        '  Unknown copyright mentioned in %s/%s' %
                        (reldirpath, fname))
        # Report
        print('Replaced %i copyright statements' % count_replaced)
        print('Found %i copyright statements up to date' % count_ok)
