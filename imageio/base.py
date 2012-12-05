# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 

.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes will probably change. We'll have to
    implement a few more plugins to see what works well and what not.

These are the main classes of imageio. They expose an interface for
advanced users and plugin developers. A brief overview:
  
  * imageio.FormatManager - for keeping track of registered formats.
  * imageio.Format - the thing that says it can read/save a certain file.
    Has a reader and writer class asociated with it.
  * imageio.Reader - object used during the reading of a file.
  * imageio.Writer - object used during saving a file.
  * imageio.Request - used to store the filename and other info.

Plugins need to implement a Reader, Writer and Format class and register
a format object using ``imageio.formats.add_format()``.

"""

# Some notes:
#
# The classes in this module use the Request object to pass filename and
# related info around. This request object is instantiated in imageio.read
# and imageio.save.
#
# The classes in this module do not do any input checking. This is done by
# imageio.read and imageio.save
#
# We use the verbs read and save throughout imageio. However, for the 
# associated classes we use the nouns "reader" and "writer", since 
# "saver" feels so awkward. 

from __future__ import with_statement

import sys
import os

# Define expects
EXPECT_IM = 0
EXPECT_MIM = 1
EXPECT_VOL = 2
EXPECT_MVOL = 3


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



class Request(object):
    """ Request(filename, expect, **kwargs)
    
    Represents a request for reading or saving a file. This object wraps
    information to that request.
    
    Per read/save operation a single Request instance is used and passed
    to the can_read/can_save method of a format, and subsequently to the
    Reader/Writer class. This allows some rudimentary passing of 
    information between different formats and between a format and its 
    reader/writer.
    
    """
    
    def __init__(self, filename, expect, **kwargs):
        self._filename = filename
        self._expect = expect
        self._kwargs = kwargs
        self._firstbytes = None
        
        self._potential_formats = []
    
    @property
    def filename(self):
        """ Get the filename for which reading/saving was requested.
        """
        return self._filename
    
    @property
    def expect(self):
        """ Get what kind of data was expected for reading. 
        See the imageio.EXPECT_* constants.
        """
        return self._expect
    
    @property
    def kwargs(self):
        """ Get the dict of keyword arguments supplied by the user.
        """
        return self._kwargs
    
    @property
    def firstbytes(self):
        """ Get the first 256 bytes of the file. This can be used to 
        parse the header to determine the file-format.
        """
        if self._firstbytes is None:
            self._firstbytes = self._read_first_bytes()
        return self._firstbytes
    
    def _read_first_bytes(self, N=256):
        f = open(self.filename, 'rb')
        first_bytes = binary_type()
        while len(first_bytes) < N:
            extra_bytes = f.read(N-len(first_bytes))
            if not extra_bytes:
                break
            first_bytes += extra_bytes
        f.close()
        return first_bytes
    
    # This is a bit experimental. Not sure how useful it will be in practice.
    # One use case I though of is that if there is a bug in FreeImage, we might
    # be able to circumvent it by providing an alternative Format for that
    # file-format.
    def add_potential_format(self, format):
        """ add_potential_format(format)
        
        Allows a format to add itself as a potential format in cases
        where it seems capable of reading-saving the file, but 
        priority should be given to another Format.
        """
        self._potential_formats.append(format)
    
    def get_potential_format(self):
        """ get_potential_format()
        
        Get the first known potential format. Calling this method 
        repeatedly will yield different formats until the list of 
        potential formats is exhausted.
        """
        if self._potential_formats:
            format = self._potential_formats.pop(0)
        return format



class Format:
    """ 
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
    
    """
    
    # todo: maybe it is sometimes enough to only specify the extensions.
    
    def __init__(self, name, description, extensions=None):
        
        # Store name and description
        self._name = name.upper()
        self._description = description
        
        # Store extensions, do some effort to normalize them.
        # They are stores as a list of lowercas strings without leading dots.
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
        return '%s - %s\n\n%s' % (self.name, self.description, self.__doc__)
    
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
        """
        return self._extensions
    
    def read(self, request):
        """ read(request)
        
        Return a reader object that can be used to read data and info
        from the given file. Used internally. Users are encouraged to
        use imageio.read() instead.
        """
        return self._get_reader_class()(request)
    
    def save(self, request):
        """ save(request)
        
        Return a writer object that can be used to save data and info
        to the given file. Used internally. Users are encouraged to
        use imageio.save() instead.
        """
        return self._get_writer_class()(request)
    
    def can_read(self, request):
        """ can_read(request)
        
        Get whether this format can read data from the specified file.
        """
        return self._can_read(request)
    
    def can_save(self, request):
        """ can_save(request)
        
        Get whether this format can save data to the speciefed file.
        """
        return self._can_save(request)
    
    
    def _get_reader_class(self):
        return Reader # Plugins should implement this
    
    def _get_writer_class(self):
        return Writer # Plugins should implement this
    
    def _can_read(self, request):
        return None # Plugins should implement this
    
    def _can_save(self, request):
        return None # Plugins should implement this



class BaseReaderWriter(object):
    """ Base class for the Reader and Writer class to implement common 
    functionality.
    """
    
    def __init__(self, request):
        self._request = request
    
    @property
    def request(self):
        """ Get the request object corresponding to the current read/save 
        operation.
        """
        return self._request
    
    def init(self):
        """ Initialize the reader/writer. Note that the recommended usage
        of reader/writer objects is to use them in a "with-statement".
        """
        self._init()
    
    def close(self):
        """ Close this reader/writer. Note that the recommended usage
        of reader/writer objects is to use them in a "with-statement".
        """
        self._close()
    
    def __del__(self):
        self._close()
    
    def __enter__(self):
        self._init()
        return self
    
    def __exit__(self, *args):
        self._close()
    
    def _init(self):
        pass # Plugins can implement this
    
    def _close(self):
        pass # Plugins can implement this


class Reader(BaseReaderWriter):
    """
    A reader is an object that is instantiated for reading data from
    an image file. A reader can be used as an iterator, and only reads
    data from the file when new data is requested. The reading should
    finish by calling close().
    
    Plugins should overload a couple of methods to implement a reader. 
    A plugin may also specify extra methods to expose an interface
    specific for the file-format it exposes.
    
    A reader object should be obtained by calling imageio.read() or
    by calling the read() method on a format object.
    
    """
    
    def read_data(self, *indices, **kwargs):
        """ read_data(*indices, **kwargs)
        
        Read data from the file. If appropriate, indices can be given.
        The keyword arguments are merged with the keyword arguments
        specified in the read() function.
        
        """
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._read_data(*indices, **D)
    
    def read_info(self, *indices, **kwargs):
        """ read_info(*indices, **kwargs)
        
        Read info (i.e. meta data) from the file. If appropriate, indices 
        can be given. The keyword arguments are merged with the keyword 
        arguments specified in the read() function.
        
        """
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._read_info(*indices, **D)
    
    def __len__(self):
        p = 1
        for s in self._mshape():
            p *= s
        return s
    
    # todo: allow a format to specify that the length is unknown?
    # e.g. video
    # in that case: iterate not over length, but until we can
    def __iter__(self):
        i = 0
        while i < len(self):
            yield self.read_data(i)
            i += 1
    
    def _mshape(self):
        raise NotImplemented() # Plugins should implement this
    
    def _read_data(self, *indices, **kwargs):
        raise NotImplemented() # Plugins should implement this
    
    def _read_info(self, *indices, **kwargs):
        raise NotImplemented() # Plugins should implement this



class Writer(BaseReaderWriter):
    """ 
    A writer is an object that is instantiated for saving data to
    an image file. A writer enables writing different parts separately.
    The writing should be flushed by using close().
    
    Plugins should overload a couple of methods to implement a writer. 
    A plugin may also specify extra methods to expose an interface
    specific for the file-format it exposes.
    
    A writer object should be obtained by calling imageio.save() or
    by calling the save() method on a format object.
    
    """
    
    # todo: I can imagine that plugins often want to directly overload this
    # method to be able to give it a proper docstring.
    def save_data(self, data, *indices, **kwargs):
        """ save_data(*indices, **kwargs)
        
        Save image data to the file. If appropriate, indices can be given.
        The keyword arguments are merged with the keyword arguments
        specified in the save() function.
        
        """
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._save_data(data, *indices, **D)
    
    def save_info(self, info, *indices, **kwargs):
        """ save_info(*indices, **kwargs)
        
        Save info (i.e. meta data) to the file. If appropriate, indices can 
        be given. The keyword arguments are merged with the keyword arguments
        specified in the save() function.
        
        """
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._save_info(info, *indices, **D)
    
    
    def _save_data(self, data, *indices, **kwargs):
        raise NotImplemented() # Plugins should implement this
    
    def _save_info(self, info, *indices, **kwargs):
        raise NotImplemented() # Plugins should implement this



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
