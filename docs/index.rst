.. imageio documentation master file, created by
   sphinx-quickstart on Thu May 17 16:58:47 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to imageio's documentation!
===================================

.. insertdocs start:: imageio.__doc__



The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

The imageio library is intended as a replacement for PIL. Currently, most
functionality is obtained by wrapping the FreeImage library using ctypes. 

Quickstart:

  * Use :ref:`imageio.imread<insertdocs-imageio-imread>` to read an image
  * Use :ref:`imageio.imsave<insertdocs-imageio-imsave>` to save an image
  * See the `functions page <http://imageio.readthedocs.org/en/latest/functions.html>`_ for more information.
 
.. insertdocs end::


Features
========

  * Simple interface via a consise set of :doc:`functions <functions>`.
  * Easy to install (no compilation needed, required binaries are automatically 
    downloaded on Windows and Mac).
  * More powerfull interface if needed via :ref:`imageio.read<insertdocs-imageio-read>` and :ref:`imageio.save<insertdocs-imageio-save>`.
  * Easy to extend using plugins, also for file formats with complex data structures.
  * Pure Python, runs on Python 2.x and 3.x (without 2to3).
  * Lots of supported :doc:`formats <formats>`.

Installation
============
You can install imageio using one of these options:
  
  * ``pip install imageio`` or ``easy_install imageio``.
  * Get the zip file with the source code, extract and call 
    ``python setup.py install``.
  * Clone the repository to a directory called "imageio" and place that 
    somewhere on your PYTHONPATH. 

Important links
================

  * main website: http://imageio.readthedocs.org
  * discussion group: http://groups.google.com/d/forum/imageio
  * source code: http://bitbucket.org/almarklein/imageio
  * downloads: http://pypi.python.org/pypi/imageio


Contents
========

.. toctree::
  :maxdepth: 1
  
  imageio's functions (user API) <functions>
  imageio's classes (developer API) <classes>
  supported formats <formats>
  writing plugins <plugins>
  release notes <releasenotes>
    
