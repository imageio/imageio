# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" imageio.base

This module defines the main classes of imageio. A brief overview:
  
  * Request - used to store the filename and other info.
  * Reader - Object used during the reading of a file.
  * Writer - Object used during saving a file.
  * Format - The thing that says it can read/save a certain file.
    Has a reader and writer class asociated with it.
  * FormatManager - For keeping track of registered formats.

Plugins need to implement a Reader, Writer and Format class and register
the format using imageio.formats.add_format().
    
"""

from __future__ import with_statement

import sys

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



class Request:
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
        return self._filename
    
    @property
    def expect(self):
        return self._expect
    
    @property
    def kwargs(self):
        return self._kwargs
    
    @property
    def firstbytes(self):
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
    
    def add_potential_format(self, format):
        self._potential_formats.append(format)
    
    def get_potential_format(self):
        if self._potential_formats:
            format = self._potential_formats.pop(0)
        return format



class BaseReaderWriter:
    """ Base class for the Reader and Writer class to implement common 
    functionality.
    """
    
    def __init__(self, request):
        self._request = request
    
    @property
    def request(self):
        return self._request
    
    def close(self):
        self._close()
    
    def __del__(self):
        self.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def _close(self):
        pass # Implement this


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
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._read_data(*indices, **D)
    
    def read_info(self, *indices, **kwargs):
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
     
    def __iter__(self):
        i = 0
        while i < len(self):
            yield self.read_data(i)
            i += 1
    
    def _mshape(self):
        raise NotImplemented()
    
    def _read_data(self, *indices, **kwargs):
        raise NotImplemented()
    
    def _read_info(self, *indices, **kwargs):
        raise NotImplemented()



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
    
    def save_data(self, data, *indices, **kwargs):
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._save_data(data, *indices, **D)
    
    def save_info(self, info, *indices, **kwargs):
        D = self.request.kwargs.copy()
        D.update(kwargs)
        return self._save_info(info, *indices, **D)
    
    def __len__(self):
        p = 1
        for s in self._mshape():
            p *= s
        return s
    
    
    def _save_data(self, data, *indices, **kwargs):
        raise NotImplemented()
    
    def _save_info(self, info, *indices, **kwargs):
        raise NotImplemented()


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
    
    To implement a specific format, see the docs for the plugins.
    
    """
    
    # Refs to standard docs
    _readerClass = Reader
    _writerClass = Writer
     
    # todo: maybe it is sometimes enough to only specify the extensions.
    
    def __init__(self, name, description, extensions=None):
        
        # Store name and description
        self._name = name.upper()
        self._description = description
        
        # Store extensions, do some effort to normalize them.
        # They are stores as a list of lowercas strings without leading dots.
        if extensions is None:
            extentions = []
        elif isinstance(extensions, string_types):
            extensions = extensions.replace(',', ' ').split(' ')
        #
        if isinstance(extensions, (tuple, list)):
            self._extensions = [e.strip('.').lower() for e in extensions if e]
        else:
            raise ValueError('Invalid value for extensions given.')
        
    
    def __repr__(self):
        return '<Format %s - %s>' % (self.name, self.description)
    
    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    @property
    def long_description(self):
        return self.__doc__
    
    @property
    def extensions(self):
        """ Return a list of file extensions supported by this plugin.
        """
        return self._extensions
    
    
    def read(self, filename, expect=None, **kwargs):
        if isinstance(filename, Request):
            request = filename
        else:
            request = Request(filename, expect, **kwargs)
        return self._readerClass(request)
    
    def save(self, filename, expect=None, **kwargs):
        if isinstance(filename, Request):
            request = filename
        else:
            request = Request(filename, expect, **kwargs)
        return self._writerClass(request)
    
    def can_read(self, request):
        return self._can_read(request)
    
    def can_save(self, request):
        return self._can_save(request)
    
    def _can_read(self, request):
        return None
    
    def _can_save(self, request):
        return None



class FormatManager:
    """ 
    The format manager keeps track of the registered formats and can be used
    to list all formats, to select a certain format based on its name, 
    or to search for a format using a request object.
    
    There is exactly one FormatManager object in imageio: imageio.formats.
    """
    
    def __init__(self):
        self._formats = []
    
    def __repr__(self):
        return '<imageio.FormatManager with %i registered formats>' % len(self._formats)
    
    def add_format(self, format):
        if isinstance(format, Format):
            self._formats.append(format)
        else:
            raise ValueError('add_format needs argument to be a Format instance.')
    
    def formats(self):
        return [f for f in self._formats]
    
    def print_formats(self):
        for format in self._formats: 
            ext = ', '.join(format.extensions)
            s = '%s - %s [%s]' % (format.name, format.description, ext)
            print(s)
    
    def docs(self, name):
        format = self[name]
        doc = '%s - %s\n' % (format.name, format.description)
        return doc + format.__doc__
    
    def print_docs(self, name):
        print(self.docs(name))
    
    def __getitem__(self, name):
        
        # Check and correct name
        if not isinstance(name, string_types):
            raise ValueError('Looking up a format should be done by name or extension.')
        elif name.startswith('.'):
            # Look for extension
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
        
        # Nothing found ...
        raise IndexError('No format known by name %s.' % name)
    
    def search_read_format(self, request):
        for format in self._formats:
            if format.can_read(request):
                return format
        else:
            return request.get_potential_format()
    
    def search_save_format(self, request):
        for format in self._formats:
            if format.can_save(request):
                return format
        else:
            return request.get_potential_format()
    