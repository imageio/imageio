# -*- coding: utf-8 -*-
# Copyright (C) 2015, imageio contributors
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
  * Maybe test pypi page via "python setup.py register -r test"

Release:

  * Increase __version__
  * git tag the release
  * Upload to Pypi: python setup.py sdist upload
  * Update conda recipe on conda-forge feedstock

After release:

  * Set __version__ to dev
  * Announce

"""

import os
import os.path as op
import sys
import shutil
from distutils.core import Command
from distutils.command.sdist import sdist
from distutils.command.build_py import build_py


try:
    from setuptools import setup  # Supports wheels
except ImportError:
    from distutils.core import setup  # Supports anything else


try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = object


name = 'imageio'
description = 'Library for reading and writing a wide range of image, video, scientific, and volumetric data formats.'

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

.. code-block:: python
    
    >>> import imageio
    >>> im = imageio.imread('astronaut.png')
    >>> im.shape  # im is a numpy array
    (512, 512, 3)
    >>> imageio.imwrite('imageio:astronaut-gray.jpg', im[:, :, 0])

See the `user API <http://imageio.readthedocs.org/en/latest/userapi.html>`_
or `examples <http://imageio.readthedocs.org/en/latest/examples.html>`_
for more information.
"""

# Prepare resources dir
package_data = []
package_data.append('resources/shipped_resources_go_here')
package_data.append('resources/*.*')
package_data.append('resources/images/*.*')
package_data.append('resources/freeimage/*.*')
package_data.append('resources/ffmpeg/*.*')
package_data.append('resources/avbin/*.*')


def _set_crossplatform_resources(resource_dir):
    import imageio
    
    # Clear now
    if op.isdir(resource_dir):
        shutil.rmtree(resource_dir)
    os.mkdir(resource_dir)
    open(op.join(resource_dir, 'shipped_resources_go_here'), 'wb')
    
    # Load images
    for fname in ['images/chelsea.png',
                  'images/chelsea.zip',
                  'images/astronaut.png',
                  'images/newtonscradle.gif',
                  'images/cockatoo.mp4',
                  'images/realshort.mp4',
                  'images/stent.npz',
                  ]:
        imageio.core.get_remote_file(fname, resource_dir, 
                                     force_download=True)


def _set_platform_resources(resource_dir, platform):
    import imageio
    
    # Create file to show platform
    assert platform
    open(op.join(resource_dir, 'platform_%s' % platform), 'wb')
    
    # Load freeimage
    fname = imageio.plugins.freeimage.FNAME_PER_PLATFORM[platform]
    imageio.core.get_remote_file('freeimage/'+fname, resource_dir,
                                    force_download=True)
    
    # Load ffmpeg
    #fname = imageio.plugins.ffmpeg.FNAME_PER_PLATFORM[platform]
    #imageio.core.get_remote_file('ffmpeg/'+fname, resource_dir, 
    #                             force_download=True)


class test_command(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from imageio import testing
        os.environ['IMAGEIO_NO_INTERNET'] = '1'  # run tests without inet
        sys.exit(testing.test_unit())


class build_with_fi(build_py):
    def run(self):
        # Download images and libs
        import imageio
        resource_dir = imageio.core.resource_dirs()[0]
        _set_crossplatform_resources(resource_dir)
        _set_platform_resources(resource_dir, imageio.core.get_platform())
        # Build as  normal
        build_py.run(self)


class build_with_images(sdist):
    def run(self):
        # Download images
        import imageio
        resource_dir = imageio.core.resource_dirs()[0]
        _set_crossplatform_resources(resource_dir)
        # Build as  normal
        sdist.run(self)


setup(
    cmdclass={#'bdist_wheel_all': bdist_wheel_all,
              #'sdist_all': sdist_all,
              'build_with_images': build_with_images,
              'build_with_fi': build_with_fi,
              'sdist': build_with_images,
              'test': test_command},
    
    name = name,
    version = __version__,
    author = 'imageio contributors',
    author_email = 'almar.klein@gmail.com',
    license = '(new) BSD',
    
    url = 'http://imageio.github.io/',
    download_url = 'http://pypi.python.org/pypi/imageio',    
    keywords = "image video volume imread imwrite io animation ffmpeg",
    description = description,
    long_description = long_description.replace('__doc__', __doc__),
    
    platforms = 'any',
    provides = ['imageio'],
    install_requires = ['numpy', 'pillow'],
    extras_require = {'fits': ['astropy'],
                      'gdal': ['gdal'],
                      'simpleitk': ['SimpleITK'],
                      'full': ['astropy', 'gdal', 'SimpleITK'],
                      },
    
    packages = ['imageio', 'imageio.core', 'imageio.plugins'],
    package_dir = {'imageio': 'imageio'}, 
    
    # Data in the package
    package_data = {'imageio': package_data},
    
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
        'Programming Language :: Python :: 3.5',
        ],
    )
