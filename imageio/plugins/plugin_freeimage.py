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

# todo: support files with only meta data
# todo: multi-page files

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


# todo: reader and writer use filenames directly if possible, so that
# when only reading meta data, or not all files from a multi-page file,
# the performance is increased.
class Reader(base.Reader):
    
    def _get_length(self):
        return 1
    
    
    def _enter(self, flags=0):
        
        # Create bitmap
        bm = fi.create_bitmap(self.request.filename, self.format.fif, flags)
        bb = self.request.get_bytes()
        bm.load_from_bytes(bb)
        self._bm = bm
    
    
    def _exit(self):
        self._bm.close()
    
    
    def _get_data(self, index, flags=0):
        # todo: Allow special cases with kwrags
        
        if index != 0:
            raise IndexError()
        
        return self._bm.get_image_data(), self._bm.get_meta_data()
    
    
    def _get_meta_data(self, index):
        
        if index is None or index==0:
            pass
        else:
            raise IndexError()
        
        return self._bm.get_meta_data()


    def _get_next_data(self, **kwargs):
        raise NotImplemented() 



class Writer(base.Writer):
    
    def _enter(self, flags=0):        
        self._bm = None
        self._set = False
        self._meta = {}
    
    
    def _exit(self):
        # Set global meta now
        self._bm.set_meta_data(self._meta)
        # Save
        bb = self._bm.save_to_bytes()
        self.request.set_bytes(bb)
        # Close bitmap
        self._bm.close()
    
    
    def _append_data(self, im, meta, flags=0):        
        if not self._set:
            self._set = True
        else:
            raise RuntimeError('Singleton image; can only append image data ones.')
        
        # Lazy instantaion of the bitmap, we need image data
        if self._bm is None:
            self._bm = fi.create_bitmap(self.request.filename, self.format.fif, flags)
            self._bm.allocate(im)
        
        # Set
        self._bm.set_image_data(im)
        self._bm.set_meta_data(meta)
    
    
    def set_meta_data(self, meta):
        self._meta = meta


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
