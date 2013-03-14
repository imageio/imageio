# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin for animated GIF, using the freeimage lib as a backend.
"""

from imageio import Format, formats
from imageio import base
from imageio import fi
import ctypes

from imageio.freeimage import IO_FLAGS

# The freetype image format for GIF is 25
FIF = 25


class AnimatedGifFormat(Format):
    """ A format for reading and writing animated GIF, based on the
    Freeimage library.
    
    Keyword arguments for reading
    -----------------------------
    playback : bool
        'Play' the GIF to generate each frame (as 32bpp) instead of
        returning raw frame data when loading. Default True.
    
    Keyword arguments for writing
    -----------------------------
    
    """
    
    def _can_read(self, request):
        if fi and request.expect == base.EXPECT_MIM:
            if request.filename.lower().endswith('.gif'):
                return True
    
    def _can_save(self, request):
        return False  # self._can_read(request)
        # todo: Needs implementing


    class Reader(Format.Reader):
        
        def _open(self, flags=0, playback=True):
            # Build flags from kwargs
            flags = int(flags)
            if playback:
                flags |= IO_FLAGS.GIF_PLAYBACK 
            # Create bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, FIF, flags)
            self._bm.load_from_filename(self.request.get_local_filename())
        
        def _close(self):
            self._bm.close()
        
        def _get_length(self):
            return len(self._bm)
        
        def _get_data(self, index):
            sub = self._bm.get_page(index)
            try:
                return sub.get_image_data(), sub.get_meta_data()
            finally:
                sub.close()
        
        def _get_meta_data(self, index):
            if index is None:
                return self._bm.get_meta_data()
            else:
                sub = self._bm.get_page(index)
                try:
                    return sub.get_meta_data()
                finally:
                    sub.close()
        
        def _get_next_data(self):
            # No need to implement, imageio will determine our length and
            # then iterate via _get_data()
            raise NotImplementedError()
    
    
    class Writer(Format.Writer):
        
        def _open(self, flags=0):        
            self._flags = flags  # Store flags for later use
            self._bm = None
            self._set = False
            self._meta = {}
        
        def _close(self):
            # Set global meta now
            self._bm.set_meta_data(self._meta)
            # Save
            self._bm.save_to_filename(self.request.get_local_filename())
            # Close bitmap
            self._bm.close()
        
        def _append_data(self, im, meta):        
            if not self._set:
                self._set = True
            else:
                raise RuntimeError('Singleton image; can only append image data once.')
            
            # Lazy instantaion of the bitmap, we need image data
            if self._bm is None:
                self._bm = fi.create_bitmap(self.request.filename, FIF, self._flags)
                self._bm.allocate(im)
            
            # Set
            self._bm.set_image_data(im)
            self._bm.set_meta_data(meta)
        
        def set_meta_data(self, meta):
            self._meta = meta


formats.add_format(AnimatedGifFormat('ANIGIF', 'Animated gif', '.gif'))
