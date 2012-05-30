# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" This module defines root_plugin instance. It is a FormatCollection
that the plugins should add themselves to.

This implementation defines all the read/save functions that are exposed
to the user. Therefore there is quite a bit of argument checking, producing
of useful error messages, and docstrings here.

"""

import os
import sys
import numpy as np

from imageio.base import Plugin, FormatCollection, Format

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



class RootPlugin(FormatCollection):
    """ The root plugin 
    """ 
    
    def _read_first_bytes(self, filename, N=256):
        """ Read the first few bytes that can be used by 
        plugins to identify the file.
        """
        f = open(filename, 'rb')
        first_bytes = binary_type()
        while len(first_bytes) < N:
            extra_bytes = f.read(N-len(first_bytes))
            if not extra_bytes:
                break
            first_bytes += extra_bytes
        f.close()
        return first_bytes
    
    
    def imread(self, filename, format=None, **kwargs):
        
        # Test filename
        if not isinstance(filename, string_types):
            raise TypeError('Filename must be a string.')
        if not os.path.isfile(filename):
            raise IOError("No such file: '%s'" % filename)
        
        # Get first bytes
        first_bytes = self._read_first_bytes(filename)
        
        if format is not None:
            # Format explicitly given
            if isinstance(format, Format):
                pass
            elif isinstance(format, string_type):
                # todo: get format from string
                raise NotImplemented('TODO: GET FORMAT FROM STRING')
            else:
                raise ValueError('Invalid format given.')
        else:
            # Ask all plugins whether they can read it (until one says it can)        
            plugins = self._format_collections + self._formats
            for plugin in plugins:
                format = plugin.can_read_im(filename, first_bytes)                
                if isinstance(format, Format):
                    break
            else:
                raise IOError("No format found that can read '%s'." % filename)
        
        # Read 
        return format.imread(filename, **kwargs)
    
    
    def imsread(self, filename, format, **kwargs):
        raise NotImplemented()
    
    def volread(self, filename, format, **kwargs):
        raise NotImplemented()
    
    
    def imsave(self, filename, im, format=None, **kwargs):
        
        # Test filename
        if not isinstance(filename, string_types):
            raise TypeError('Filename must be a string.')
        
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
        
        if format is not None:
            # Format explicitly given
            if isinstance(format, Format):
                pass
            elif isinstance(format, string_type):
                # todo: get format from string
                raise NotImplemented('TODO: GET FORMAT FROM STRING')
            else:
                raise ValueError('Invalid format given.')
        else:
            # Ask all plugins whether they can read it (until one says it can)        
            plugins = self._format_collections + self._formats
            for plugin in plugins:
                format = plugin.can_save_im(filename)                
                if isinstance(format, Format):
                    break
            else:
                raise IOError("No format found that can save '%s'." % filename)
        
        # Read 
        return format.imsave(filename, im, **kwargs)
    
    
    def imssave(self, filename, ims, format, **kwargs):
        raise NotImplemented()
    
    def volsave(self, filename, vol, format, **kwargs):
        raise NotImplemented()

