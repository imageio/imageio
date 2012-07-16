# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

The imageio library is intended as a replacement for PIL. Currently, most
functionality is obtained by wrapping the FreeImage library using ctypes. 

Quickstart:

  * Use imageio.imread to read an image
  * Use imageio.imsave to save an image
  * See the `functions page <http://imageio.readthedocs.org/en/latest/functions.html>`_ for more information.
 
"""

# todo: test images at: http://sourceforge.net/projects/freeimage/files/

__version__ = '0.2.2'

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
from imageio.functions import help
from imageio.functions import read, imread, mimread, volread, mvolread
from imageio.functions import save, imsave, mimsave, volsave, mvolsave

# Clean up some names
del sys

