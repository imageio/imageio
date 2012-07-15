----------------------
The classes in imageio
----------------------

.. insertdocs start:: imageio.base.__doc__




.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes will probably change. We'll have to
    implement a few more plugins to see what works well and what not.

These are the main classes of imageio. They expose an interface for
advanced users and plugin developers. A brief overview:
  
  * :ref:`imageio.FormatManager<insertdocs-imageio-FormatManager>` - for keeping track of registered formats.
  * :ref:`imageio.Format<insertdocs-imageio-Format>` - the thing that says it can read/save a certain file.
    Has a reader and writer class asociated with it.
  * :ref:`imageio.Reader<insertdocs-imageio-Reader>` - object used during the reading of a file.
  * :ref:`imageio.Writer<insertdocs-imageio-Writer>` - object used during saving a file.
  * :ref:`imageio.Request<insertdocs-imageio-Request>` - used to store the filename and other info.

Plugins need to implement a Reader, Writer and Format class and register
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
  
  A format instance is responsible for 1) providing information
  about a format; 2) instantiating a reader/writer class; 3) determining
  whether a certain file can be read/saved with this format.
  
  Generally, imageio will select the right format and use that to
  read/save an image. A format can also be used directly by calling 
  its read() and save() methods.
  
  Use print(format) to see its documentation.
  
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
    

  .. _insertdocs-imageio-Format-name:
  
  .. py:attribute:: imageio.Format.name
  
    Get the name of this format.
    

  *METHODS*

  .. _insertdocs-imageio-Format-can_read:
  
  .. py:method:: imageio.Format.can_read(request)
  
    Get whether this format can read data from the specified file.
    

  .. _insertdocs-imageio-Format-can_save:
  
  .. py:method:: imageio.Format.can_save(request)
  
    Get whether this format can save data to the speciefed file.
    

  .. _insertdocs-imageio-Format-read:
  
  .. py:method:: imageio.Format.read(request)
  
    Return a reader object that can be used to read data and info
    from the given file. Used internally. Users are encouraged to
    use imageio.read() instead.
    

  .. _insertdocs-imageio-Format-save:
  
  .. py:method:: imageio.Format.save(request)
  
    Return a writer object that can be used to save data and info
    to the given file. Used internally. Users are encouraged to
    use imageio.save() instead.
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Reader
.. insertdocs :inherited-members: 
.. insertdocs :members: 


.. _insertdocs-imageio-Reader:

.. py:class:: imageio.Reader

  *Inherits from BaseReaderWriter*

  
  A reader is an object that is instantiated for reading data from
  an image file. A reader can be used as an iterator, and only reads
  data from the file when new data is requested. The reading should
  finish by calling close().
  
  Plugins should overload a couple of methods to implement a reader. 
  A plugin may also specify extra methods to expose an interface
  specific for the file-format it exposes.
  
  A reader object should be obtained by calling imageio.read() or
  by calling the read() method on a format object.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Reader-request:
  
  .. py:attribute:: imageio.Reader.request
  
    Get the request object corresponding to the current read/save 
    operation.
    

  *METHODS*

  .. _insertdocs-imageio-Reader-close:
  
  .. py:method:: imageio.Reader.close()
  
    Close this reader/writer. Note that the recommended usage
    of reader/writer objects is to use them in a "with-statement".
    

  .. _insertdocs-imageio-Reader-init:
  
  .. py:method:: imageio.Reader.init()
  
    Initialize the reader/writer. Note that the recommended usage
    of reader/writer objects is to use them in a "with-statement".
    

  .. _insertdocs-imageio-Reader-read_data:
  
  .. py:method:: imageio.Reader.read_data(*indices, **kwargs)
  
    Read data from the file. If appropriate, indices can be given.
    The keyword arguments are merged with the keyword arguments
    specified in the read() function.
    
    

  .. _insertdocs-imageio-Reader-read_info:
  
  .. py:method:: imageio.Reader.read_info(*indices, **kwargs)
  
    Read info (i.e. meta data) from the file. If appropriate, indices 
    can be given. The keyword arguments are merged with the keyword 
    arguments specified in the read() function.
    
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Writer
.. insertdocs :inherited-members: 
.. insertdocs :members: 
    

.. _insertdocs-imageio-Writer:

.. py:class:: imageio.Writer

  *Inherits from BaseReaderWriter*

  
  A writer is an object that is instantiated for saving data to
  an image file. A writer enables writing different parts separately.
  The writing should be flushed by using close().
  
  Plugins should overload a couple of methods to implement a writer. 
  A plugin may also specify extra methods to expose an interface
  specific for the file-format it exposes.
  
  A writer object should be obtained by calling imageio.save() or
  by calling the save() method on a format object.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Writer-request:
  
  .. py:attribute:: imageio.Writer.request
  
    Get the request object corresponding to the current read/save 
    operation.
    

  *METHODS*

  .. _insertdocs-imageio-Writer-close:
  
  .. py:method:: imageio.Writer.close()
  
    Close this reader/writer. Note that the recommended usage
    of reader/writer objects is to use them in a "with-statement".
    

  .. _insertdocs-imageio-Writer-init:
  
  .. py:method:: imageio.Writer.init()
  
    Initialize the reader/writer. Note that the recommended usage
    of reader/writer objects is to use them in a "with-statement".
    

  .. _insertdocs-imageio-Writer-save_data:
  
  .. py:method:: imageio.Writer.save_data(*indices, **kwargs)
  
    Save image data to the file. If appropriate, indices can be given.
    The keyword arguments are merged with the keyword arguments
    specified in the save() function.
    
    

  .. _insertdocs-imageio-Writer-save_info:
  
  .. py:method:: imageio.Writer.save_info(*indices, **kwargs)
  
    Save info (i.e. meta data) to the file. If appropriate, indices can 
    be given. The keyword arguments are merged with the keyword arguments
    specified in the save() function.
    
    



.. insertdocs end::

----

.. insertdocs start:: imageio.Request
.. insertdocs :members: 


.. _insertdocs-imageio-Request:

.. py:class:: imageio.Request(filename, expect, **kwargs)

  *Inherits from object*

  Represents a request for reading or saving a file. This object wraps
  information to that request.
  
  Per read/save operation a single Request instance is used and passed
  to the can_read/can_save method of a format, and subsequently to the
  Reader/Writer class. This allows some rudimentary passing of 
  information between different formats and between a format and its 
  reader/writer.
  
  

  *PROPERTIES*

  .. _insertdocs-imageio-Request-expect:
  
  .. py:attribute:: imageio.Request.expect
  
    Get what kind of data was expected for reading. 
    See the imageio.EXPECT_* constants.
    

  .. _insertdocs-imageio-Request-filename:
  
  .. py:attribute:: imageio.Request.filename
  
    Get the filename for which reading/saving was requested.
    

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
    

  .. _insertdocs-imageio-Request-get_potential_format:
  
  .. py:method:: imageio.Request.get_potential_format()
  
    Get the first known potential format. Calling this method 
    repeatedly will yield different formats until the list of 
    potential formats is exhausted.
    



.. insertdocs end::
