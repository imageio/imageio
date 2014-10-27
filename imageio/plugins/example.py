# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Example plugin. You can use this as a template for your own plugin.
"""

from imageio import formats
from imageio.core import Format
import numpy as np


class DummyFormat(Format):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or save a file. When
    explicitly asked to read, it will simply read the bytes. When 
    explicitly asked to save, it will raise an error.
    
    This documentation is shown when the user does ``help('thisformat')``.
    
    Keyword arguments for reading
    -----------------------------
    Specify arguments in numpy doc style here.
    
    Keyword arguments for writing
    -----------------------------
    Specify arguments in numpy doc style here.
    
    """
    
    def _can_read(self, request):
        # The request object has:
        # request.filename: a representation of the source (only for reporing)
        # request.firstbytes: the first 256 bytes of the file.
        # request.mode[0]: read or write mode
        # request.mode[1]: what kind of data the user expects: one of 'iIvV?'
        
        # These lines are used in testing
        if request.kwargs.get('dummy_potential', False):
            request.add_potential_format(self)
        if request.kwargs.get('dummy_can', False):
            return True
        
        return False
    
    def _can_save(self, request):
        # These lines are used in testing
        if request.kwargs.get('dummy_potential', False):
            request.add_potential_format(self)
        if request.kwargs.get('dummy_can', False):
            return True
        
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
        
        def _get_next_data(self):
            # Optional. Formats can implement this to support reading the
            # images as a stream. If not implemented, imageio will ask for
            # the length and use _get_data() to get the images.
            raise NotImplementedError()  
    
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
# - name
# - short description
# - list of extensions (can be a space or comma separated string)
format = DummyFormat('dummy', 'An example format that does nothing.', '')
formats.add_format(format)


if __name__ == '__main__':
    import imageio
    #fname = 'C:/almar/projects/pylib/visvis/visvisResources/lena.png'
    fname = '/home/almar/projects/pylib/visvis/visvisResources/lena.png'
    
    im = imageio.imread(fname, 'dummy')  # Explicitly use this format
    print(im.shape)  # (473831, 1)
    imageio.imsave(fname, im, 'dummy')  # Raises error
