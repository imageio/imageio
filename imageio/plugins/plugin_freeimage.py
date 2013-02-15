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

from imageio.freeimage import IO_FLAGS


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
        self._flags = flags  # Store flags for later use
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
    
    
    def _append_data(self, im, meta):        
        if not self._set:
            self._set = True
        else:
            raise RuntimeError('Singleton image; can only append image data once.')
        
        # Lazy instantaion of the bitmap, we need image data
        if self._bm is None:
            self._bm = fi.create_bitmap(self.request.filename, self.format.fif, self._flags)
            self._bm.allocate(im)
        
        # Set
        self._bm.set_image_data(im)
        self._bm.set_meta_data(meta)
    
    
    def set_meta_data(self, meta):
        self._meta = meta


# todo: implement separate Formats for some FreeImage file formats


## Special plugins


class FreeimagePngFormat(FreeimageFormat):
    """ A PNG format based on the Freeimage library.
    
    Keyword arguments for reading
    -----------------------------
    ignoregamma : bool
        Avoid gamma correction. Default False.
    
    Keyword arguments for writing
    -----------------------------
    compression : {0, 1, 6, 9}
        The compression factor. Higher factors result in more
        compression at the cost of speed. Note that PNG compression is
        always lossless. Default 6.
    interlaced : bool
        Save using Adam7 interlacing. Default False.
    
    """
    
    def _get_reader_class(self):
        return PngReader
    
    def _get_writer_class(self):
        return PngWriter 


class PngReader(Reader):
    def _enter(self, flags=0, ignoregamma=False):
        # Build flags from kwargs
        flags = int(flags)        
        if ignoregamma:
            flags |= IO_FLAGS.PNG_IGNOREGAMMA
        # Enter as usual, with modified flags
        return Reader._enter(self, flags)


class PngWriter(Writer):
    def _enter(self, flags=0, compression=6, interlaced=False):
        # Build flags from kwargs
        flags = int(flags)
        if compression == 0:
            flags |= IO_FLAGS.PNG_Z_NO_COMPRESSION
        elif compression == 1:
            flags |= IO_FLAGS.PNG_Z_BEST_SPEED
        elif compression == 6:
            flags |= IO_FLAGS.PNG_Z_DEFAULT_COMPRESSION
        elif compression == 9:
            flags |= IO_FLAGS.PNG_Z_BEST_COMPRESSION
        else:
            raise ValueError('Png compression must be 0, 1, 6, or 9.')
        #
        if interlaced:
            flags |= IO_FLAGS.PNG_INTERLACED
        
        # Act as usual, but with modified flags
        return Writer._enter(self, flags)



class FreeimageJpegFormat(FreeimageFormat):
    """ A JPEG format based on the Freeimage library.
    
    Keyword arguments for reading
    -----------------------------
    exifrotate : bool
        Automatically rotate the image according to the exif flag. Default True.
    quickread : bool
        Read the image more quickly, at the expense of quality. Default False.
    
    Keyword arguments for writing
    -----------------------------
    quality : scalar
        The compression factor of the saved image (0..100), higher
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
    
    def _get_reader_class(self):
        return JpegReader
    
    def _get_writer_class(self):
        return JpegWriter 


class JpegReader(Reader):
    def _enter(self, flags=0, exifrotate=True, quickread=False):
        # Build flags from kwargs
        flags = int(flags)        
        if exifrotate:
            flags |= IO_FLAGS.JPEG_EXIFROTATE
        if not quickread:
            flags |= IO_FLAGS.JPEG_ACCURATE
        # Enter as usual, with modified flags
        return Reader._enter(self, flags)


class JpegWriter(Writer):
    def _enter(self, flags=0, 
            quality=75, progressive=False, optimize=False, baseline=False):
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
        return Writer._enter(self, flags)



## Create the formats

SPECIAL_CLASSES = { 'jpeg': FreeimageJpegFormat,
                    'png': FreeimagePngFormat,
                }


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
            # Get class for format
            FormatClass = SPECIAL_CLASSES.get(name.lower(), FreeimageFormat)
            # Create Format and add
            format = FormatClass(name, des, ext, i)
            formats.add_format(format)

create_freeimage_formats()
