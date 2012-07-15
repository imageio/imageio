# -*- coding: utf-8 -*-
# Copyright (C) 2012, imageio contributers
#
# imageio is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

import os
import sys
from distutils.core import setup

name = 'imageio'
description = 'Library for reading and writing a wide range of image formats.'


# Get version and docstring
__version__ = None
__doc__ = ''
docStatus = 0 # Not started, in progress, done
initFile = os.path.join(os.path.dirname(__file__), '__init__.py')
for line in open(initFile).readlines():
    if (line.startswith('__version__')):
        exec(line.strip())
    elif line.startswith('"""'):
        if docStatus == 0:
            docStatus = 1
            line = line.lstrip('"')
        elif docStatus == 1:
            docStatus == 2
    if docStatus == 1:
        __doc__ += line


# Download libs at install-time (not needed if user has them installed)
# If the lib cannot be found and is also not downloadable (e.g. Linux),
# only a warning is given. If not found but should be downloadable, will 
# raise error if this fails.
import freeimage_install
import findlib
if ('build' in sys.argv) or ('install' in sys.argv):
    findlib.load_freeimage(freeimage_install, False) 

setup(
    name = name,
    version = __version__,
    author = 'imageio contributers',
    author_email = 'a.klein@science-applied.nl',
    license = '(new) BSD',
    
    url = 'http://imageio.readthedocs.org',
    download_url = 'http://bitbucket.org/almarklein/imageio/downloads',    
    keywords = "FreeImage image imread imsave io",
    description = description,
    long_description = __doc__,
    
    platforms = 'any',
    provides = ['imageio'],
    requires = ['numpy'],
    
    packages = ['imageio', 'imageio.plugins'],
    package_dir = {'imageio': '.'}, # must be a dot, not an empty string
    package_data = {'imageio': ['lib/*',]},
    zip_safe = False,
    )
