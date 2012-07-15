------------------------
The functions in imageio
------------------------


.. insertdocs start:: imageio.functions.__doc__




.. note::
    imageio is under construction, only a limited set of functions have yet
    been implemented. However, the imread and imsave functions work
    and their signature is very likely to stay the same.

These functions are the main interface for the imageio user. They
provide a common interface to read and save image data 
for a large variety of formats. All read and save functions accept keyword 
arguments, which are passed on to the format that does the actual work. 
To see what keyword arguments are supported by a specific format, use
the :ref:`imageio.help<insertdocs-imageio-help>` function.

Functions for reading/saving of images:

  * :ref:`imageio.imread<insertdocs-imageio-imread>` - reads an image from the specified file and return as a 
    numpy array.
  * :ref:`imageio.imsave<insertdocs-imageio-imsave>` - save an image to the specified file.
  * imageio.mimread - read a series of images from the specified file.
  * imageio.mimsave - save a series of images to the specified file.

Functions for reading/saving of volumes: todo

For a larger degree of control, imageio provides the functions 
:ref:`imageio.read<insertdocs-imageio-read>` and :ref:`imageio.save<insertdocs-imageio-save>`. They respectively return an :ref:`imageio.Reader<insertdocs-imageio-Reader>`
and an :ref:`imageio.Writer<insertdocs-imageio-Writer>` object, which can be used to read/save data and meta
data in a more controlled manner. This also allows specific scientific 
formats to be exposed in a way that best suits that file-format.

.. insertdocs end::

----

.. insertdocs start:: imageio.help


.. _insertdocs-imageio-help:

.. py:function:: imageio.help(name=None)

  Print the documentation of the format specified by name, or a list
  of supported formats if name is omitted.
  
  The specified name can be the name of a format, a filename extension, 
  or a full filename.
  
  See also the :doc:`formats page <formats>`.
  
  
.. insertdocs end::



.. insertdocs start:: imageio.read


.. _insertdocs-imageio-read:

.. py:function:: imageio.read(filename, format=None, expect=None, **kwargs)

  Returns a reader object which can be used to read data and info 
  from the specified file.
  
  **Parameters**
  
  
  filename : str
      The location of the file on the file system.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
      Used to give the reader a hint on what the user expects. Optional.
  
  Further keyword arguments are passed to the reader. See the docstring
  of the corresponding format to see what arguments are available.
  
  
.. insertdocs end::

.. insertdocs start:: imageio.save


.. _insertdocs-imageio-save:

.. py:function:: imageio.save(filename, format=None, expect=None, **kwargs)

  Returns a writer object which can be used to save data and info 
  to the specified file.
  
  **Parameters**
  
  
  filename : str
      The location of the file to save to.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename.
  expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
      Used to give the writer a hint on what kind of data to expect. Optional.
  
  Further keyword arguments are passed to the writer. See the docstring
  of the corresponding format to see what arguments are available.
  
  
.. insertdocs end::

.. insertdocs start:: imageio.imread


.. _insertdocs-imageio-imread:

.. py:function:: imageio.imread(filename, format=None, **kwargs)

  Reads an image from the specified file. Returns a numpy array.
  
  **Parameters**
  
  
  filename : str
      The location of the file on the file system.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See the docstring
  of the corresponding format to see what arguments are available.
  
  
.. insertdocs end::

.. insertdocs start:: imageio.imsave


.. _insertdocs-imageio-imsave:

.. py:function:: imageio.imsave(filename, im, format=None, **kwargs)

  Save an image to the specified file.
  
  **Parameters**
  
  
  filename : str
      The location of the file to save to.
  im : numpy.ndarray
      The image data. Must be NxM, NxMx3 or NxMx4.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the writer. See the docstring
  of the corresponding format to see what arguments are available.
  
  
.. insertdocs end::

