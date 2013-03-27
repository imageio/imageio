-------
Plugins
-------

.. insertdocs start:: imageio.plugins.__doc__




.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes and how they should be implemented
    may still change. If you want to implement a plugin, maybe you
    can also help work out the details of the API for the Reader
    and Writer classes.

**What is a plugin**



In imageio, a plugin provides one or more :ref:`imageio.Format<insertdocs-imageio-Format>` objects, and 
corresponding imageio.Reader and imageio.Writer classes.
Each :ref:`imageio.Format<insertdocs-imageio-Format>` object represents an implementation to read/save a 
particular file format. Its Reader and Writer classes do the actual
reading/saving.


**Registering**



Strictly speaking a format can be used stand alone. However, to allow 
imageio to automatically select it for a specific file, the format must
be registered using imageio.formats.add_format(). 

Note that a plugin is not required to be part of the imageio package; as
long as a format is registered, imageio can use it. This makes imageio very 
easy to extend.


**What methods to implement**



Imageio is designed such that plugins only need to implement a few
private methods. The public API is implemented by the base classes.
In effect, the public methods can be given a descent docstring which
does not have to be repeated at the plugins.

For the :ref:`imageio.Format<insertdocs-imageio-Format>` class, the following needs to be implemented/specified:

  * The format needs a short name, a description, and a list of file
    extensions that are common for the file-format in question.
  * Use a docstring to provide more detailed information about the
    format/plugin.
  * Implement _can_read(request), return a bool. See also the Request class.
  * Implement _can_save(request), dito.

For the :ref:`imageio.Format.Reader<insertdocs-imageio-Format-Reader>` class:
  
  * Implement _open(**kwargs) to initialize the reader, with the
    user-provided keyword arguments.
  * Implement _close() to clearn up
  * Implement _get_length() to provide a suitable length based on what
    the user expects. Can be np.inf for streaming data.
  * Implement _get_data(index) to return an array and a meta-data dict.
  * Implement _get_meta_data(index) to return a meta-data dict. If index
    is None, it should return the 'global' meta-data.
  * Optionally implement _get_next_data() to provide allow streaming.

For the imageio.format.Writer class:
    
  * Implement _open(**kwargs) to initialize the writer, with the
    user-provided keyword arguments.
  * Implement _close() to clearn up
  * Implement _append_data(im, meta) to add data (and meta-data).
  * Implement _set_meta_data(meta) to set the global meta-data.

.. insertdocs end::


Example
-------

This code is from ``imageio/plugins/example.py``:

.. code-block:: python
    :linenos:

    from imageio import formats
    from imageio.base import Format
    import numpy as np
    
    
    class DummyFormat(Format):
        """ The dummy format is an example format that does nothing.
        It will never indicate that it can read or save a file. When
        explicitly asked to read, it will simply read the bytes. When 
        explicitly asked to save, it will raise an error.
        """
        
        def _can_read(self, request):
            # The request object has:
            # request.filename: the filename
            # request.firstbytes: the first 256 bytes of the file.
            # request.expect: what kind of data the user expects
            # request.kwargs: the keyword arguments specified by the user
            return False
        
        def _can_save(self, request):
            return False
        
        
        class Reader(Format.Reader):
        
            def _open(self):
                self._fp = self.request.get_file()
            
            def _close(self):
                pass  # The request object will close the file
            
            def _get_length(self):
                return 1
            
            def _get_data(self, index):
                if index != 0:
                    raise IndexError('The dummy format only supports singleton images.')
                # Read all bytes
                data = self._fp.read()
                # Put in a numpy array
                im = np.frombuffer(data, 'uint8')
                im.shape = len(im), 1
                # Return array and dummy meta data
                return im, {}
            
            def _get_meta_data(self, index):
                raise RuntimeError('The dymmy format cannot read meta data.')
            
            def _get_next_data(self):
                # Optional. Formats can implement this to support reading the
                # images as a stream. If not implemented, imageio will ask for
                # the length and use _get_data() to get the images.
                raise NotImplementedError()  
        
        
        class Writer(Format.Writer):
            
            def _open(self, flags=0):        
                pass
            
            def _close(self):
                pass
            
            def _append_data(self, im, meta):    
                raise RuntimeError('The dymmy format cannot save image data.')
            
            def set_meta_data(self, meta):
                raise RuntimeError('The dymmy format cannot save meta data.')
    
    
    # Register. You register an *instance* of a Format class.
    format = DummyFormat('dummy', 'An example format that does nothing.')
    formats.add_format(format)
