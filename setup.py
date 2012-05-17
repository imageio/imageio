# -*- coding: utf-8 -*-
# Copyright (C) 2012, imageio contributers
#
# imageio is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

import sys
import imageio
from distutils.core import setup

name = 'imageio'
description = 'Library for reading and writing a wide range of image formats.'
long_description = imageio.__doc__
version = imageio.__version__

# todo: Allow downloading during runtime as well
# todo: Windows generates a warning popup when trying to load the MAC dll.

# Download libs and put in the lib dir
from imageio.freeimage_install import retrieve_files
if 'sdist' in sys.argv or 'bdist' in sys.argv:
    retrieve_files(True) # Retieve *all* binaries
elif 'build' in sys.argv or 'install' in sys.argv:
    retrieve_files() # Retieve only the one for this OS


setup(
    name = name,
    version = version,
    author = 'imageio contributers',
    author_email = 'a.klein@science-applied.nl',
    license = '(new) BSD',
    
    url = 'http://imageio.readthedocs.org',
    download_url = 'http://bitbucket.org/almarklein/imageio/downloads',    
    keywords = "FreeImage image imread imwrite io",
    description = description,
    long_description = long_description,
    
    platforms = 'any',
    provides = ['imageio'],
    requires = ['numpy'],
    
    packages = ['imageio'],
    package_dir = {'imageio': '.'}, # must be a dot, not an empty string
    package_data = {'imageio': ['lib/*',]},
    zip_safe = False, # I want examples to work
    )
