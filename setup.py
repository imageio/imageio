# -*- coding: utf-8 -*-
# Copyright (C) 2014, imageio contributors
#
# imageio is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

# styletest: skip

"""

Before release:

  * Run test suite on pypy (with numpy)
  * Run test suite on Windows 32
  * Run test suite on Windows 64
  * Run test suite on OS X
  * Write release notes
  * Check if docs are still good

Release:

  * Increase __version__
  * git tag the release
  * Upload to Pypi:
    * python setup.py register
    * python setup.py sdist upload
  * Update, build and upload conda package

Add "-r testpypi" to use the test repo. 

After release:

  * Set __version__ to dev
  * Announce

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

# Template for long description. __doc__ gets inserted here
long_description = """
.. image:: https://travis-ci.org/imageio/imageio.svg?branch=master
    :target: https://travis-ci.org/imageio/imageio'

.. image:: https://coveralls.io/repos/imageio/imageio/badge.png?branch=master
  :target: https://coveralls.io/r/imageio/imageio?branch=master

__doc__

Release notes: http://imageio.readthedocs.org/en/latest/releasenotes.html

Example:

.. code-block:: python:
    
    >>> import imageio
    >>> im = imageio.imread('astronaut.png')
    >>> im.shape  # im is a numpy array
    (512, 512, 3)
    >>> imageio.imsave('astronaut-gray.jpg', im[:, :, 0])

See the `user API <http://imageio.readthedocs.org/en/latest/userapi.html>`_
or `examples <http://imageio.readthedocs.org/en/latest/examples.html>`_
for more information.
"""

setup(
    name = name,
    version = __version__,
    author = 'imageio contributors',
    author_email = 'almar.klein@gmail.com',
    license = '(new) BSD',
    
    url = 'http://imageio.github.io/',
    download_url = 'http://pypi.python.org/pypi/imageio',    
    keywords = "image imread imsave io animation volume FreeImage ffmpeg",
    description = description,
    long_description = long_description.replace('__doc__', __doc__),
    
    platforms = 'any',
    provides = ['imageio'],
    requires = ['numpy'],
    
    packages = ['imageio', 'imageio.core', 'imageio.plugins'],
    package_dir = {'imageio': 'imageio'}, 
    
    classifiers = [
        'Development Status :: 5 - Production/Stable',
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
