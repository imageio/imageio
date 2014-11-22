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
import os.path as op
import sys
from distutils.core import setup

name = 'imageio'
description = 'Library for reading and writing a wide range of image formats.'

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Get version and docstring
__version__ = None
__doc__ = ''
docStatus = 0 # Not started, in progress, done
initFile = os.path.join(THIS_DIR, 'imageio',  '__init__.py')
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

# Collect files to more or less reproduce the repo in the dist package.
# In that way the tests can be run and docs be build for Debian packaging.
#
# Collect docs
docs_files = [os.path.join('docs', fn) 
              for fn in os.listdir(op.join(THIS_DIR, 'docs'))]
docs_files += [op.join('docs', 'ext', fn) 
               for fn in os.listdir(op.join(THIS_DIR, 'docs', 'ext'))]
docs_files = [fn for fn in docs_files if op.isfile(op.join(THIS_DIR, fn))]
# Collect test files
test_files = [os.path.join('tests', fn)
              for fn in os.listdir(os.path.join(THIS_DIR, 'tests'))
              if (fn.endswith('.py') or fn.endswith('.md'))]
# Collect make files
make_files = [os.path.join('make', fn)
              for fn in os.listdir(os.path.join(THIS_DIR, 'make'))
              if (fn.endswith('.py') or fn.endswith('.md'))]

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
    
    data_files = [('tests', test_files),
                  ('docs', docs_files), 
                  ('make', make_files), 
                  ('', ['LICENSE', 'README.md', 'CONTRIBUTORS.txt'])],
    
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
