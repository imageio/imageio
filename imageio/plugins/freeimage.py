# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the freeimage lib. The wrapper for Freeimage is
part of the core of imageio, but it's functionality is exposed via
the plugin system (therefore this plugin is very thin).
"""

from __future__ import absolute_import, print_function, division

import numpy as np

from imageio import formats
from imageio.core import Format
from ._freeimage import fi, IO_FLAGS


# todo: support files with only meta data
# todo: multi-page files


class FreeimageFormat(Format):
    """ This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    
    Parameters for reading
    ----------------------
    flags : int
        A freeimage-specific option. In most cases we provide explicit
        parameters for influencing image reading.
    
    Parameters for saving
    ----------------------
    flags : int
        A freeimage-specific option. In most cases we provide explicit
        parameters for influencing image saving.
    """
    
    _modes = 'i'
    
    @property
    def fif(self):
        return self._fif  # Set when format is created
    
    def _can_read(self, request):
        modes = self._modes + '?'
        if fi and request.mode[1] in modes:
            if not hasattr(request, '_fif'):
                try:
                    request._fif = fi.getFIF(request.filename, 'r', 
                                             request.firstbytes)
                except Exception:  # pragma: no cover
                    request._fif = -1
            if request._fif == self.fif:
                return True
    
    def _can_save(self, request):
        modes = self._modes + '?'
        if fi and request.mode[1] in modes:
            if not hasattr(request, '_fif'):
                try:
                    request._fif = fi.getFIF(request.filename, 'w')
                except Exception:  # pragma: no cover
                    request._fif = -1
            if request._fif is self.fif:
                return True
    
    # --
    
    class Reader(Format.Reader):
        
        def _get_length(self):
            return 1
        
        def _open(self, flags=0):
            self._bm = fi.create_bitmap(self.request.filename, 
                                        self.format.fif, flags)
            self._bm.load_from_filename(self.request.get_local_filename())
        
        def _close(self):
            self._bm.close()
        
        def _get_data(self, index):
            if index != 0:
                raise IndexError('This format only supports singleton images.')
            return self._bm.get_image_data(), self._bm.get_meta_data()
        
        def _get_meta_data(self, index):
            if not (index is None or index == 0):
                raise IndexError()
            return self._bm.get_meta_data()
    
    # --
    
    class Writer(Format.Writer):
        
        def _open(self, flags=0):        
            self._flags = flags  # Store flags for later use
            self._bm = None
            self._is_set = False  # To prevent appending more than one image
            self._meta = {}
        
        def _close(self):
            # Set global meta data
            self._bm.set_meta_data(self._meta)
            # Write and close
            self._bm.save_to_filename(self.request.get_local_filename())
            self._bm.close()
        
        def _append_data(self, im, meta):    
            # Check if set
            if not self._is_set:
                self._is_set = True
            else:
                raise RuntimeError('Singleton image; '
                                   'can only append image data once.')
            # Pop unit dimension for grayscale images
            if im.ndim == 3 and im.shape[-1] == 1:
                im = im.reshape(im.shape[:2])
            # Lazy instantaion of the bitmap, we need image data
            if self._bm is None:
                self._bm = fi.create_bitmap(self.request.filename, 
                                            self.format.fif, self._flags)
                self._bm.allocate(im)
            # Set data
            self._bm.set_image_data(im)
            # There is no distinction between global and per-image meta data 
            # for singleton images
            self._meta = meta  
        
        def set_meta_data(self, meta):
            self._meta = meta


## Special plugins

# todo: there is also FIF_LOAD_NOPIXELS, 
# but perhaps that should be used with get_meta_data.

class FreeimageBmpFormat(FreeimageFormat):
    """ A BMP format based on the Freeimage library.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for saving
    ---------------------
    compression : bool
        Whether to compress the bitmap using RLE when saving. Default False.
    
    """

    class Writer(FreeimageFormat.Writer):
        def _open(self, flags=0, compression=False):
            # Build flags from kwargs
            flags = int(flags)
            if compression:
                flags |= IO_FLAGS.BMP_SAVE_RLE
            else:
                flags |= IO_FLAGS.BMP_DEFAULT
            # Act as usual, but with modified flags
            return FreeimageFormat.Writer._open(self, flags)
        
        def _append_data(self, im, meta):
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            return FreeimageFormat.Writer._append_data(self, im, meta)


class FreeimageGifFormat(FreeimageFormat):
    """ A GIF format based on the Freeimage library.
    
    Reading a gif image always yields an RGBA image.
    
    Parameters for reading
    ----------------------
    playback : bool
        'Play' the GIF to generate each frame (as 32bpp) instead of
        returning raw frame data when loading. Default True.

    """
    
    class Reader(FreeimageFormat.Reader):
        def _open(self, flags=0, playback=True):
            # Build flags from kwargs
            flags = int(flags)
            if playback:
                flags |= IO_FLAGS.GIF_PLAYBACK 
            # Act as usual, but with modified flags
            return FreeimageFormat.Reader._open(self, flags)
    
    class Writer(FreeimageFormat.Writer):
        def _append_data(self, im, meta):
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            return FreeimageFormat.Writer._append_data(self, im, meta)


class FreeimageIcoFormat(FreeimageFormat):
    """ An ICO format based on the Freeimage library.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for reading
    ----------------------
    makealpha : bool
        Convert to 32-bit and create an alpha channel from the AND-
        mask when loading. Default False. Note that this returns wrong
        results if the image was already RGBA.
    
    """
    
    _modes = 'iI'
    
    # todo: this supports multiple images!
    
    class Reader(FreeimageFormat.Reader):
        def _open(self, flags=0, makealpha=False):
            # Build flags from kwargs
            flags = int(flags)
            if makealpha:
                flags |= IO_FLAGS.ICO_MAKEALPHA
            # Create bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, 
                                                  self.format.fif, flags)
            self._bm.load_from_filename(self.request.get_local_filename())
            
            # Act as usual, but with modified flags
            #return FreeimageFormat.Reader._open(self, flags)
        
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
                # ICO does not support global meta data (I think)
                # return self._bm.get_meta_data()  # SEGFAULT
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
            self._flags = int(flags)
            # Instantiate multi-page bitmap
            self._bm = fi.create_multipage_bitmap(self.request.filename, 
                                                  self.format.fif, flags)
            self._bm.save_to_filename(self.request.get_local_filename())
        
        def _close(self):
            # Set global meta now
            self._bm.set_meta_data(self._meta)
            # Close bitmap
            self._bm.close()
        
        def _append_data(self, im, meta): 
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
        
        def set_meta_data(self, meta):
            self._meta.update(meta)


class FreeimagePngFormat(FreeimageFormat):
    """ A PNG format based on the Freeimage library.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for reading
    ----------------------
    ignoregamma : bool
        Avoid gamma correction. Default False.
    
    Parameters for saving
    ---------------------
    compression : {0, 1, 6, 9}
        The compression factor. Higher factors result in more
        compression at the cost of speed. Note that PNG compression is
        always lossless. Default 9.
    quantize : int
        If specified, turn the given RGB or RGBA image in a paletted image
        for more efficient storage. The value should be between 2 and 256.
        If the value of 0 the image is not quantized.
    interlaced : bool
        Save using Adam7 interlacing. Default False.
    
    Note: the compression and interlaced parameters currently do not
    seem to work.
    
    """
    
    class Reader(FreeimageFormat.Reader):
        def _open(self, flags=0, ignoregamma=False):
            # Build flags from kwargs
            flags = int(flags)        
            if ignoregamma:
                flags |= IO_FLAGS.PNG_IGNOREGAMMA
            # Enter as usual, with modified flags
            return FreeimageFormat.Reader._open(self, flags)
    
    # -- 
    
    class Writer(FreeimageFormat.Writer):
        def _open(self, flags=0, compression=9, quantize=0, interlaced=False):
            compression_map = {0: IO_FLAGS.PNG_Z_NO_COMPRESSION,
                               1: IO_FLAGS.PNG_Z_BEST_SPEED,
                               6: IO_FLAGS.PNG_Z_DEFAULT_COMPRESSION,
                               9: IO_FLAGS.PNG_Z_BEST_COMPRESSION, }
            # Build flags from kwargs
            flags = int(flags)
            if interlaced:
                flags |= IO_FLAGS.PNG_INTERLACED
            try:
                flags |= compression_map[compression]
            except KeyError:
                raise ValueError('Png compression must be 0, 1, 6, or 9.')
            # Act as usual, but with modified flags
            return FreeimageFormat.Writer._open(self, flags)
        
        def _append_data(self, im, meta):
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            FreeimageFormat.Writer._append_data(self, im, meta)
            # Quantize?
            q = int(self.request.kwargs.get('quantize', False))
            if not q:
                pass
            elif not (im.ndim == 3 and im.shape[-1] in (3, 4)):
                raise ValueError('Cannot quantize grayscale images')
            elif q < 2 or q > 256:
                raise ValueError('PNG quantize param must be 2..256')
            else:
                bm = self._bm.quantize(0, q)
                self._bm.close()
                self._bm = bm


class FreeimageJpegFormat(FreeimageFormat):
    """ A JPEG format based on the Freeimage library.
    
    This format supports grayscale and RGB images.
    
    Parameters for reading
    ----------------------
    exifrotate : bool
        Automatically rotate the image according to the exif flag.
        Default True.
    quickread : bool
        Read the image more quickly, at the expense of quality. 
        Default False.
    
    Parameters for saving
    ---------------------
    quality : scalar
        The compression factor of the saved image (1..100), higher
        numbers result in higher quality but larger file size. Default 75.
    progressive : bool
        Save as a progressive JPEG file (e.g. for images on the web).
        Default False.
    optimize : bool
        On saving, compute optimal Huffman coding tables (can reduce a
        few percent of file size). Default False.
    baseline : bool
        Save basic JPEG, without metadata or any markers. Default False.
    
    """
    
    class Reader(FreeimageFormat.Reader):
        def _open(self, flags=0, exifrotate=True, quickread=False):
            # Build flags from kwargs
            flags = int(flags)        
            if exifrotate:
                pass  # we do this ourselves  flags |= IO_FLAGS.JPEG_EXIFROTATE
            if not quickread:
                flags |= IO_FLAGS.JPEG_ACCURATE
            # Enter as usual, with modified flags
            return FreeimageFormat.Reader._open(self, flags)
        
        def _get_data(self, index):
            im, meta = FreeimageFormat.Reader._get_data(self, index)
            im = self._rotate(im, meta)
            return im, meta
        
        def _rotate(self, im, meta):
            """ Use Orientation information from EXIF meta data to 
            orient the image correctly. Freeimage is also supposed to
            support that, and I am pretty sure it once did, but now it
            does not, so let's just do it in Python.
            """
            if self.request.kwargs.get('exifrotate', True):
                try:
                    ori = meta['EXIF_MAIN']['Orientation']
                except KeyError:
                    pass  # Orientation not available
                else:  # pragma: no cover  we cannot touch all cases
                    # www.impulseadventure.com/photo/exif-orientation.html
                    if ori in [1, 2]:
                        pass
                    if ori in [3, 4]:
                        im = np.rot90(im, 2)
                    if ori in [5, 6]:
                        im = np.rot90(im, 3)
                    if ori in [7, 8]:
                        im = np.rot90(im)
                    if ori in [2, 4, 5, 7]:  # Flipped cases (rare)
                        im = np.fliplr(im)
            return im
    
    # --
        
    class Writer(FreeimageFormat.Writer):
        def _open(self, flags=0, quality=75, progressive=False, optimize=False,
                  baseline=False):
            # Test quality
            quality = int(quality)
            if quality < 1 or quality > 100:
                raise ValueError('JPEG quality should be between 1 and 100.')
            # Build flags from kwargs
            flags = int(flags)
            flags |= quality
            if progressive:
                flags |= IO_FLAGS.JPEG_PROGRESSIVE
            if optimize:
                flags |= IO_FLAGS.JPEG_OPTIMIZE
            if baseline:
                flags |= IO_FLAGS.JPEG_BASELINE
            # Act as usual, but with modified flags
            return FreeimageFormat.Writer._open(self, flags)
        
        def _append_data(self, im, meta):
            if im.ndim == 3 and im.shape[-1] == 4:
                raise IOError('JPEG does not support alpha channel.')
            if im.dtype in (np.float32, np.float64):
                im = (im * 255).astype(np.uint8)
            return FreeimageFormat.Writer._append_data(self, im, meta)


## Create the formats

SPECIAL_CLASSES = {'jpeg': FreeimageJpegFormat,
                   'png': FreeimagePngFormat,
                   'bmp': FreeimageBmpFormat,
                   'gif': FreeimageGifFormat,
                   'ico': FreeimageIcoFormat,
                   }


def create_freeimage_formats():
    
    # Freeimage available?
    if fi is None:  # pragma: no cover
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
            # Get class for format
            FormatClass = SPECIAL_CLASSES.get(name.lower(), FreeimageFormat)
            # Create Format and add
            format = FormatClass(name, des, ext, FormatClass._modes)
            format._fif = i
            formats.add_format(format)

create_freeimage_formats()
