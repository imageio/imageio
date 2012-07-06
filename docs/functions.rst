------------------------
The functions in imageio
------------------------

.. note::
    imageio is under construction, only a limited set of functions have yet
    been implemented.

.. insertdocs start:: imageio.functions.__doc__



These are the main functions exposed to the user.

For images:

  * :ref:`imageio.imread<insertdocs-imageio-imread>` - reads an image from the specified file and return as a 
    numpy array.
  * :ref:`imageio.imsave<insertdocs-imageio-imsave>` - save an image to the specified file.
  * imageio.mimread - read a series of images from the specified file.
  * imageio.mimsave - save a series of images to the specified file.

For volumes: todo

For somewhat lower level and more control:

  * :ref:`imageio.read<insertdocs-imageio-read>`: returns a reader object which can be used to read data 
    and info from the specified file. 
  * :ref:`imageio.save<insertdocs-imageio-save>`: returns a writer object which can be used to write data
    and info to the specified file.


.. insertdocs end::

----

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

  Returns a writer object which can be used to write data and info 
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

