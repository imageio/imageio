# -*- coding: utf-8 -*-
# Copyright (C) 2012, imageio contributers
#
# imageio is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" To Update to new version:

  * Increase __version__
  * Write release notes
  * Update docs (pushing the repo will trigger RTD to rebuild)
  * python setup.py register
  * python setup.py sdist upload
  * python setup.py bdist_wininst upload

Add "-r testpypi" to use the test repo. 

"""

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
            docStatus = 2
    if docStatus == 1:
        __doc__ += line


# Download libs at install-time (not needed if user has them installed)
# If the lib cannot be found and is also not downloadable (e.g. Linux),
# only a warning is given. If not found but should be downloadable, will 
# raise error if this fails.
# 
# For bdist distributions (Windows only) will download both 32bit and 64bit
# libs when building the package. 

import freeimage_install
if ('build' in sys.argv) or ('install' in sys.argv):
    # Download what *this* system needs
    freeimage_install.load_freeimage(False) 
    libFilter = 'lib/*'
elif 'sdist' in sys.argv:
    # Pack only the txt file
    libFilter = 'lib/*.txt' 
elif 'bdist' in sys.argv or 'bdist_wininst' in sys.argv:
    # Download and pack 32 bit and 64 bit binaries 
    freeimage_install.retrieve_files(32) 
    freeimage_install.retrieve_files(64)
    libFilter = 'lib/*'
else:
    libFilter = 'lib/*'


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
    package_data = {'imageio': [libFilter,]},
    zip_safe = False,
    )
