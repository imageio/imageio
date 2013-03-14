----------------------
The classes in imageio
----------------------

.. insertdocs start:: imageio.base.__doc__




.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes may change. 

These are the main classes of imageio. They expose an interface for
advanced users and plugin developers. A brief overview:
  
  * :ref:`imageio.FormatManager<insertdocs-imageio-FormatManager>` - for keeping track of registered formats.
  * :ref:`imageio.Format<insertdocs-imageio-Format>` - representation of a file format reader/writer
  * :ref:`imageio.Format.Reader<insertdocs-imageio-Format-Reader>` - object used during the reading of a file.
  * :ref:`imageio.Format.Writer<insertdocs-imageio-Format-Writer>` - object used during saving a file.
  * :ref:`imageio.Request<insertdocs-imageio-Request>` - used to store the filename and other info.

Plugins need to implement a Format class and register
a format object using ``imageio.formats.add_format()``.

.. insertdocs end::

----

.. insertdocs start:: imageio.FormatManager
.. insertdocs :members: 


.. _insertdocs-imageio-FormatManager:

.. py:class:: imageio.FormatManager

  *Inherits from object*

  
  The format manager keeps track of the registered formats.
  
  This object supports getting a format object using indexing (by 
  format name or extension). When used as an iterator, this object 
  yields all format objects.
  
  There is exactly one FormatManager object in imageio: ``imageio.formats``.
  
  See also :ref:`imageio.help<insertdocs-imageio-help>`.
  

  *METHODS*

  .. _insertdocs-imageio-FormatManager-add_format:
  
  .. py:method:: imageio.FormatManager.add_format()
  
    add_formar(format)
    
    Register a format, so that imageio can use it.
    

  .. _insertdocs-imageio-FormatManager-create_docs_for_all_formats:
  
  .. py:method:: imageio.FormatManager.create_docs_for_all_formats()
  
    Function to auto-generate documentation for all the formats.
    

  .. _insertdocs-imageio-FormatManager-search_read_format:
  
  .. py:method:: imageio.FormatManager.search_read_format(request)
  
    Search a format that can read a file according to the given request.
    Returns None if no appropriate format was found. (used internally)
    

  .. _insertdocs-imageio-FormatManager-search_save_format:
  
  .. py:method:: imageio.FormatManager.search_save_format(request)
  
    Search a format that can save a file according to the given request. 
    Returns None if no appropriate format was found. (used internally)
    



.. insertdocs end::


----

.. insertdocs start:: imageio.Format
.. insertdocs :members: 


.. _insertdocs-imageio-Format:

.. py:class:: imageio.Format

  *Inherits from object*

  
  A format represents an implementation to read/save a particular 
  file format.
  
  A format instance is responsible for 1) providing information about
  a format; 2) determining whether a certain file can be read/saved
  with this format; 3) providing a reader/writer class.
  
  Generally, imageio will select the right format and use that to
  read/save an image. A format can also be explicitly chosen in all
  read/save functios.
  
  Use print(format), or help(format_name) to see its documentation.
  
  To implement a specific format, see the docs for the plugins.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Format-description:
  
  .. py:attribute:: imageio.Format.description
  
    Get a short description of this format.
    

  .. _insertdocs-imageio-Format-doc:
  
  .. py:attribute:: imageio.Format.doc
  
    Get documentation for this format (name + description + docstring).
    

  .. _insertdocs-imageio-Format-extensions:
  
  .. py:attribute:: imageio.Format.extensions
  
    Get a list of file extensions supported by this plugin.
    These are all lowercase without a leading dot.
    

  .. _insertdocs-imageio-Format-name:
  
  .. py:attribute:: imageio.Format.name
  
    Get the name of this format.
    

  *METHODS*

  .. _insertdocs-imageio-Format-can_read:
  
  .. py:method:: imageio.Format.can_read(request)
  
    Get whether this format can read data from the specified uri.
    

  .. _insertdocs-imageio-Format-can_save:
  
  .. py:method:: imageio.Format.can_save(request)
  
    Get whether this format can save data to the speciefed uri.
    

  .. _insertdocs-imageio-Format-read:
  
  .. py:method:: imageio.Format.read(request)
  
    Return a reader object that can be used to read data and info
    from the given file. Users are encouraged to use imageio.read() instead.
    

  .. _insertdocs-imageio-Format-save:
  
  .. py:method:: imageio.Format.save(request)
  
    Return a writer object that can be used to save data and info
    to the given file. Users are encouraged to use imageio.save() instead.
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Format.Reader
.. insertdocs :inherited-members: 
.. insertdocs :members: 


.. _insertdocs-imageio-Format-Reader:

.. py:class:: imageio.Format.Reader

  *Inherits from _BaseReaderWriter*

  
  A reader is an object that is instantiated for reading data from
  an image file. A reader can be used as an iterator, and only reads
  data from the file when new data is requested. 
  
  Plugins should overload a couple of methods to implement a reader. 
  A plugin may also specify extra methods to expose an interface
  specific for the file-format it exposes.
  
  A reader object should be obtained by calling imageio.read() or
  by calling the read() method on a format object. A reader can
  be used as a context manager so that it is automatically closed.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Format-Reader-closed:
  
  .. py:attribute:: imageio.Format.Reader.closed
  
    Get whether the reader/writer is closed.
    

  .. _insertdocs-imageio-Format-Reader-format:
  
  .. py:attribute:: imageio.Format.Reader.format
  
    Get the format corresponding to the current read/save operation.
    

  .. _insertdocs-imageio-Format-Reader-request:
  
  .. py:attribute:: imageio.Format.Reader.request
  
    Get the request object corresponding to the current read/save 
    operation.
    

  *METHODS*

  .. _insertdocs-imageio-Format-Reader-close:
  
  .. py:method:: imageio.Format.Reader.close()
  
    Flush and close the reader/writer.
    This method has no effect if it is already closed.
    

  .. _insertdocs-imageio-Format-Reader-get_data:
  
  .. py:method:: imageio.Format.Reader.get_data(index)
  
    Read image data from the file, using the image index. The
    returned image has a 'meta' attribute with the meta data.
    
    

  .. _insertdocs-imageio-Format-Reader-get_length:
  
  .. py:method:: imageio.Format.Reader.get_length()
  
    Get the number of images in the file. (Note: you can also
    use len(reader_object).)
    
    The result can be:
    * 0 for files that only have meta data
    * 1 for singleton images (e.g. in PNG, JPEG, etc.)
    * N for image series
    * np.inf for streams (series of unknown length)
    
    

  .. _insertdocs-imageio-Format-Reader-get_meta_data:
  
  .. py:method:: imageio.Format.Reader.get_meta_data(index=None)
  
    Read meta data from the file. using the image index. If the
    index is omitted, return the file's (global) meta data.
    
    Note that get_data also provides the meta data for the returned
    image as an atrribute of that image.
    
    The meta data is a dict that maps group names to subdicts. Each
    group is a dict with name-value pairs. The groups represent the
    different metadata formats (EXIF, XMP, etc.).
    
    

  .. _insertdocs-imageio-Format-Reader-iter_data:
  
  .. py:method:: imageio.Format.Reader.iter_data()
  
    Iterate over all images in the series. (Note: you can also
    iterate over the reader object.)
    
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Format.Writer
.. insertdocs :inherited-members: 
.. insertdocs :members: 
    

.. _insertdocs-imageio-Format-Writer:

.. py:class:: imageio.Format.Writer

  *Inherits from _BaseReaderWriter*

  
  A writer is an object that is instantiated for saving data to
  an image file. 
  
  Plugins should overload a couple of methods to implement a writer. 
  A plugin may also specify extra methods to expose an interface
  specific for the file-format it exposes.
  
  A writer object should be obtained by calling imageio.save() or
  by calling the save() method on a format object. A writer can
  be used as a context manager so that it is automatically closed.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Format-Writer-closed:
  
  .. py:attribute:: imageio.Format.Writer.closed
  
    Get whether the reader/writer is closed.
    

  .. _insertdocs-imageio-Format-Writer-format:
  
  .. py:attribute:: imageio.Format.Writer.format
  
    Get the format corresponding to the current read/save operation.
    

  .. _insertdocs-imageio-Format-Writer-request:
  
  .. py:attribute:: imageio.Format.Writer.request
  
    Get the request object corresponding to the current read/save 
    operation.
    

  *METHODS*

  .. _insertdocs-imageio-Format-Writer-append_data:
  
  .. py:method:: imageio.Format.Writer.append_data(im, meta={})
  
    Append an image to the file. 
    
    The appended meta data consists of the meta data on the given
    image (if applicable), updated with the given meta data.
    
    

  .. _insertdocs-imageio-Format-Writer-close:
  
  .. py:method:: imageio.Format.Writer.close()
  
    Flush and close the reader/writer.
    This method has no effect if it is already closed.
    

  .. _insertdocs-imageio-Format-Writer-set_meta_data:
  
  .. py:method:: imageio.Format.Writer.set_meta_data(meta)
  
    Sets the file's (global) meta data.
    
    The meta data is a dict that maps group names to subdicts. Each
    group is a dict with name-value pairs. The groups represents
    the different metadata formats (EXIF, XMP, etc.). Note that
    some meta formats may not be supported for writing, and even
    individual fields may be ignored if they are invalid.
    
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Request
.. insertdocs :members: 


.. _insertdocs-imageio-Request:

.. py:class:: imageio.Request

  *Inherits from object*

  ReadRequest(uri, expect, **kwargs)
  
  Represents a request for reading or saving a file. This object wraps
  information to that request and acts as an interface for the plugins
  to several resources; it allows the user to read from http, zipfiles,
  raw bytes, etc., but offer a simple interface to the plugins:
  get_file() and get_local_filename().
  
  Per read/save operation a single Request instance is used and passed
  to the can_read/can_save method of a format, and subsequently to the
  Reader/Writer class. This allows rudimentary passing of information
  between different formats and between a format and its reader/writer.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Request-expect:
  
  .. py:attribute:: imageio.Request.expect
  
    Get what kind of data was expected for reading. 
    See the imageio.EXPECT_* constants.
    

  .. _insertdocs-imageio-Request-filename:
  
  .. py:attribute:: imageio.Request.filename
  
    Get the uri for which reading/saving was requested. This
    can be a filename, an http address, or other resource
    identifier. Do not rely on the filename to obtain the data,
    but use the get_file() or get_local_filename() instead.
    

  .. _insertdocs-imageio-Request-firstbytes:
  
  .. py:attribute:: imageio.Request.firstbytes
  
    Get the first 256 bytes of the file. This can be used to 
    parse the header to determine the file-format.
    

  .. _insertdocs-imageio-Request-kwargs:
  
  .. py:attribute:: imageio.Request.kwargs
  
    Get the dict of keyword arguments supplied by the user.
    

  *METHODS*

  .. _insertdocs-imageio-Request-add_potential_format:
  
  .. py:method:: imageio.Request.add_potential_format(format)
  
    Allows a format to add itself as a potential format in cases
    where it seems capable of reading-saving the file, but 
    priority should be given to another Format.
    

  .. _insertdocs-imageio-Request-finish:
  
  .. py:method:: imageio.Request.finish()
  
    For internal use (called when the context of the reader/writer
    exists). Finishes this request. Close open files and process
    results.
    

  .. _insertdocs-imageio-Request-get_file:
  
  .. py:method:: imageio.Request.get_file()
  
    Get a file object for the resource associated with this request.
    If this is a reading request, the file is in read mode,
    otherwise in write mode. This method is not thread safe. Plugins
    do not need to close the file when done.
    
    This is the preferred way to read/write the data. If a format
    cannot handle file-like objects, they should use get_local_filename().
    

  .. _insertdocs-imageio-Request-get_local_filename:
  
  .. py:method:: imageio.Request.get_local_filename()
  
    If the filename is an existing file on this filesystem, return
    that. Otherwise a temporary file is created on the local file
    system which can be used by the format to read from or write to.
    

  .. _insertdocs-imageio-Request-get_potential_format:
  
  .. py:method:: imageio.Request.get_potential_format()
  
    Get the first known potential format. Calling this method 
    repeatedly will yield different formats until the list of 
    potential formats is exhausted.
    

  .. _insertdocs-imageio-Request-get_result:
  
  .. py:method:: imageio.Request.get_result()
  
    For internal use. In some situations a write action can have
    a result (bytes data). That is obtained with this function.
    



.. insertdocs end::
