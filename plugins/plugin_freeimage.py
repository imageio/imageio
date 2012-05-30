# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the freeimage lib. The wrapper for Freeimage is
part of the core of imageio, but it's functionality is exposed via
the plugin system (therefore this plugin is very thin).
"""

from imageio import FormatCollection, Format, root_plugin
from imageio import fi
import ctypes


class FreeimageFormatCollection(FormatCollection):
    
    def can_read_im(self, filename, first_bytes):
        if fi:
            # Lazy loading
            if not hasattr(self, '_formatDict'):
                self.create_freeimage_formats()
            # Get fif and return the format that corresponds with it
            fif = fi.getFIF(filename, 'r')
            return self._formatDict.get(fif, None)
            
    def can_save_im(self, filename):
        if fi:
            # Lazy loading
            if not hasattr(self, '_formatDict'):
                self.create_freeimage_formats()
            # Get fif and return the format that corresponds with it
            fif = fi.getFIF(filename, 'w')
            return self._formatDict.get(fif, None)
    
    def create_freeimage_formats(self):
        
        # Freeimage available?
        if fi is None:
            return 
        
        # Init
        lib = fi._lib
        self._formatDict = {}
        
        # Create formats        
        for i in range(lib.FreeImage_GetFIFCount()):
            if lib.FreeImage_IsPluginEnabled(i):                
                # Get info
                name = lib.FreeImage_GetFormatFromFIF(i)            
                des = lib.FreeImage_GetFIFDescription(i)
                ext = lib.FreeImage_GetFIFExtensionList(i)
                # Create Format and add (in two ways)
                format = FreeimageFormat(name, des, i)
                self._formatDict[i] = format
                self.add_plugin(format)


class FreeimageFormat(Format):
    
    def __init__(self, name, description, fif):
        Format.__init__(self, name, description)
        self._fif = fif
    
    @property
    def fif(self):
        return self._fif
    
    def imread(self, filename, flags=0):
        # todo: Allow special cases with kwrags
        return fi.read(filename, flags)
    
    def imsave(self, filename, im, flags=0):
        # todo: rename to save for consistency (or whatever name we decide on)
        return fi.write(im, filename, flags)

# Create and register plugin
root_plugin.add_plugin(FreeimageFormatCollection())
