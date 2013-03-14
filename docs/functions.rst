------------------------
The functions in imageio
------------------------


.. insertdocs start:: imageio.functions.__doc__



These functions are the main interface for the imageio user. They
provide a common interface to read and save image data for a large
variety of formats. All read and save functions accept keyword
arguments, which are passed on to the format that does the actual work.
To see what keyword arguments are supported by a specific format, use
the :ref:`imageio.help<insertdocs-imageio-help>` function.

**Functions for reading**



  * :ref:`imageio.imread<insertdocs-imageio-imread>` - read an image from the specified uri
  * :ref:`imageio.mimread<insertdocs-imageio-mimread>` - read a series of images from the specified uri
  * :ref:`imageio.volread<insertdocs-imageio-volread>` - read a volume from the specified uri
  * :ref:`imageio.mvolsave<insertdocs-imageio-mvolsave>` - save a series of volumes to the specified uri

**Functions for saving**



  * :ref:`imageio.imsave<insertdocs-imageio-imsave>` - save an image to the specified uri
  * :ref:`imageio.mimsave<insertdocs-imageio-mimsave>` - save a series of images to the specified uri
  * :ref:`imageio.volsave<insertdocs-imageio-volsave>` - save a volume to the specified uri
  * :ref:`imageio.mvolread<insertdocs-imageio-mvolread>` - read a series of volumes from the specified uri

**More control**



For a larger degree of control, imageio provides the functions
:ref:`imageio.read<insertdocs-imageio-read>` and :ref:`imageio.save<insertdocs-imageio-save>`. They respectively return an
:ref:`imageio.Format.Reader<insertdocs-imageio-Format-Reader>` and an :ref:`imageio.Format.Writer<insertdocs-imageio-Format-Writer>` object, which can
be used to read/save data and meta data in a more controlled manner.
This also allows specific scientific formats to be exposed in a way
that best suits that file-format.

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

.. py:function:: imageio.read(uri, format=None, expect=None, **kwargs)

  Returns a reader object which can be used to read data and info 
  from the specified file.
  
  **Parameters**
  
  
  uri : {str, bytes}
      The resource to load the image from. This can be a normal
      filename, a file in a zipfile, an http/ftp address, a file
      object, or the raw bytes.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
      Used to give the reader a hint on what the user expects. Optional.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.save


.. _insertdocs-imageio-save:

.. py:function:: imageio.save(uri, format=None, expect=None, **kwargs)

  Returns a writer object which can be used to save data and info 
  to the specified file.
  
  **Parameters**
  
  
  uri : str
      The resource to save the image to. This can be a normal
      filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
      case the raw bytes are returned.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename.
  expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
      Used to give the writer a hint on what kind of data to expect. Optional.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


----


.. insertdocs start:: imageio.imread


.. _insertdocs-imageio-imread:

.. py:function:: imageio.imread(uri, format=None, **kwargs)

  Reads an image from the specified file. Returns a numpy array, which
  comes with a dict of meta data at its 'meta' attribute.
  
  **Parameters**
  
  
  uri : {str, bytes}
      The resource to load the image from. This can be a normal
      filename, a file in a zipfile, an http/ftp address, a file
      object, or the raw bytes.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.mimread


.. _insertdocs-imageio-mimread:

.. py:function:: imageio.mimread(uri, format=None, **kwargs)

  Reads multiple images from the specified file. Returns a list of
  numpy arrays, each with a dict of meta data at its 'meta' attribute.
  
  **Parameters**
  
  
  uri : {str, bytes}
      The resource to load the images from. This can be a normal
      filename, a file in a zipfile, an http/ftp address, a file
      object, or the raw bytes.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.volread


.. _insertdocs-imageio-volread:

.. py:function:: imageio.volread(uri, format=None, **kwargs)

  Reads a volume from the specified file. Returns a numpy array, which
  comes with a dict of meta data at its 'meta' attribute.
  
  **Parameters**
  
  
  uri : {str, bytes}
      The resource to load the volume from. This can be a normal
      filename, a file in a zipfile, an http/ftp address, a file
      object, or the raw bytes.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.mvolread


.. _insertdocs-imageio-mvolread:

.. py:function:: imageio.mvolread(uri, format=None, **kwargs)

  Reads multiple volumes from the specified file. Returns a list of
  numpy arrays, each with a dict of meta data at its 'meta' attribute.
  
  **Parameters**
  
  
  uri : {str, bytes}
      The resource to load the volumes from. This can be a normal
      filename, a file in a zipfile, an http/ftp address, a file
      object, or the raw bytes.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


----


.. insertdocs start:: imageio.imsave


.. _insertdocs-imageio-imsave:

.. py:function:: imageio.imsave(uri, im, format=None, **kwargs)

  Save an image to the specified file.
  
  **Parameters**
  
  
  uri : str
      The resource to save the image to. This can be a normal
      filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
      case the raw bytes are returned.
  im : numpy.ndarray
      The image data. Must be NxM, NxMx3 or NxMx4.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.mimsave


.. _insertdocs-imageio-mimsave:

.. py:function:: imageio.mimsave(uri, ims, format=None, **kwargs)

  Save multiple images to the specified file.
  
  **Parameters**
  
  
  uri : str
      The resource to save the images to. This can be a normal
      filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
      case the raw bytes are returned.
  ims : sequence of numpy arrays
      The image data. Each array must be NxM, NxMx3 or NxMx4.
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.volsave


.. _insertdocs-imageio-volsave:

.. py:function:: imageio.volsave(uri, vol, format=None, **kwargs)

  Save a volume to the specified file.
  
  **Parameters**
  
  
  uri : str
      The resource to save the image to. This can be a normal
      filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
      case the raw bytes are returned.
  vol : numpy.ndarray
      The image data. Must be NxMxL (or NxMxLxK if each voxel is a tuple).
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::


.. insertdocs start:: imageio.mvolsave


.. _insertdocs-imageio-mvolsave:

.. py:function:: imageio.mvolsave(uri, vols, format=None, **kwargs)

  Save multiple volumes to the specified file.
  
  **Parameters**
  
  
  uri : str
      The resource to save the volumes to. This can be a normal
      filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
      case the raw bytes are returned.
  ims : sequence of numpy arrays
      The image data. Each array must be NxMxL (or NxMxLxK if each
      voxel is a tuple).
  format : str
      The format to use to read the file. By default imageio selects
      the appropriate for you based on the filename and its contents.
  
  Further keyword arguments are passed to the reader. See :ref:`imageio.help<insertdocs-imageio-help>`
  to see what arguments are available for a particular format.
  
  
.. insertdocs end::
