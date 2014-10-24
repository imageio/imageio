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
  * See the :ref:`functions page <sec-functions>` for more information.
 
"""

__version__ = '0.5.1dev'

# Load some bits from core
from .core import FormatManager, RETURN_BYTES  # noqa
from .core import EXPECT_IM, EXPECT_MIM, EXPECT_VOL, EXPECT_MVOL  # noqa

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
