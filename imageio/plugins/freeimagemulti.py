# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin for multi-image freeimafe formats, like animated GIF and ico.
"""

from __future__ import absolute_import, print_function, division

import numpy as np

from imageio import formats
from imageio.core import Format
from ._freeimage import fi, IO_FLAGS
from .freeimage import FreeimageFormat


class FreeimageMulti(FreeimageFormat):
    """ Base class for freeimage formats that support multiple images.
    """
    
    _modes = 'iI'
    _fif = -1
    
    class Reader(Format.Reader):
        def _open(self, flags=0):
            flags = int(flags)
            # Create bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, 
                                                  self.format.fif, flags)
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
                return {}
                # return self._bm.get_meta_data()  SEGFAULT
            else:
                sub = self._bm.get_page(index)
                try:
                    return sub.get_meta_data()
                finally:
                    sub.close()
    
    # --
    
    class Writer(FreeimageFormat.Writer):
        
        def _open(self, flags=0):
            self._meta = {}
            # Set flags
            self._flags = flags = int(flags)
            # Instantiate multi-page bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, 
                                                  self.format.fif, flags)
            self._bm.save_to_filename(self.request.get_local_filename())
        
        def _close(self):
            # Set global meta now
            #self._bm.set_meta_data(self._meta)  We cannot get, so why set?
            # Close bitmap
            self._bm.close()
        
        def _append_data(self, im, meta):
            raise NotImplementedError()
        
        def _set_meta_data(self, meta):
            self._meta.update(meta)


class IcoFormat(FreeimageMulti):
    """ An ICO format based on the Freeimage library.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for reading
    ----------------------
    makealpha : bool
        Convert to 32-bit and create an alpha channel from the AND-
        mask when loading. Default False. Note that this returns wrong
        results if the image was already RGBA.
    
    """
    
    _fif = 1
    
    class Reader(FreeimageMulti.Reader):
        def _open(self, flags=0, makealpha=False):
            # Build flags from kwargs
            flags = int(flags)
            if makealpha:
                flags |= IO_FLAGS.ICO_MAKEALPHA
            return FreeimageMulti.Reader._open(self, flags)
    
    class Writer(FreeimageMulti.Writer):
        
        def _append_data(self, im, meta):
            # Make array unint8 and nicely shaped
            if im.ndim == 3 and im.shape[-1] == 1:
                im = im.reshape(im.shape[:2])
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            # Create sub bitmap
            sub1 = fi.create_bitmap(self._bm._filename, self.format.fif)
            sub1.allocate(im)
            sub1.set_image_data(im)
            sub1.set_meta_data(meta)
            # Add
            self._bm.append_bitmap(sub1)
            sub1.close()
    

class GifFormat(FreeimageMulti):
    """ A format for reading and writing static and animated GIF, based
    on the Freeimage library.
    
    Images read with this format are always RGBA. Currently,
    the alpha channel is ignored when saving RGB images with this
    format.
    
    Parameters for reading
    ----------------------
    playback : bool
        'Play' the GIF to generate each frame (as 32bpp) instead of
        returning raw frame data when loading. Default True.
    
    Parameters for saving
    ---------------------
    loop : int
        The number of iterations. Default 0 (meaning loop indefinitely)
        This argument is not implemented yet :(
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
    
    _fif = 25
    
    class Reader(FreeimageMulti.Reader):
        
        def _open(self, flags=0, playback=True):
            # Build flags from kwargs
            flags = int(flags)
            if playback:
                flags |= IO_FLAGS.GIF_PLAYBACK 
            FreeimageMulti.Reader._open(self, flags)
        
        def _get_data(self, index):
            im, meta = FreeimageMulti.Reader._get_data(self, index)
            # im = im[:, :, :3]  # Drop alpha channel
            return im, meta
    
    # -- writer 
    
    class Writer(FreeimageMulti.Writer):
       
        # todo: loop argument
        # todo: subrectangles
        # todo: global palette
        
        def _open(self, flags=0, loop=0, duration=0.1, palettesize=256, 
                  quantizer='Wu'):
            # Check palettesize
            if palettesize < 2 or palettesize > 256:
                raise ValueError('PNG quantize param must be 2..256')
            if palettesize not in [2, 4, 8, 16, 32, 64, 128, 256]:
                palettesize = 2 ** int(np.log2(128) + 0.999)
                print('Warning: palettesize (%r) modified to a factor of '
                      'two between 2-256.' % palettesize)
            self._palettesize = palettesize
            # Check quantizer
            self._quantizer = {'wu': 0, 'nq': 1}.get(quantizer.lower(), None)
            if self._quantizer is None:
                raise ValueError('Invalid quantizer, must be "wu" or "nq".')
            # Check frametime
            if isinstance(duration, list):
                self._frametime = [int(1000 * d) for d in duration]
            elif isinstance(duration, (float, int)):
                self._frametime = [int(1000 * duration)]
            else:
                raise ValueError('Invalid value for duration: %r' % duration)
            # Intialize meta
            self._meta = {'ANIMATION': {  
                          #'GlobalPalette': np.array([]).astype(np.uint8),
                          # 'Loop': np.array([loop]).astype(np.uint32),
                          # Loop segfaults, why?
                          }
                          }
            FreeimageMulti.Writer._open(self, flags)
        
        def _append_data(self, im, meta): 
            # Check array
            if im.ndim == 3 and im.shape[-1] == 4:
                im = im[:, :, :3]
            if im.ndim == 3 and im.shape[-1] == 1:
                im = im.reshape(im.shape[:2])
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            # Tweak meta data
            meta = meta.copy()
            meta_a = meta['ANIMATION'] = {}
            # Set frame time
            index = len(self._bm)
            if index < len(self._frametime):
                ft = self._frametime[index]
            else:
                ft = self._frametime[-1]
            meta_a['FrameTime'] = np.array([ft]).astype(np.uint32)
            # Create sub bitmap
            sub1 = fi.create_bitmap(self._bm._filename, self.format.fif)
            sub1.allocate(im)
            sub1.set_image_data(im)
            # Quantize it if its RGB 
            sub2 = sub1
            if im.ndim == 3 and im.shape[2] in (3, 4):
                sub2 = sub1.quantize(self._quantizer, self._palettesize)
            # Set meta data for this frame
            if self.request.mode[1] == 'i':
                del meta['ANIMATION']
            sub2.set_meta_data(meta)
            # Append bitmap and close sub bitmap(s)
            self._bm.append_bitmap(sub2)
            sub2.close()
            if sub1 is not sub2:
                sub1.close()


formats.add_format(GifFormat('GIF', 'Static and animated gif', 
                             '.gif', 'iI'))
formats.add_format(IcoFormat('ICO', 'Windows icon', 
                             '.ico', 'iI'))
