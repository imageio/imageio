# -*- coding: utf-8 -*-
# Copyright (C) 2013, imageio contributers
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

from freeimage_install import retrieve_files

name = 'imageio'
description = 'Library for reading and writing a wide range of image formats.'


# Get version and docstring
__version__ = None
__doc__ = ''
docStatus = 0 # Not started, in progress, done
initFile = os.path.join(os.path.dirname(__file__), 'imageio',  '__init__.py')
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


# Get Resource dir
RD = os.path.abspath('imageio/lib') 

# Download libs at install-time. Determine which libs to include
if ('build' in sys.argv) or ('install' in sys.argv):
    # Download what *this* system needs
    if sys.platform.startswith('win'):
        retrieve_files(RD, 32) 
        retrieve_files(RD, 64)
    else:
        retrieve_files(RD)
    libFilter = 'lib/*'
elif 'sdist' in sys.argv:
    # Pack only the txt file
    libFilter = 'lib/*.txt' 
elif 'bdist' in sys.argv or 'bdist_wininst' in sys.argv:
    # Download and pack 32 bit and 64 bit binaries 
    retrieve_files(RD, 32) 
    retrieve_files(RD, 64)
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
    download_url = 'http://pypi.python.org/pypi/imageio',    
    keywords = "FreeImage image imread imsave io animation volume",
    description = description,
    long_description = __doc__,
    
    platforms = 'any',
    provides = ['imageio'],
    requires = ['numpy'],
    
    packages = ['imageio', 'imageio.plugins'],
    package_dir = {'imageio': 'imageio'}, 
    package_data = {'imageio': [libFilter, '../freeimage_install.py'] },
    zip_safe = False,
    
    classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Education',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          ],
    )
