# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the freeimage lib. The wrapper for Freeimage is
part of the core of imageio, but it's functionality is exposed via
the plugin system (therefore this plugin is very thin).
"""

from imageio import Format, formats
from imageio import base
from imageio import fi
import ctypes


class FreeimageFormat(Format):
    """ This is the default format used for FreeImage.
    """
    
    def __init__(self, name, description, extensions, fif):
        Format.__init__(self, name, 'FI: '+description, extensions)
        self._fif = fif
    
    @property
    def fif(self):
        return self._fif
    
    def _get_reader_class(self):
        return Reader
    
    def _get_writer_class(self):
        return Writer 
    
    def _can_read(self, request):
        if fi and request.expect in [None, base.EXPECT_IM, base.EXPECT_MIM]:
            if not hasattr(request, '_fif'):
                request._fif = fi.getFIF(request.filename, 'r')
            if request._fif == self.fif:
                return True
                # Note: adding as a potential format and then returning False
                # will give preference to other formats that can read the file.
                #request.add_potential_format(self)
    
    def _can_save(self, request):
        if fi and request.expect in [None, base.EXPECT_IM, base.EXPECT_MIM]:
            if not hasattr(request, '_fif'):
                request._fif = fi.getFIF(request.filename, 'w')
            if request._fif is self.fif:
                return True


class Reader(base.Reader):
    
    def _mshape(self):
        return 1
    
    def _get_kwargs(self, flags=0):
        return flags
    
    def _read_data(self, *indices, **kwargs):
        flags = self._get_kwargs(**kwargs)
        # todo: Allow special cases with kwrags
        return fi.read(self.request.filename, flags)
    
    def _read_info(self, *indices, **kwargs):
        raise NotImplemented()
    
  
class Writer(base.Writer):
    
    def _get_kwargs(self, flags=0):
        return flags
    
    def _save_data(self, im, *indices, **kwargs):
        flags = self._get_kwargs(**kwargs)
        return fi.write(im, self.request.filename, flags)
    
    def _save_info(self, *indices, **kwargs):
        raise NotImplemented()

# todo: implement separate Formats for some FreeImage file formats



def create_freeimage_formats():
    
    # Freeimage available?
    if fi is None:
        return 
    
    # Init
    lib = fi._lib
    
    # Create formats        
    for i in range(lib.FreeImage_GetFIFCount()):
        if lib.FreeImage_IsPluginEnabled(i):                
            # Get info
            name = lib.FreeImage_GetFormatFromFIF(i).decode('ascii')
            des = lib.FreeImage_GetFIFDescription(i).decode('ascii')
            ext = lib.FreeImage_GetFIFExtensionList(i).decode('ascii')
            # Create Format and add (in two ways)
            format = FreeimageFormat(name, des, ext, i)
            formats.add_format(format)

create_freeimage_formats()
