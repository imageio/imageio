# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

Imageio has a relatively simple core that provides a common interface
to different file formats. The actual file formats are implemented in
plugins, which makes imageio easy to extend. A large range of formats
are already supported (in part thanks to the freeimage library), but
we aim to include much more (scientific) formats in the future.

Quickstart:

  * Use imageio.imread to read an image.
  * Use imageio.imsave to save an image.
  * See the `functions page <http://imageio.readthedocs.org/en/latest/functions.html>`_ for more information.
 
"""

__version__ = '0.5'

import sys

# Explicitly import these
import imageio.findlib 
import imageio.freeze 

# Load some utils in this namespace
from imageio.util import Image

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
from imageio.base import Format, FormatManager
from imageio.request import Request, RETURN_BYTES
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

