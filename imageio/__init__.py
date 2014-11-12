# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

# This docstring is what is used in setup.py and ends up on our Pypi page
""" 
Imageio is a Python library that provides an easy interface to read and
write a wide range of image data, including animated images, volumetric
data, and scientific formats. It is cross-platform, runs on Python 2.x
and 3.x, and is easy to install.

Main website: http://imageio.github.io

.. code-block:: python:
    
    import imageio
    
    >>> import imageio
    >>> im = imageio.imread('astronaut.png')
    >>> im.shape  # im is a numpy array
    (512, 512, 3)
    >>> imageio.imsave('astronaut-gray.jpg', im[:, :, 0])

See the `user API <http://imageio.readthedocs.org/en/latest/userapi.html>`_
or `more examples <http://imageio.readthedocs.org/en/latest/examples.html>`_
for more information.
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
