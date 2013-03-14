# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 

.. note::
    imageio is under construction, only a limited set of functions have yet
    been implemented. However, the imread and imsave functions work
    and their signature is very likely to stay the same.

These functions are the main interface for the imageio user. They
provide a common interface to read and save image data for a large
variety of formats. All read and save functions accept keyword
arguments, which are passed on to the format that does the actual work.
To see what keyword arguments are supported by a specific format, use
the imageio.help function.

Functions for reading/saving of images:

  * imageio.imread - reads an image from the specified file and return as a 
    numpy array.
  * imageio.imsave - save an image to the specified file.
  * imageio.mimread - read a series of images from the specified file.
  * imageio.mimsave - save a series of images to the specified file.

Functions for reading/saving of volumes: todo

For a larger degree of control, imageio provides the functions
imageio.read and imageio.save. They respectively return an
imageio.Reader and an imageio.Writer object, which can be used to
read/save data and meta data in a more controlled manner. This also
allows specific scientific formats to be exposed in a way that best
suits that file-format.

"""


import sys
import os 
import numpy as np

import imageio
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


def help(name=None):
    """ help(name=None)
    
    Print the documentation of the format specified by name, or a list
    of supported formats if name is omitted.
    
    The specified name can be the name of a format, a filename extension, 
    or a full filename.
    
    See also the :doc:`formats page <formats>`.
    
    """
    if not name:
        print(formats)
    else:
        print(formats[name])

# todo: implement inforead function?

## Base functions that return a reader/writer

def read(uri, format=None, expect=None, **kwargs):
    """ read(uri, format=None, expect=None, **kwargs)
    
    Returns a reader object which can be used to read data and info 
    from the specified file.
    
    Parameters
    ----------
    uri : {str, bytes}
        The resource to load the image from. This can be a normal
        filename, a file in a zipfile, an http/ftp address, a file
        object, or the raw bytes.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
        Used to give the reader a hint on what the user expects. Optional.
    
    Further keyword arguments are passed to the reader. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Create request object
    request = imageio.request.ReadRequest(uri, expect, **kwargs)
    
    # Get format
    if format is not None:
        format = formats[format]
    else:
        format = formats.search_read_format(request)
    if format is None:
        raise ValueError('Could not find a format to read the specified file.')
    
    # Return its reader object
    return format.read(request)


def save(uri, format=None, expect=None, **kwargs):
    """ save(uri, format=None, expect=None, **kwargs)
    
    Returns a writer object which can be used to save data and info 
    to the specified file.
    
    Parameters
    ----------
    uri : str
        The resource to save the image to. This can be a normal
        filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
        case the raw bytes are returned.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename.
    expect : {imageio.EXPECT_IM, imageio.EXPECT_MIM, imageio.EXPECT_VOL}
        Used to give the writer a hint on what kind of data to expect. Optional.
    
    Further keyword arguments are passed to the writer. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Create request object
    request = imageio.request.WriteRequest(uri, expect, **kwargs)
    
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

def imread(uri, format=None, **kwargs):
    """ imread(uri, format=None, **kwargs)
    
    Reads an image from the specified file. Returns a numpy array, which
    comes with a dict of meta data at its 'meta' attribute.
    
    Parameters
    ----------
    uri : {str, bytes}
        The resource to load the image from. This can be a normal
        filename, a file in a zipfile, an http/ftp address, a file
        object, or the raw bytes.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    
    Further keyword arguments are passed to the reader. See the docstring
    of the corresponding format to see what arguments are available.
    
    """ 
    
    # Get reader and read first
    reader = read(uri, format, imageio.EXPECT_IM, **kwargs)
    with reader:
        return reader.get_data(0)


def imsave(uri, im, format=None, **kwargs):
    """ imsave(uri, im, format=None, **kwargs)
    
    Save an image to the specified file.
    
    Parameters
    ----------
    uri : str
        The resource to save the image to. This can be a normal
        filename, a file in a zipfile, or imageio.RETURN_BYTES, in which
        case the raw bytes are returned.
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
    
    # Get writer and write first
    writer = save(uri, format, imageio.EXPECT_IM, **kwargs)
    with writer:
        writer.append_data(im)
    
    # Return a result if there is any
    return writer.request.get_result()


## Multiple images

def mimread(uri, format=None, **kwargs):
    # Get reader and read all
    reader = read(uri, format, imageio.EXPECT_MIM, **kwargs)
    with reader:
        return [im for im in reader]


def mimsave(uri, ims, format=None, **kwargs):
    raise NotImplemented()


## Volumes

def volread(uri, format=None, **kwargs):
    reader = read(uri, format, imageio.EXPECT_VOL, **kwargs)
    with reader:
        return reader.get_data(0)


def volsave(filename, vol, format, **kwargs):
    raise NotImplemented()


## Multiple volumes

def mvolread(self, filename, vol, format, **kwargs):
    raise NotImplemented()


def mvolsave(self, filename, vol, format, **kwargs):
    raise NotImplemented()
