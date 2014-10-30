# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Example plugin. You can use this as a template for your own plugin.
"""

from __future__ import absolute_import, print_function, division

import numpy as np

from imageio import formats
from imageio.core import Format


class DummyFormat(Format):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or save a file. When
    explicitly asked to read, it will simply read the bytes. When 
    explicitly asked to save, it will raise an error.
    
    This documentation is shown when the user does ``help('thisformat')``.
    
    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.
    
    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.
    
    """
    
    def _can_read(self, request):
        # The request object has:
        # request.filename: a representation of the source (only for reporing)
        # request.firstbytes: the first 256 bytes of the file.
        # request.mode[0]: read or write mode
        # request.mode[1]: what kind of data the user expects: one of 'iIvV?'
        return False
    
    def _can_save(self, request):
        return False
    
    # -- reader
    
    class Reader(Format.Reader):
    
        def _open(self, some_option=False):
            # Process kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to get access to the
            # data. Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            self._fp = self.request.get_file()
        
        def _close(self):
            # Close the reader. 
            # Note that the request object will close self._fp
            pass
        
        def _get_length(self):
            # Return the number of images. Can be np.inf
            return 1
        
        def _get_data(self, index):
            # Return the data for the given index
            if index != 0:
                raise IndexError('Dummy format only supports singleton images')
            # Read all bytes
            data = self._fp.read()
            # Put in a numpy array
            im = np.frombuffer(data, 'uint8')
            im.shape = len(im), 1
            # Return array and dummy meta data
            return im, {}
        
        def _get_meta_data(self, index):
            # Get the meta data for the given index
            raise RuntimeError('The dummy format cannot read meta data.')
    
    # -- writer
    
    class Writer(Format.Writer):
        
        def _open(self, flags=0):        
            # Process kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to write the data.
            # Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            self._fp = self.request.get_file()
        
        def _close(self):
            # Close the reader. 
            # Note that the request object will close self._fp
            pass
        
        def _append_data(self, im, meta):
            # Process the given data and meta data.
            raise RuntimeError('The dummy format cannot save image data.')
        
        def set_meta_data(self, meta):
            # Process the given meta data (global for all images)
            # It is not mandatory to support this.
            raise RuntimeError('The dummy format cannot save meta data.')


# Register. You register an *instance* of a Format class. Here specify:
format = DummyFormat('dummy',  # shot name
                     'An example format that does nothing.',  # one line descr.
                     '',  # list of extensions as a space separated string
                     ''  # modes, characters in iIvV
                     )
formats.add_format(format)
