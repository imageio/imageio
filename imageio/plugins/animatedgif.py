# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin for animated GIF, using the freeimage lib as a backend.
"""

import numpy as np

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
    loop : int
        The number of iterations. Default 0 (meaning loop indefinitely)
        This argumen is not implemented yet :(
    duration : {float, list}
        The duration (in seconds) of each frame. Either specify one value
        that is used for all frames, or one value for each frame.
        Default 0.1
    palettesize : int
        The number of colors to quantize the image to. Is rounded to
        the nearest power of two. Default 256.
    quantizer : {'wu', 'nq'}
        The quantization algorithm:
          * wu - Wu, Xiaolin, Efficient Statistical Computations for
            Optimal Color Quantization
          * nq (neuqant) - Dekker A. H., Kohonen neural networks for
            optimal color quantization
    
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
        
        # todo: loop argument
        # todo: subrectangles
        # todo: global palette
        
        def _open(self, flags=0, loop=0, duration=0.1, palettesize=256, quantizer='Wu'): 
            # Check palettesize
            self._palettesize = max(2, min(256, int(palettesize)))
            if palettesize not in [2, 4, 8, 16, 32, 64, 128, 256]:
                print('Warning: palettesize (%r) modified to a factor of two between 2-256.' % palettesize)
            # Check quantizer
            self._quantizer = {'wu':0, 'nq':1}.get(quantizer.lower(), None)
            if self._quantizer is None:
                raise ValueError('Invalid quantizer, must be "wu" or "nq".')
            # Check frametime
            if isinstance(duration, list):
                self._frametime = [int(1000*d) for d in duration]
            elif isinstance(duration, (float, int)):
                self._frametime = [ int(1000*duration) ]
            else:
                raise ValueError('Invalid value for duration: %r' % duration)
            
            # Set flags
            self._flags = int(flags)
            # Intialize meta
            self._meta = {'ANIMATION': {    #'GlobalPalette': np.array([]).astype(np.uint8),
                                           # 'Loop': np.array([loop]).astype(np.uint32),
                                           # Loop segfaults, why?
                                        }
                            }
            # Instantiate multi-page bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, FIF, flags)
            self._bm.save_to_filename(self.request.get_local_filename())
        
        def _close(self):
            # Set global meta now
            self._bm.set_meta_data(self._meta)
            # Close bitmap
            self._bm.close()
        
        def _append_data(self, im, meta): 
            meta = meta.copy()
            meta_a = meta['ANIMATION'] = {}
            # Tweak meta data
            index = len(self._bm)
            if index < len(self._frametime):
                ft = self._frametime[index]
            else:
                ft = self._frametime[-1]
            meta_a['FrameTime'] = np.array([ft]).astype(np.uint32)
            # Discard alpha
            if im.ndim == 3 and im.shape[-1] ==4:
                im = im[:,:,:3]
            # Create sub bitmap
            sub1 = fi.create_bitmap(self._bm._filename, FIF)
            sub1.allocate(im)
            sub1.set_image_data(im)
            # Quantize it
            sub2 = sub1.quantize(self._quantizer, self._palettesize)
            sub2.set_meta_data(meta)
            # Add
            self._bm.append_bitmap(sub2)
            sub1.close()
            sub2.close()
        
        def set_meta_data(self, meta):
            self._meta.update(meta)


formats.add_format(AnimatedGifFormat('ANIGIF', 'Animated gif', '.gif'))
