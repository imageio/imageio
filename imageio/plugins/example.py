# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Example plugin.
"""

from imageio import formats
from imageio import base
import numpy as np


class DummyFormat(base.Format):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or save a file. When
    explicitly asked to read, it will simply read the bytes. When 
    explicitly asked to save, it will raise an error.
    """
    
    def _can_read(request):
        # The request object has:
        # request.filename: the filename
        # request.firstbytes: the first 256 bytes of the file.
        # request.expect: what kind of data the user expects
        # request.kwargs: the keyword arguments specified by the user
        return False
    
    def _can_save(request):
        return False

    def _get_reader_class(self):
        return Reader
    
    def _get_writer_class(self):
        return Writer 

# Register. You register an *instance* of a Format class, which has
# corresponding Reader and Writer *classes*.
format = DummyFormat('dummy', 'An example format that does nothing.')
formats.add_format(format)


class Reader(base.Reader):
    
    def _init(self):
        self._fp = open(self.request.filename, 'rb')
    
    def _close(self):
        self._fp.close()
    
    def _read_data(self, *indices, **kwargs):
        if indices and indices != (0,):
             raise RuntimeError('The dymmy format only supports reading single images.')
        
        # Read all bytes
        self._fp.seek(0)
        data = self._fp.read()
        
        # Put in a numpy array
        im = np.frombuffer(data, 'uint8')
        im.shape = len(im), 1
        return im
    
    def _read_info(self, *indices, **kwargs):
        raise RuntimeError('The dymmy format cannot read meta data.')


class Writer(base.Writer):
    
    # No need to inplement _init or _close, because we are not opening any files.
    
    def _save_data(self, data, *indices, **kwargs):
        raise RuntimeError('The dymmy format cannot save image data.')
    
    def _save_info(self, info, *indices, **kwargs):
        raise RuntimeError('The dymmy format cannot save meta data.')


if __name__ == '__main__':
    import imageio
    fname = 'C:/almar/projects/py/visvis/visvisResources/lena.png'
    
    im = imageio.imread(fname, 'dummy') # Explicitly use this format
    print(im.shape) # (473831, 1)
    imageio.imsave(fname, im, 'dummy') # Raises error
