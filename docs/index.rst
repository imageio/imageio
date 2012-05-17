.. imageio documentation master file, created by
   sphinx-quickstart on Thu May 17 16:58:47 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to imageio's documentation!
===================================

.. insertdocs start:: imageio.__doc__



The imageio library aims to support reading and writing a wide 
range of image data, including animated images. It is written 
in pure Python (2.x and 3.x) and most functionality is obtained
by wrapping the FreeImage library using ctypes. The imageio 
projected is intended as a replacement for PIL.

Four functions are exposed:
  * imread() - to read an image file and return a numpy array
  * imwrite() - to write a numpy array to an image file
  * movieread() - (name may change) to read animated image data as a list of numpy arrays
  * moviewrite() - (name may change) to write a list of numpy array to an animated image

Further, via the module imageio.freeimage part of the FreeImage library 
is exposed.

Well this is the idea anyway. We're still developing :)
.. insertdocs end::


Important links
================
   * main website: http://imageio.readthedocs.org
   * discussion group: http://groups.google.com/d/forum/imageio
   * source code: http://bitbucket.org/almarklein/imageio





API
===


.. insertdocs start:: imageio.imread


.. _insertdocs-imageio-imread:

.. py:function:: imageio.imread()

  
  img = imread(filename)
  
  Reads an image from file `filename`
  
  **Parameters**
  
  
    filename : file name
  **Returns**
  
  
    img : ndarray
.. insertdocs end::

.. insertdocs start:: imageio.imwrite


.. _insertdocs-imageio-imwrite:

.. py:function:: imageio.imwrite()

  
  imwrite(filename, img)
  
  Save image to disk
  
  Image type is inferred from filename
  
  **Parameters**
  
  
    filename : file name
    img : image to be saved as nd array
.. insertdocs end::




..  Indices and tables
.. ==================

..  * :ref:`genindex`
..  * :ref:`modindex`
.. * :ref:`search`

.. Contents:

.. c .. toctree::
.. c   :maxdepth: 2
