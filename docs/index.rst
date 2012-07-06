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

For images, four convenience functions are exposed:
  * :ref:`imageio.imread<insertdocs-imageio-imread>` - to read an image file and return a numpy array
  * :ref:`imageio.imsave<insertdocs-imageio-imsave>` - to write a numpy array to an image file
  * imageio.mimread - to read animated image data as a list of numpy arrays
  * imageio.mimsave - to write a list of numpy array to an animated image

Similarly, for volumes imageio provides volread, volsave, mvolread and mvolsave.

For a larger degree of control, imageio provides the functions 
:ref:`imageio.read<insertdocs-imageio-read>` and :ref:`imageio.save<insertdocs-imageio-save>`. They respectively return a :ref:`imageio.Reader<insertdocs-imageio-Reader>` and a
:ref:`imageio.Writer<insertdocs-imageio-Writer>` object, which can be used to read/save data and meta data in a
more controlled manner. This also allows specific scientific formats to
be exposed in a way that best suits that file-format.

To get a list of supported formats and documentation for a certain format, 
use the ``help`` method of the ``imageio.formats`` object (see the 
:ref:`imageio.FormatManager<insertdocs-imageio-FormatManager>`
class).

The imageio library is intended as a replacement for PIL. Currently, most
functionality is obtained by wrapping the FreeImage library using ctypes. 

.. insertdocs end::


Features
========

  * Simple interface via :ref:`imageio.imread<insertdocs-imageio-imread>`, :ref:`imageio.imsave<insertdocs-imageio-imsave>` and others.
  * Easy to install (no compilation needed, required binaries automatically 
    downloaded on Windows and Mac).
  * More powerfull interface via :ref:`imageio.read<insertdocs-imageio-read>` and :ref:`imageio.save<insertdocs-imageio-save>`.
  * Easy to extend using plugins, also for file formats with complex data structures.
  * Pure Python, runs on Python 2.x and 3.x (without 2to3).
  * Loads of supported :doc:`formats <formats>`.

Installation
============
You can install imageio using one of these options:
  
  * imageio will be pip installable soon. (and easy_install too)
  * Get the zip file with the source code, extract and call 
    ``python setup.py install``.
  * Clone the repository to a directory called "imageio" and place that 
    somewhere on your PYTHONPATH. 

Important links
================
   * main website: http://imageio.readthedocs.org
   * discussion group: http://groups.google.com/d/forum/imageio
   * source code: http://bitbucket.org/almarklein/imageio


Contents
========

.. toctree::
  :maxdepth: 1
  
  imageio's functions <functions>
  imageio's classes <classes>
  supported formats <formats>
  writing plugins <plugins>
    
