# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images. It is written 
in pure Python (2.x and 3.x) and most functionality is obtained
by wrapping the FreeImage library using ctypes. The imageio 
projected is intended as a replacement for PIL.

Four functions are exposed:
  * imread() - to read an image file and return a numpy array
  * imwrite() - to write a numpy array to an image file
  * movieread() - (name may change) to read animated image data as a list of numpy arrays
  * moviewrite() - (name may change) to write a list of numpy array to an animated image

Further, via the module imageio.freeimage part of the FreeImage library 
is exposed.

Well this is the idea anyway. We're still developing :)

"""

__version__ = '0.1'
import sys

# Try to load freeimage wrapper
import imageio.freeimage
try:
    fi = imageio.freeimage.Freeimage()
except OSError:
    print('Warning: the freeimage wrapper of imageio could not be loaded:')
    e_type, e_value, e_tb = sys.exc_info(); del e_tb
    print(str(e_value))
    fi = None

# todo: temporary solution until we have implemented plugins
def imread(*args, **kwargs):
    if fi is None:
        raise ValueError('Freeimage not available')
    return fi.read(*args, **kwargs)

def imsave(*args, **kwargs):
    if fi is None:
        raise ValueError('Freeimage not available')
    return fi.write(*args, **kwargs)

imwrite =imsave # provide alias for interoperability with e.g. the imread package

# Clean up some names
del sys
