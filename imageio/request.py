# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
Definition of the Request object, which acts as a kind of bridge between
what the user wants and what the plugins can.
"""

import sys
import os
from io import BytesIO
import zipfile
import tempfile
import shutil

from imageio.base import string_types, text_type, binary_type

# URI types
URI_BYTES = 1
URI_FILE = 2
URI_FILENAME = 3
URI_ZIPPED = 4
URI_HTTP = 5
URI_FTP = 6


# The user can use this string in a write call to get the data back as bytes.
RETURN_BYTES = '<bytes>'


class Request(object):
    """ ReadRequest(uri, expect, **kwargs)
    
    Represents a request for reading or saving a file. This object wraps
    information to that request and acts as an interface for the plugins
    to several resources; it allows the user to read from http, zipfiles,
    raw bytes, etc., but offer a simple interface to the plugins:
    get_file() and get_local_filename().
    
    Per read/save operation a single Request instance is used and passed
    to the can_read/can_save method of a format, and subsequently to the
    Reader/Writer class. This allows rudimentary passing of information
    between different formats and between a format and its reader/writer.
    
    """
    
    def __init__(self, uri, expect, **kwargs):
        
        # General        
        self._uri_type = None
        self._filename = None
        self._expect = expect
        self._kwargs = kwargs
        self._result = None         # Some write actions may have a result
        
        # To handle the user-side
        self._filename_zip = None   # not None if a zipfile is used
        self._bytes = None          # Incoming bytes
        self._zipfile = None        # To store a zipfile instance (if applicable)
        
        # To handle the plugin side
        self._file = None               # To store the file instance
        self._filename_local = None     # not None if we are using a temp file on the local FS
        self._firstbytes = None         # For easy header parsing
        
        # To store formats that may be able to fulfil this request
        self._potential_formats = []
        
        # Parse what was given
        self._parse_uri(uri)
    
    
    def _parse_uri(self, uri):
        """ Try to figure our what we were given
        """
        py3k = sys.version_info[0] == 3
        
        if isinstance(uri, string_types):
            # Explicit
            if uri.startswith('http://') or uri.startswith('https://'):
                self._uri_type = URI_HTTP
                self._filename = uri
            elif uri.startswith('ftp://') or uri.startswith('ftps://'):
                self._uri_type = URI_FTP
                self._filename = uri
            elif uri.startswith('file://'):
                self._uri_type = URI_FILENAME
                self._filename = uri[7:]
            elif uri.startswith('<video') and isinstance(self, ReadRequest):
                self._uri_type = URI_BYTES
                self._filename = uri
            elif uri == RETURN_BYTES and isinstance(self, WriteRequest):
                self._uri_type = URI_BYTES
                self._filename = '<bytes>'
            # Less explicit (particularly on py 2.x)
            elif py3k:
                self._uri_type = URI_FILENAME
                self._filename = uri
            else:
                try:
                    isfile = os.path.isfile(uri)
                except Exception:
                    isfile = False  # If checking does not even work ...
                if isfile:
                    self._uri_type = URI_FILENAME
                    self._filename = uri
                elif len(uri) < 256: # Can go wrong with veeery tiny images
                    self._uri_type = URI_FILENAME
                    self._filename = uri
                elif isinstance(uri, binary_type) and isinstance(self, ReadRequest):
                    self._uri_type = URI_BYTES
                    self._filename = '<bytes>'
                    self._bytes = uri
                else:
                    self._uri_type = URI_FILENAME
                    self._filename = uri
        elif py3k and isinstance(uri, binary_type) and isinstance(self, ReadRequest):
            self._uri_type = URI_BYTES
            self._filename = '<bytes>'
            self._bytes = uri
        # Files
        elif isinstance(self, ReadRequest):
            if hasattr(uri, 'read') and hasattr(uri, 'close'):
                self._uri_type = URI_FILE
                self._filename = '<file>'
                self._file = uri
        elif isinstance(self, WriteRequest):
            if hasattr(uri, 'write') and hasattr(uri, 'close'):
                self._uri_type = URI_FILE
                self._filename = '<file>'
                self._file = uri
        
        # Check if a zipfile
        if self._uri_type == URI_FILENAME:
            # Search for zip extension followed by a path separater
            for needle in ['.zip/', '.zip\\']:
                zip_i = self._filename.lower().find(needle)
                if zip_i > 0:                    
                    zip_i += 4
                    self._uri_type = URI_ZIPPED
                    self._filename_zip = (  self._filename[:zip_i], 
                                    self._filename[zip_i:].lstrip('/\\') )
                    break
        
        # Check if we could read it
        if self._uri_type is None:
            uri_r = repr(uri)
            if len(uri_r) > 60:
                uri_r = uri_r[:57]+ '...'
            raise IOError("Cannot understand given URI: %s." % uri_r)
        
        # Check if this is supported
        noWriting = [URI_HTTP, URI_FTP]
        if isinstance(self, WriteRequest) and self._uri_type in noWriting:
            raise RuntimeError('imageio does not support writing to http/ftp.')
        
        # Check if file exists
        if isinstance(self, ReadRequest):
            if self._uri_type in [URI_FILENAME, URI_ZIPPED]:
                fn = self._filename_zip[0] if self._filename_zip else self._filename
                if not os.path.exists(fn):
                    raise IOError("No such file: '%s'" % fn)
    
    
    @property
    def filename(self):
        """ Get the uri for which reading/saving was requested. This
        can be a filename, an http address, or other resource
        identifier. Do not rely on the filename to obtain the data,
        but use the get_file() or get_local_filename() instead.
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
    
    
    ## For obtaining data
    
    
    def get_file(self):
        """ get_file()
        Get a file object for the resource associated with this request.
        If this is a reading request, the file is in read mode,
        otherwise in write mode. This method is not thread safe. Plugins
        do not need to close the file when done.
        
        This is the preferred way to read/write the data. If a format
        cannot handle file-like objects, they should use get_local_filename().
        """
        want_to_write = isinstance(self, WriteRequest)
        
        #if self._uri_type == URI_FILE:
        if self._file is not None:
            self._file.seek(0)
            return self._file
        
        if self._uri_type == URI_BYTES:
            if want_to_write:                          
                self._file = BytesIO()
            else:
                self._file = BytesIO(self._bytes)
        
        elif self._uri_type == URI_FILENAME:
            if want_to_write:
                self._file = open(self.filename, 'wb')
            else:
                self._file = open(self.filename, 'rb')
        
        elif self._uri_type == URI_ZIPPED:
            # Get the correct filename
            filename, name = self._filename_zip
            if want_to_write:
                # Create new file object, we catch the bytes in finish()
                self._file = BytesIO()
            else:
                # Open zipfile and open new file object for specific file
                self._zipfile = zipfile.ZipFile(filename, 'r')
                self._file = self._zipfile.open(name, 'r')
        
        elif self._uri_type in [URI_HTTP or URI_FTP]:
            if want_to_write:
                raise RuntimeError('imageio does not support writing to http/ftp.')
            else:
                self._file = compat_urlopen(self.filename, timeout=20)
        
        return self._file
    
    
    def get_local_filename(self):
        """ get_local_filename()
        If the filename is an existing file on this filesystem, return
        that. Otherwise a temporary file is created on the local file
        system which can be used by the format to read from or write to.
        """
        
        if self._uri_type == URI_FILENAME:
            return self._filename
        else:
            # Get filename
            ext = os.path.splitext(self._filename)[1]
            self._filename_local = tempfile.mktemp(ext, 'imageio_')
            # Write stuff to it?
            if isinstance(self, ReadRequest):
                with open(self._filename_local, 'wb') as file:
                    shutil.copyfileobj(self.get_file(), file)
            return self._filename_local
    
    
    def finish(self):
        """ finish()
        For internal use (called when the context of the reader/writer
        exists). Finishes this request. Close open files and process
        results.
        """
        
        # Init
        bytes = None
        
        # Collect bytes from temp file
        if isinstance(self, WriteRequest) and self._filename_local:
            bytes = open(self._filename_local, 'rb').read()
        
        # Collect bytes from BytesIO file object.
        written = isinstance(self, WriteRequest) and self._file
        if written and self._uri_type in [URI_BYTES, URI_ZIPPED]:
            bytes = self._file.getvalue()
        
        # Close open files that we know of (and are responsible for)
        if self._file and self._uri_type != URI_FILE:
            self._file.close()
            self._file = None
        if self._zipfile:
            self._zipfile.close()
            self._zipfile = None
        # Remove temp file
        if self._filename_local:
            try:
                os.remove(self._filename_local)
            except Exception:
                pass
            self._filename_local = None
        
        # Handle bytes that we collected
        if bytes is not None:
            if self._uri_type == URI_BYTES:
                self._result = bytes  # Picked up by imread function
            elif self._uri_type == URI_ZIPPED:
                zf = zipfile.ZipFile(self._filename_zip[0], 'a')
                zf.writestr(self._filename_zip[1], bytes)
                zf.close()
        
        # Detach so gc can clean even if a reference of self lingers
        self._bytes = None
    
    
    def get_result(self):
        """ For internal use. In some situations a write action can have
        a result (bytes data). That is obtained with this function.
        """
        self._result, res = None, self._result
        return res
    
    
    @property
    def firstbytes(self):
        """ Get the first 256 bytes of the file. This can be used to 
        parse the header to determine the file-format.
        """
        if self._firstbytes is None:
            self._read_first_bytes()
        return self._firstbytes
    
    def _read_first_bytes(self, N=256):
        if self._bytes is not None:
            self._firstbytes = self._bytes[:N]
        else:
            # Prepare
            if self._file is None:
                self.get_file()
            i = self._file.tell()
            # Read
            first_bytes = binary_type()
            while len(first_bytes) < N:
                extra_bytes = self._file.read(N-len(first_bytes))
                if not extra_bytes:
                    break
                first_bytes += extra_bytes
            self._firstbytes = first_bytes
            # Set back
            self._file.seek(i)
    
    
    ## For formats
    
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
            return self._potential_formats.pop(0)
        else:
            return None
    


class ReadRequest(Request):
    pass

class WriteRequest(Request):
    pass



def compat_urlopen(*args, **kwargs):
    """ Compatibility function for the urlopen function.
    """ 
    try:
        from urllib2 import urlopen
    except ImportError:
        try:
            from urllib.request import urlopen # Py3k
        except ImportError:
            urlopen = None 
    
    if urlopen is None:
        raise RuntimeError('Could not import urlopen.')
    else:
        return urlopen(*args, **kwargs)

