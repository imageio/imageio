# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Example plugin.
"""

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




if __name__ == '__main__':
    import imageio
    #fname = 'C:/almar/projects/pylib/visvis/visvisResources/lena.png'
    fname = '/home/almar/projects/pylib/visvis/visvisResources/lena.png'
    
    im = imageio.imread(fname, 'dummy') # Explicitly use this format
    print(im.shape) # (473831, 1)
    imageio.imsave(fname, im, 'dummy') # Raises error
