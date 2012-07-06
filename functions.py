# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
These are the main functions exposed to the user.

For images:

  * imageio.imread - reads an image from the specified file and return as a 
    numpy array.
  * imageio.imsave - save an image to the specified file.
  * imageio.mimread - read a series of images from the specified file.
  * imageio.mimsave - save a series of images to the specified file.

For volumes: todo

For somewhat lower level and more control:

  * imageio.read: returns a reader object which can be used to read data 
    and info from the specified file. 
  * imageio.save: returns a writer object which can be used to write data
    and info to the specified file.


"""


import sys
import os 
import numpy as np

from imageio import formats
from imageio import base

# Taken from six.py
PY3 = sys.version_info[0] == 3
if PY3:
    string_types = str,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    text_type = unicode
    binary_type = str


## Base functions that return a reader/writer

def read(filename, format=None, expect=None, **kwargs):
    """ read(filename, format=None, expect=None, **kwargs)
    
    Returns a reader object which can be used to read data and info 
    from the specified file.
    
    Parameters
    ----------
    filename : str
        The location of the file on the file system.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
        Used to give the reader a hint on what the user expects. Optional.
    
    Further keyword arguments are passed to the reader. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Test filename
    if not isinstance(filename, string_types):
        raise TypeError('Filename must be a string.')
    if not os.path.isfile(filename):
        raise IOError("No such file: '%s'" % filename)
    
    # Create request object
    request = base.Request(filename, expect, **kwargs)
    
    # Get format
    if format is not None:
        format = formats[format]
    else:
        format = formats.search_read_format(request)
    if format is None:
        raise ValueError('Could not find a format to read the specified file.')
    
    # Return its reader object
    return format.read(request)


def save(filename, format=None, expect=None, **kwargs):
    """ save(filename, format=None, expect=None, **kwargs)
    
    Returns a writer object which can be used to write data and info 
    to the specified file.
    
    Parameters
    ----------
    filename : str
        The location of the file to save to.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename.
    expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
        Used to give the writer a hint on what kind of data to expect. Optional.
    
    Further keyword arguments are passed to the writer. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Test filename
    if not isinstance(filename, string_types):
        raise TypeError('Filename must be a string.')
    
    # Create request object
    request = base.Request(filename, expect, **kwargs)
    
    # Get format
    if format is not None:
        format = formats[format]
    else:
        format = formats.search_save_format(request)
    if format is None:
        raise ValueError('Could not find a format to save the specified file.')
    
    # Return its writer object
    return format.save(request)


## Images

def imread(filename, format=None, **kwargs):
    """ imread(filename, format=None, **kwargs)
    
    Reads an image from the specified file. Returns a numpy array.
    
    Parameters
    ----------
    filename : str
        The location of the file on the file system.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    
    Further keyword arguments are passed to the reader. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Get reader and read first
    reader = read(filename, format, base.EXPECT_IM, **kwargs)
    with reader:
        return reader.read_data(0)


def imsave(filename, im, format=None, **kwargs):
    """ imsave(filename, im, format=None, **kwargs)
    
    Save an image to the specified file.
    
    Parameters
    ----------
    filename : str
        The location of the file to save to.
    im : numpy.ndarray
        The image data. Must be NxM, NxMx3 or NxMx4.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    
    Further keyword arguments are passed to the writer. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Test image
    if isinstance(im, np.ndarray):
        if im.ndim == 2:
            pass
        elif im.ndim == 3 and im.shape[2] in [3,4]:
            pass
        else:
            raise ValueError('Image must be 2D (grayscale, RGB, or RGBA).')
    else:
        raise ValueError('Image must be a numpy array.')
    
    # Get writer der and write first
    writer = save(filename, format, base.EXPECT_IM, **kwargs)
    with writer:
        writer.save_data(im, 0)


## Multiple images

def mimread(self, filename, ims, format, **kwargs):
    raise NotImplemented()

def mimsave(self, filename, ims, format, **kwargs):
    raise NotImplemented()


## Volumes

def volread(self, filename, vol, format, **kwargs):
    raise NotImplemented()


def volsave(self, filename, vol, format, **kwargs):
    raise NotImplemented()


## Multiple volumes

def mvolread(self, filename, vol, format, **kwargs):
    raise NotImplemented()


def mvolsave(self, filename, vol, format, **kwargs):
    raise NotImplemented()
