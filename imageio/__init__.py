# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

Main website: http://imageio.github.io

Quickstart:

* Use :func:`.imread` to read an image.
* Use :func:`.imsave` to save an image.
* See :doc:`userapi` for more information.

"""

__version__ = '0.5.1dev'

# Load some bits from core
from .core import FormatManager, RETURN_BYTES  # noqa

# Instantiate format manager
formats = FormatManager()

# Load the functions
from .core.functions import help  # noqa
from .core.functions import read, imread, mimread, volread, mvolread  # noqa
from .core.functions import save, imsave, mimsave, volsave, mvolsave  # noqa

# Load all the plugins
from . import plugins  # noqa

# Clean up some names
del FormatManager
