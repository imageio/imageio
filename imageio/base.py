# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 

.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes may change. 

These are the main classes of imageio. They expose an interface for
advanced users and plugin developers. A brief overview:
  
  * imageio.FormatManager - for keeping track of registered formats.
  * imageio.Format - representation of a file format reader/writer
  * imageio.Format.Reader - object used during the reading of a file.
  * imageio.Format.Writer - object used during saving a file.
  * imageio.Request - used to store the filename and other info.

Plugins need to implement a Format class and register
a format object using ``imageio.formats.add_format()``.

"""

# Some notes:
#
# The classes in this module use the Request object to pass filename and
# related info around. This request object is instantiated in imageio.read
# and imageio.save.
#
# We use the verbs read and save throughout imageio. However, for the 
# associated classes we use the nouns "reader" and "writer", since 
# "saver" feels so awkward. 

from __future__ import with_statement

import sys
import os

import numpy as np

from imageio.util import Image, ImageList


# Taken from six.py
PY3 = sys.version_info[0] == 3
if PY3:
    string_types = str,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    text_type = unicode
    binary_type = str


# Define expects
# These are like hints, that the plugins can use to better serve the user.
EXPECT_IM = 0
EXPECT_MIM = 1
EXPECT_VOL = 2
EXPECT_MVOL = 3


class Format:
    """ Represents an implementation to read/save a particular file format
    
    A format instance is responsible for 1) providing information about
    a format; 2) determining whether a certain file can be read/saved
    with this format; 3) providing a reader/writer class.
    
    Generally, imageio will select the right format and use that to
    read/save an image. A format can also be explicitly chosen in all
    read/save functios.
    
    Use print(format), or help(format_name) to see its documentation.
    
    To implement a specific format, see the docs for the plugins.
    
    Parameters
    ----------
    name : str
        A short name of this format. Users can select a format using its name.
    description : str
        A one-line description of the format
    extensions : str | list | None
        List of filename extensions that this format supports. If a string
        is passed it should be space or comma separated. Users can select
        a format by specifying the file extension.
    
    """
    
    def __init__(self, name, description, extensions=None):
        
        # Store name and description
        self._name = name.upper()
        self._description = description
        
        # Store extensions, do some effort to normalize them.
        # They are stored as a list of lowercase strings without leading dots.
        if extensions is None:
            extensions = []
        elif isinstance(extensions, string_types):
            extensions = extensions.replace(',', ' ').split(' ')
        #
        if isinstance(extensions, (tuple, list)):
            self._extensions = [e.strip('.').lower() for e in extensions if e]
        else:
            raise ValueError('Invalid value for extensions given.')
        
    def __repr__(self):
        # Short description
        return '<Format %s - %s>' % (self.name, self.description)
    
    def __str__(self):
        return self.doc
    
    @property
    def doc(self):
        """ Get documentation for this format (name + description + docstring).
        """
        # Our docsring is assumed to be indented by four spaces. The
        # first line needs special attention.
        return '%s - %s\n\n    %s\n' % (self.name, self.description, self.__doc__.strip())
    
    @property
    def name(self):
        """ Get the name of this format.
        """
        return self._name
    
    @property
    def description(self):
        """ Get a short description of this format.
        """ 
        return self._description
    
    @property
    def extensions(self):
        """ Get a list of file extensions supported by this plugin.
        These are all lowercase without a leading dot.
        """
        return self._extensions
    
    def read(self, request):
        """ read(request)
        
        Return a reader object that can be used to read data and info
        from the given file. Users are encouraged to use imageio.read() instead.
        """
        return self.Reader(self, request)
    
    def save(self, request):
        """ save(request)
        
        Return a writer object that can be used to save data and info
        to the given file. Users are encouraged to use imageio.save() instead.
        """
        return self.Writer(self, request)
    
    def can_read(self, request):
        """ can_read(request)
        
        Get whether this format can read data from the specified uri.
        """
        return self._can_read(request)
    
    def can_save(self, request):
        """ can_save(request)
        
        Get whether this format can save data to the speciefed uri.
        """
        return self._can_save(request)
    
    
    def _can_read(self, request):
        return None # Plugins must implement this
    
    def _can_save(self, request):
        return None # Plugins must implement this



    class _BaseReaderWriter(object):
        """ Base class for the Reader and Writer class to implement common 
        functionality. It implements a similar approach for opening/closing
        and context management as Python's file objects.
        """
        
        def __init__(self, format, request):
            self.__closed = False
            self._BaseReaderWriter_last_index = -1
            self._format = format
            self._request = request
            # Open the reader/writer
            self._open(**self.request.kwargs.copy())
        
        @property
        def format(self):
            """ Get the format corresponding to the current read/save operation.
            """
            return self._format
        
        @property
        def request(self):
            """ Get the request object corresponding to the current read/save 
            operation.
            """
            return self._request
        
        
        def __enter__(self):
            self._checkClosed()
            return self
        
        def __exit__(self, type, value, traceback):
            if value is None:
                # Otherwise error in close hide the real error.
                self.close() 
        
        def __del__(self):
            try:
                self.close()
            except:
                pass  # Supress noise when called during interpreter shutdown
        
        
        def close(self):
            """Flush and close the reader/writer.
            This method has no effect if it is already closed.
            """
            if self.__closed:
                return
            self.__closed = True
            self._close()
            # Process results and clean request object
            self.request.finish()
        
        @property
        def closed(self):
            """ Get whether the reader/writer is closed.
            """
            return self.__closed
        
        def _checkClosed(self, msg=None):
            """Internal: raise an ValueError if file is closed
            """
            if self.closed:
                what = self.__class__.__name__
                msg = msg or ("I/O operation on closed %s." % what)
                raise ValueError(msg)
        
        
        def _open(self, **kwargs):
            """ _open(**kwargs)
            
            Plugins should probably implement this.
            
            It is called when reader/writer is created. Here the
            plugin can do its initialization. The given keyword arguments
            are those that were given by the user at imageio.read() or
            imageio.write().
            
            """ 
            pass
        
        
        def _close(self):
            """ _close()
            
            Plugins should probably implement this.
            
            It is called when the reader/writer is closed. Here the plugin
            can do a cleanup, flush, etc.
            
            """ 
            pass
    
    
    
    class Reader(_BaseReaderWriter):
        """
        A reader is an object that is instantiated for reading data from
        an image file. A reader can be used as an iterator, and only reads
        data from the file when new data is requested. 
        
        Plugins should overload a couple of methods to implement a reader. 
        A plugin may also specify extra methods to expose an interface
        specific for the file-format it exposes.
        
        A reader object should be obtained by calling imageio.read() or
        by calling the read() method on a format object. A reader can
        be used as a context manager so that it is automatically closed.
        
        """
        
        def get_length(self):
            """ get_length()
            
            Get the number of images in the file. (Note: you can also
            use len(reader_object).)
            
            The result can be:
            * 0 for files that only have meta data
            * 1 for singleton images (e.g. in PNG, JPEG, etc.)
            * N for image series
            * np.inf for streams (series of unknown length)
            
            """ 
            return self._get_length()
        
        
        def get_data(self, index):
            """ get_data(index)
            
            Read image data from the file, using the image index. The
            returned image has a 'meta' attribute with the meta data.
            
            """
            self._BaseReaderWriter_last_index = index
            im, meta = self._get_data(index)
            return Image(im, meta)
        
        
        def get_next_data(self):
            """ get_next_data()
            
            Read the next image from the series.
            
            """
            return self.get_data(self._BaseReaderWriter_last_index+1)
        
        
        def get_meta_data(self, index=None):
            """ get_meta_data(index=None)
            
            Read meta data from the file. using the image index. If the
            index is omitted, return the file's (global) meta data.
            
            Note that get_data also provides the meta data for the returned
            image as an atrribute of that image.
            
            The meta data is a dict that maps group names to subdicts. Each
            group is a dict with name-value pairs. The groups represent the
            different metadata formats (EXIF, XMP, etc.).
            
            """
            return self._get_meta_data(index)
        
        
        def iter_data(self):
            """ iter_data():
            
            Iterate over all images in the series. (Note: you can also
            iterate over the reader object.)
            
            """ 
            
            try:
                # Test one
                im, meta = self._get_next_data()
                yield Image(im, meta)
            
            except NotImplementedError:
                # No luck, but we can still iterate (in a way that allows len==inf)
                i, n = 0, self.get_length()
                while i < n:
                    im, meta = self._get_data(i)
                    yield Image(im, meta)
                    i += 1
            else:
                # Iterate further (untill StopIteration is raised)
                while True:
                    im, meta = self._get_next_data()
                    yield Image(im, meta)
        
        
        # Compatibility
        def __iter__(self):
            return self.iter_data()
        def __len__(self):
            return self.get_length()
        
        
        # The plugin part
        
        def _get_length(self):
            """ _get_length()
            
            Plugins must implement this.
            
            The retured scalar specifies the number of images in the series.
            See Reader.get_length for more information.
            
            """ 
            raise NotImplementedError() 
        
        
        def _get_data(self, index):
            """ _get_data()
            
            Plugins must implement this, but may raise an IndexError in
            case the plugin does not support random access.
            
            It should return the image and meta data: (ndarray, dict).
            
            """ 
            raise NotImplementedError() 
        
        
        def _get_meta_data(self, index):
            """ _get_meta_data(index)
            
            Plugins must implement this. 
            
            It should return the meta data as a dict, corresponding to the
            given index, or to the file's (global) meta data if index is
            None.
            
            """ 
            raise NotImplementedError() 
        
        
        def _get_next_data(self):
            """ _get_next_data()
            
            Plugins can implement this to provide a more efficient way to
            stream images.
            
            It should return the next image and meta data: (ndarray, dict).
            
            """
            raise NotImplementedError() 
    
    
    
    class Writer(_BaseReaderWriter):
        """ 
        A writer is an object that is instantiated for saving data to
        an image file. 
        
        Plugins should overload a couple of methods to implement a writer. 
        A plugin may also specify extra methods to expose an interface
        specific for the file-format it exposes.
        
        A writer object should be obtained by calling imageio.save() or
        by calling the save() method on a format object. A writer can
        be used as a context manager so that it is automatically closed.
        
        """
        
        
        def append_data(self, im, meta=None):
            """ append_data(im, meta={})
            
            Append an image to the file. 
            
            The appended meta data consists of the meta data on the given
            image (if applicable), updated with the given meta data.
            
            """ 
            
            # Check image data
            if not isinstance(im, np.ndarray):
                raise ValueError('append_data accepts a numpy array as first argument.')
            # Get total meta dict
            total_meta = {}
            if hasattr(im, 'meta') and isinstance(im.meta, dict):
                total_meta.update(im.meta)
            if meta is None:
                pass
            elif not isinstance(meta, dict):
                raise ValueError('Meta must be a dict.')
            else:
                total_meta.update(meta)        
            
            # Call
            im = np.asarray(im) # Decouple meta info
            return self._append_data(im, total_meta)
        
        
        def set_meta_data(self, meta):
            """ set_meta_data(meta)
            
            Sets the file's (global) meta data.
            
            The meta data is a dict that maps group names to subdicts. Each
            group is a dict with name-value pairs. The groups represents
            the different metadata formats (EXIF, XMP, etc.). Note that
            some meta formats may not be supported for writing, and even
            individual fields may be ignored if they are invalid.
            
            """ 
            if not isinstance(meta, dict):
                raise ValueError('Meta must be a dict.')
            else:
                return self._set_meta_data(meta)
        
        
        # The plugin part
        
        def _append_data(self, im, meta):
            # Plugins must implement this
            raise NotImplementedError() 
        
        def _set_meta_data(self, meta):
            # Plugins must implement this
            raise NotImplementedError() 



class FormatManager:
    """ 
    The format manager keeps track of the registered formats.
    
    This object supports getting a format object using indexing (by 
    format name or extension). When used as an iterator, this object 
    yields all format objects.
    
    There is exactly one FormatManager object in imageio: ``imageio.formats``.
    
    See also imageio.help.
    """
    
    def __init__(self):
        self._formats = []
    
    def __repr__(self):
        return '<imageio.FormatManager with %i registered formats>' % len(self._formats)
    
    def __iter__(self):
        return iter(self._formats)
    
    def __len__(self):
        return len(self._formats)
    
    def __str__(self):
        ss =  []
        for format in self._formats: 
            ext = ', '.join(format.extensions)
            s = '%s - %s [%s]' % (format.name, format.description, ext)
            ss.append(s)
        return '\n'.join(ss)
    
    def __getitem__(self, name):
        # Check
        if not isinstance(name, string_types):
            raise ValueError('Looking up a format should be done by name or extension.')
        
        # Test if name is existing file
        if os.path.isfile(name):
            format = self.search_read_format(name)
            if format is not None:
                return format
        
        if '.' in name:
            # Look for extension
            e1, e2 =os.path.splitext(name)
            name = e2 or e1
            # Search for format that supports this extension
            name = name.lower()[1:]
            for format in self._formats:
                if name in format.extensions:
                    return format
        else:
            # Look for name
            name = name.upper()
            for format in self._formats:
                if name == format.name:
                    return format
            else:
                # Maybe the user ment to specify an extension
                return self['.'+name.lower()]
        
        # Nothing found ...
        raise IndexError('No format known by name %s.' % name)
    
    def add_format(self, format):
        """ add_formar(format)
        
        Register a format, so that imageio can use it.
        """
        if not isinstance(format, Format):
            raise ValueError('add_format needs argument to be a Format instance.')
        elif format in self._formats:
            raise ValueError('Given Format instance is already registered.')
        else:
            self._formats.append(format)
    
    def search_read_format(self, request):
        """ search_read_format(request)
        
        Search a format that can read a file according to the given request.
        Returns None if no appropriate format was found. (used internally)
        """
        for format in self._formats:
            if format.can_read(request):
                return format
        else:
            return request.get_potential_format()
    
    def search_save_format(self, request):
        """ search_save_format(request)
        
        Search a format that can save a file according to the given request. 
        Returns None if no appropriate format was found. (used internally)
        """
        for format in self._formats:
            if format.can_save(request):
                return format
        else:
            return request.get_potential_format()
    
    def create_docs_for_all_formats(self):
        """ Function to auto-generate documentation for all the formats.
        """
        
        txt = 'List of currently supported formats:'
        
        # Get bullet list of all formats
        ss =  ['']
        for format in self._formats: 
            s = '  * :ref:`%s <%s>` - %s' % (format.name, format.name, format.description)
            ss.append(s)
        txt += '\n'.join(ss) + '\n\n'
        
        # Get more docs for each format
        for format in self._formats:
            title = '%s %s' % (format.name, format.description)
            ext = ', '.join(['``%s``'%e for e in format.extensions])
            ext = ext or 'None'
            #
            txt += '.. _%s:\n\n' % format.name
            txt += '%s\n%s\n\n' % (title, '^'*len(title))
            txt += 'Extensions: %s\n\n' % ext
            txt += format.__doc__  + '\n\n'
        
        # Done
        return txt
