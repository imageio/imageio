# -*- coding: utf-8 -*-
# Copyright (c) 2014-2020, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

# This docstring is used at the index of the documentation pages, and
# gets inserted into a slightly larger description (in setup.py) for
# the page on Pypi:
"""
Imageio is a Python library that provides an easy interface to read and
write a wide range of image data, including animated images, volumetric
data, and scientific formats. It is cross-platform, runs on Python 3.5+,
and is easy to install.

Main website: https://imageio.readthedocs.io/
"""

# flake8: noqa

__version__ = "2.14.1"

# v3.0.0 API
from .core.imopen import imopen

# Load some bits from core
from .core import FormatManager, RETURN_BYTES

# Instantiate the old format manager
formats = FormatManager()

# import v2 into top level namespace
from .v2 import *

from . import v2
from . import v3
from . import plugins

# import config after core to avoid circular import
from . import config


# expose the show method of formats
show_formats = formats.show

__all__ = [
    "v2",
    "v3",
    "config",
    "plugins",
    # v2 API
    "imread",
    "mimread",
    "volread",
    "mvolread",
    "imwrite",
    "mimwrite",
    "volwrite",
    "mvolwrite",
    # v2 aliases
    "read",
    "save",
    "imsave",
    "mimsave",
    "volsave",
    "mvolsave",
    # v2 misc
    "help",
    "get_reader",
    "get_writer",
    "formats",
    "show_formats",
]
