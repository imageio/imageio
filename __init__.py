# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

For images, four convenience functions are exposed:
  * imageio.imread - to read an image file and return a numpy array
  * imageio.imsave - to write a numpy array to an image file
  * imageio.mimread - to read animated image data as a list of numpy arrays
  * imageio.mimsave - to write a list of numpy array to an animated image

Similarly, for volumes imageio provides volread, volsave, mvolread and mvolsave.

For a larger degree of control, imageio provides the functions 
imageio.read and imageio.save. They respectively return a imageio.Reader and a
imageio.Writer object, which can be used to read/save data and meta data in a
more controlled manner. This also allows specific scientific formats to
be exposed in a way that best suits that file-format.

To get a list of supported formats and documentation for a certain format, 
use the ``help`` method of the ``imageio.formats`` object (see the 
imageio.FormatManager
class).

The imageio library is intended as a replacement for PIL. Currently, most
functionality is obtained by wrapping the FreeImage library using ctypes. 

"""

# todo: test images at: http://sourceforge.net/projects/freeimage/files/
# todo: make libs work when frozen - dont try to download when frozen!

__version__ = '0.2'

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

# Load root plugin and insert some of its functions in this namesplace
from imageio.base import Request, Format, Reader, Writer, FormatManager
from imageio.base import EXPECT_IM, EXPECT_MIM, EXPECT_VOL, EXPECT_MVOL

# Instantiate format manager
formats = FormatManager()

# Load all the plugins
import imageio.plugins

# Load the functions
from imageio.functions import read, imread, mimread, volread, mvolread
from imageio.functions import save, imsave, mimsave, volsave, mvolsave

# Clean up some names
del sys

