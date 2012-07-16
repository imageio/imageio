""" Module imageio/freeimage.py

This module contains the wrapper code for the freeimage library.
The functions defined in this module are relatively thin; just thin
enough so that arguments and results are native Python/numpy data
types.

"""

import sys
import ctypes
import numpy
from imageio import freeimage_install

# todo: the caller should check if a file exists
# todo: make API class more complete
# todo: write with meta data
# todo: write with palette?
# todo: Check if jpeg has alpha channel. if so, deal with it and maybe warn.


# Define function to encode a filename to bytes (for the current system)
efn = lambda x : x.encode(sys.getfilesystemencoding())

# 4-byte quads of 0,v,v,v from 0,0,0,0 to 0,255,255,255
GREY_PALETTE = numpy.arange(0, 0x01000000, 0x00010101, dtype=numpy.uint32)


class FI_TYPES(object):
    FIT_UNKNOWN = 0
    FIT_BITMAP = 1
    FIT_UINT16 = 2
    FIT_INT16 = 3
    FIT_UINT32 = 4
    FIT_INT32 = 5
    FIT_FLOAT = 6
    FIT_DOUBLE = 7
    FIT_COMPLEX = 8
    FIT_RGB16 = 9
    FIT_RGBA16 = 10
    FIT_RGBF = 11
    FIT_RGBAF = 12

    dtypes = {
        FIT_BITMAP: numpy.uint8,
        FIT_UINT16: numpy.uint16,
        FIT_INT16: numpy.int16,
        FIT_UINT32: numpy.uint32,
        FIT_INT32: numpy.int32,
        FIT_FLOAT: numpy.float32,
        FIT_DOUBLE: numpy.float64,
        FIT_COMPLEX: numpy.complex128,
        FIT_RGB16: numpy.uint16,
        FIT_RGBA16: numpy.uint16,
        FIT_RGBF: numpy.float32,
        FIT_RGBAF: numpy.float32
        }

    fi_types = {
        (numpy.uint8, 1): FIT_BITMAP,
        (numpy.uint8, 3): FIT_BITMAP,
        (numpy.uint8, 4): FIT_BITMAP,
        (numpy.uint16, 1): FIT_UINT16,
        (numpy.int16, 1): FIT_INT16,
        (numpy.uint32, 1): FIT_UINT32,
        (numpy.int32, 1): FIT_INT32,
        (numpy.float32, 1): FIT_FLOAT,
        (numpy.float64, 1): FIT_DOUBLE,
        (numpy.complex128, 1): FIT_COMPLEX,
        (numpy.uint16, 3): FIT_RGB16,
        (numpy.uint16, 4): FIT_RGBA16,
        (numpy.float32, 3): FIT_RGBF,
        (numpy.float32, 4): FIT_RGBAF
        }

    extra_dims = {
        FIT_UINT16: [],
        FIT_INT16: [],
        FIT_UINT32: [],
        FIT_INT32: [],
        FIT_FLOAT: [],
        FIT_DOUBLE: [],
        FIT_COMPLEX: [],
        FIT_RGB16: [3],
        FIT_RGBA16: [4],
        FIT_RGBF: [3],
        FIT_RGBAF: [4]
        }


class IO_FLAGS(object):
    FIF_LOAD_NOPIXELS = 0x8000 # loading: load the image header only
                               # (not supported by all plugins)

    BMP_DEFAULT = 0
    BMP_SAVE_RLE = 1
    CUT_DEFAULT = 0
    DDS_DEFAULT = 0
    EXR_DEFAULT = 0 # save data as half with piz-based wavelet compression
    EXR_FLOAT = 0x0001 # save data as float instead of as half (not recommended)
    EXR_NONE = 0x0002 # save with no compression
    EXR_ZIP = 0x0004 # save with zlib compression, in blocks of 16 scan lines
    EXR_PIZ = 0x0008 # save with piz-based wavelet compression
    EXR_PXR24 = 0x0010 # save with lossy 24-bit float compression
    EXR_B44 = 0x0020 # save with lossy 44% float compression
                     # - goes to 22% when combined with EXR_LC
    EXR_LC = 0x0040 # save images with one luminance and two chroma channels,
                    # rather than as RGB (lossy compression)
    FAXG3_DEFAULT = 0
    GIF_DEFAULT = 0
    GIF_LOAD256 = 1 # Load the image as a 256 color image with ununsed
                    # palette entries, if it's 16 or 2 color
    GIF_PLAYBACK = 2 # 'Play' the GIF to generate each frame (as 32bpp)
                     # instead of returning raw frame data when loading
    HDR_DEFAULT = 0
    ICO_DEFAULT = 0
    ICO_MAKEALPHA = 1 # convert to 32bpp and create an alpha channel from the
                      # AND-mask when loading
    IFF_DEFAULT = 0
    J2K_DEFAULT = 0 # save with a 16:1 rate
    JP2_DEFAULT = 0 # save with a 16:1 rate
    JPEG_DEFAULT = 0 # loading (see JPEG_FAST);
                     # saving (see JPEG_QUALITYGOOD|JPEG_SUBSAMPLING_420)
    JPEG_FAST = 0x0001 # load the file as fast as possible,
                       # sacrificing some quality
    JPEG_ACCURATE = 0x0002 # load the file with the best quality,
                           # sacrificing some speed
    JPEG_CMYK = 0x0004 # load separated CMYK "as is"
                       # (use | to combine with other load flags)
    JPEG_EXIFROTATE = 0x0008 # load and rotate according to
                             # Exif 'Orientation' tag if available
    JPEG_QUALITYSUPERB = 0x80 # save with superb quality (100:1)
    JPEG_QUALITYGOOD = 0x0100 # save with good quality (75:1)
    JPEG_QUALITYNORMAL = 0x0200 # save with normal quality (50:1)
    JPEG_QUALITYAVERAGE = 0x0400 # save with average quality (25:1)
    JPEG_QUALITYBAD = 0x0800 # save with bad quality (10:1)
    JPEG_PROGRESSIVE = 0x2000 # save as a progressive-JPEG
                              # (use | to combine with other save flags)
    JPEG_SUBSAMPLING_411 = 0x1000 # save with high 4x1 chroma
                                  # subsampling (4:1:1)
    JPEG_SUBSAMPLING_420 = 0x4000 # save with medium 2x2 medium chroma
                                  # subsampling (4:2:0) - default value
    JPEG_SUBSAMPLING_422 = 0x8000 # save with low 2x1 chroma subsampling (4:2:2)
    JPEG_SUBSAMPLING_444 = 0x10000 # save with no chroma subsampling (4:4:4)
    JPEG_OPTIMIZE = 0x20000 # on saving, compute optimal Huffman coding tables
                            # (can reduce a few percent of file size)
    JPEG_BASELINE = 0x40000 # save basic JPEG, without metadata or any markers
    KOALA_DEFAULT = 0
    LBM_DEFAULT = 0
    MNG_DEFAULT = 0
    PCD_DEFAULT = 0
    PCD_BASE = 1 # load the bitmap sized 768 x 512
    PCD_BASEDIV4 = 2 # load the bitmap sized 384 x 256
    PCD_BASEDIV16 = 3 # load the bitmap sized 192 x 128
    PCX_DEFAULT = 0
    PFM_DEFAULT = 0
    PICT_DEFAULT = 0
    PNG_DEFAULT = 0
    PNG_IGNOREGAMMA = 1 # loading: avoid gamma correction
    PNG_Z_BEST_SPEED = 0x0001 # save using ZLib level 1 compression flag
                              # (default value is 6)
    PNG_Z_DEFAULT_COMPRESSION = 0x0006 # save using ZLib level 6 compression
                                       # flag (default recommended value)
    PNG_Z_BEST_COMPRESSION = 0x0009 # save using ZLib level 9 compression flag
                                    # (default value is 6)
    PNG_Z_NO_COMPRESSION = 0x0100 # save without ZLib compression
    PNG_INTERLACED = 0x0200 # save using Adam7 interlacing (use | to combine
                            # with other save flags)
    PNM_DEFAULT = 0
    PNM_SAVE_RAW = 0 #  Writer saves in RAW format (i.e. P4, P5 or P6)
    PNM_SAVE_ASCII = 1 # Writer saves in ASCII format (i.e. P1, P2 or P3)
    PSD_DEFAULT = 0
    PSD_CMYK = 1 # reads tags for separated CMYK (default is conversion to RGB)
    PSD_LAB = 2 # reads tags for CIELab (default is conversion to RGB)
    RAS_DEFAULT = 0
    RAW_DEFAULT = 0 # load the file as linear RGB 48-bit
    RAW_PREVIEW = 1 # try to load the embedded JPEG preview with included
                    # Exif Data or default to RGB 24-bit
    RAW_DISPLAY = 2 # load the file as RGB 24-bit
    SGI_DEFAULT = 0
    TARGA_DEFAULT = 0
    TARGA_LOAD_RGB888 = 1 # Convert RGB555 and ARGB8888 -> RGB888.
    TARGA_SAVE_RLE = 2 # Save with RLE compression
    TIFF_DEFAULT = 0
    TIFF_CMYK = 0x0001 # reads/stores tags for separated CMYK
                       # (use | to combine with compression flags)
    TIFF_PACKBITS = 0x0100 # save using PACKBITS compression
    TIFF_DEFLATE = 0x0200 # save using DEFLATE (a.k.a. ZLIB) compression
    TIFF_ADOBE_DEFLATE = 0x0400 # save using ADOBE DEFLATE compression
    TIFF_NONE = 0x0800 # save without any compression
    TIFF_CCITTFAX3 = 0x1000 # save using CCITT Group 3 fax encoding
    TIFF_CCITTFAX4 = 0x2000 # save using CCITT Group 4 fax encoding
    TIFF_LZW = 0x4000 # save using LZW compression
    TIFF_JPEG = 0x8000 # save using JPEG compression
    TIFF_LOGLUV = 0x10000 # save using LogLuv compression
    WBMP_DEFAULT = 0
    XBM_DEFAULT = 0
    XPM_DEFAULT = 0


class METADATA_MODELS(object):
    FIMD_COMMENTS = 0
    FIMD_EXIF_MAIN = 1
    FIMD_EXIF_EXIF = 2
    FIMD_EXIF_GPS = 3
    FIMD_EXIF_MAKERNOTE = 4
    FIMD_EXIF_INTEROP = 5
    FIMD_IPTC = 6
    FIMD_XMP = 7
    FIMD_GEOTIFF = 8
    FIMD_ANIMATION = 9


class METADATA_DATATYPE(object):
    FIDT_BYTE = 1 # 8-bit unsigned integer
    FIDT_ASCII = 2 # 8-bit bytes w/ last byte null
    FIDT_SHORT = 3 # 16-bit unsigned integer
    FIDT_LONG = 4 # 32-bit unsigned integer
    FIDT_RATIONAL = 5 # 64-bit unsigned fraction
    FIDT_SBYTE = 6 # 8-bit signed integer
    FIDT_UNDEFINED = 7 # 8-bit untyped data
    FIDT_SSHORT = 8 # 16-bit signed integer
    FIDT_SLONG = 9 # 32-bit signed integer
    FIDT_SRATIONAL = 10 # 64-bit signed fraction
    FIDT_FLOAT = 11 # 32-bit IEEE floating point
    FIDT_DOUBLE = 12 # 64-bit IEEE floating point
    FIDT_IFD = 13 # 32-bit unsigned integer (offset)
    FIDT_PALETTE = 14 # 32-bit RGBQUAD

    dtypes = {
        FIDT_BYTE: numpy.uint8,
        FIDT_SHORT: numpy.uint16,
        FIDT_LONG: numpy.uint32,
        FIDT_RATIONAL: [('numerator', numpy.uint32),
                        ('denominator', numpy.uint32)],
        FIDT_SBYTE: numpy.int8,
        FIDT_UNDEFINED: numpy.uint8,
        FIDT_SSHORT: numpy.int16,
        FIDT_SLONG: numpy.int32,
        FIDT_SRATIONAL: [('numerator', numpy.int32),
                         ('denominator', numpy.int32)],
        FIDT_FLOAT: numpy.float32,
        FIDT_DOUBLE: numpy.float64,
        FIDT_IFD: numpy.uint32,
        FIDT_PALETTE: [('R', numpy.uint8), ('G', numpy.uint8),
                       ('B', numpy.uint8), ('A', numpy.uint8)]
        }



class Freeimage(object):
    """ Class to represent an interface to the FreeImage library.
    This class is relatively thin. It provides a Pythonic API without
    the need for ctypes, but that's about it. The actual implementation
    should be provided by the plugins.
    """
    
    _API = {
        # All we're doing here is telling ctypes that some of the FreeImage
        # functions return pointers instead of integers. (On 64-bit systems,
        # without this information the pointers get truncated and crashes result).
        # There's no need to list functions that return ints, or the types of the
        # parameters to these or other functions -- that's fine to do implicitly.
    
        # Note that the ctypes immediately converts the returned void_p back to a
        # python int again! This is really not helpful, because then passing it
        # back to another library call will cause truncation-to-32-bits on 64-bit
        # systems. Thanks, ctypes! So after these calls one must immediately
        # re-wrap the int as a c_void_p if it is to be passed back into FreeImage.
        'FreeImage_AllocateT': (ctypes.c_void_p, None),
        'FreeImage_FindFirstMetadata': (ctypes.c_void_p, None),
        'FreeImage_GetBits': (ctypes.c_void_p, None),
        'FreeImage_GetPalette': (ctypes.c_void_p, None),
        'FreeImage_GetTagKey': (ctypes.c_char_p, None),
        'FreeImage_GetTagValue': (ctypes.c_void_p, None),
        'FreeImage_Load': (ctypes.c_void_p, None),
        'FreeImage_LockPage': (ctypes.c_void_p, None),
        'FreeImage_OpenMultiBitmap': (ctypes.c_void_p, None),
        
        'FreeImage_GetVersion': (ctypes.c_char_p, None),
        'FreeImage_GetFIFExtensionList': (ctypes.c_char_p, None),
        'FreeImage_GetFormatFromFIF': (ctypes.c_char_p, None),
        'FreeImage_GetFIFDescription': (ctypes.c_char_p, None),
        }
    
    
    def __init__(self):
        
        # Initialize freeimage lib as None
        self._lib = None
        
        # Init log messages lists
        self._messages = []
        self._messages2 = []
        
        # Select functype for error handler
        if sys.platform.startswith('win'): 
            functype = ctypes.WINFUNCTYPE
        else: 
            functype = ctypes.CFUNCTYPE
        # Create output message handler
        @functype(None, ctypes.c_int, ctypes.c_char_p)
        def error_handler(fif, message):
            # todo: use fif to produce a better error message
            message = message.decode('utf-8')
            self._messages.append(message)
            self._messages2.append(message)
            while (len(self._messages2)) > 256:
                self._messages2.pop(0)
        
        # Make sure to keep a ref to function
        self._error_handler = error_handler
        
        # Load library and register API
        self._load_freeimage()        
        self._register_api()
        
        # Register logger for output messages
        self._lib.FreeImage_SetOutputMessage(self._error_handler)
        
        # Store version
        self._lib_version = self._lib.FreeImage_GetVersion().decode('utf-8')
    
    
    ## Getting started
    
    def _load_freeimage(self):
        
        # Load
        lib, fname = freeimage_install.load_freeimage(True)
        
        # Store
        self._lib = lib
        self._lib_fname = fname
    
    
    def _register_api(self):
        # Albert's ctypes pattern    
        for f, (restype, argtypes) in self._API.items():
            func = getattr(self._lib, f)
            func.restype = restype
            func.argtypes = argtypes
    
    
    ## Handling of output messages
    
    def _reset_log(self):
        """ Reset the list of output messages. Call this before 
        loading or saving an image with the FreeImage API.
        """
        self._messages = []
    
    def _get_error_message(self):
        """ Get the output messages produced since the last reset as 
        one string. Returns 'No known reason.' if there are no messages. 
        Also resets the log.
        """ 
        if self._messages:
            res = ' '.join(self._messages)
            self._reset_log()
            return res
        else:
           return 'No known reason.'
    
    def _show_any_warnings(self):
        """ If there were any messages since the last reset, show them
        as a warning. Otherwise do nothing. Also resets the messages.
        """ 
        if self._messages:
            print('imageio.freeimage warning: ' + self._get_error_message())
            self._reset_log()
    
    
    def get_output_log(self):
        """ Return a list of the last 256 output messages 
        (warnings and errors) produced by the FreeImage library.
        """ 
        return [m for m in self._messages2]
    
    ## Wrapper functions for reading
    
    
    def read(self, filename, flags=0):
        """Read an image to a numpy array of shape (height, width) for
        greyscale images, or shape (height, width, nchannels) for RGB or
        RGBA images.
        The `flags` parameter should be one or more values from the IO_FLAGS
        class defined in this module, or-ed together with | as appropriate.
        (See the source-code comments for more details.)
        """
        return self._process_bitmap(filename, flags, self._array_from_bitmap)
    
    
    def read_metadata(self, filename):
        """Return a dict containing all image metadata.
    
        Returned dict maps (metadata_model, tag_name) keys to tag values, where
        metadata_model is a string name based on the FreeImage "metadata models"
        defined in the class METADATA_MODELS.
        """
        flags = IO_FLAGS.FIF_LOAD_NOPIXELS
        return self._process_bitmap(filename, flags, self._read_metadata)
    
    
    def read_multipage(self, filename, flags=0):
        """Read a multipage image to a list of numpy arrays, where each
        array is of shape (height, width) for greyscale images, or shape
        (height, width, nchannels) for RGB or RGBA images.
        The `flags` parameter should be one or more values from the IO_FLAGS
        class defined in this module, or-ed together with | as appropriate.
        (See the source-code comments for more details.)
        """
        return self._process_multipage(filename, flags, self._array_from_bitmap)
    
    
    def read_multipage_metadata(self, filename):
        """Read a multipage image to a list of metadata dicts, one dict for each
        page. The dict format is as in read_metadata().
        """
        flags = IO_FLAGS.FIF_LOAD_NOPIXELS
        return self._process_multipage(filename, flags, self._read_metadata)
    
    
    def _process_bitmap(self, filename, flags, process_func):
        """ Load a bitmap and process it with the given function.
        """
        # Get file format
        ftype = self.getFIF(filename, 'r')
        # Try loading and check if all went well
        bitmap = self._lib.FreeImage_Load(ftype, efn(filename), flags)
        bitmap = ctypes.c_void_p(bitmap)
        if not bitmap:
            raise ValueError('Could not load file "%s": %s' 
                        % (filename, self._get_error_message()))
        else:
            self._show_any_warnings()
        # Process
        try:
            return process_func(bitmap)
        finally:
            self._lib.FreeImage_Unload(bitmap)
    
    
    def _process_multipage(self, filename, flags, process_func):
        """ Load a multipage bitmap and process each bitmat with the given function.
        """
        lib = self._lib
        
        ftype = self.getFIF(filename, 'r')
        create_new = False
        read_only = True
        keep_cache_in_memory = True
        # Try opening
        multibitmap = lib.FreeImage_OpenMultiBitmap(ftype, efn(filename), create_new,
                                                    read_only, keep_cache_in_memory,
                                                    flags)
        multibitmap = ctypes.c_void_p(multibitmap)
        if not multibitmap:
            raise ValueError('Could not open file "%s" as multi-page image: %s' 
                            % (filename, self._get_error_message()))
        else:
            self._show_any_warnings()
        
        # Read data
        try:
            pages = lib.FreeImage_GetPageCount(multibitmap)
            out = []
            for i in range(pages):
                # Try loading bitmap
                bitmap = lib.FreeImage_LockPage(multibitmap, i)
                bitmap = ctypes.c_void_p(bitmap)
                if not bitmap:
                    raise ValueError('Could not open file "%s" as a multi-page image: %s'
                            % (filename, self._get_error_message()))
                else:
                    self._show_any_warnings()
                # Process
                try:
                    out.append(process_func(bitmap))
                finally:
                    lib.FreeImage_UnlockPage(multibitmap, bitmap, False)
            return out
        finally:
            lib.FreeImage_CloseMultiBitmap(multibitmap, 0)
    
    
    def _array_from_bitmap(self, bitmap):
        """ Convert a FreeImage bitmap pointer to a numpy array.
        """
        dtype, shape = self._get_type_and_shape(bitmap)
        array = self._wrap_bitmap_bits_in_array(bitmap, shape, dtype)
        # swizzle the color components and flip the scanlines to go from
        # FreeImage's BGR[A] and upside-down internal memory format to something
        # more normal
        def n(arr):
            return arr[..., ::-1].T
        if len(shape) == 3 and self._lib.FreeImage_IsLittleEndian() and \
        dtype.type == numpy.uint8:
            b = n(array[0])
            g = n(array[1])
            r = n(array[2])
            if shape[0] == 3:
                return numpy.dstack( (r, g, b) )
            elif shape[0] == 4:
                a = n(array[3])
                return numpy.dstack( (r, g, b, a) )
            else:
                raise ValueError('Cannot handle images of shape %s' % shape)
    
        # We need to copy because array does *not* own its memory
        # after bitmap is freed.
        return n(array).copy()
    
    
    def _read_metadata(self, bitmap):
        """ or _dict_from_bitmap
        """ 
        lib = self._lib
        
        metadata = {}
        models = [(name[5:], number) for name, number in
            METADATA_MODELS.__dict__.items() if name.startswith('FIMD_')]
    
        tag = ctypes.c_void_p()
        for model_name, number in models:
            mdhandle = lib.FreeImage_FindFirstMetadata(number, bitmap,
                                                    ctypes.byref(tag))
            mdhandle = ctypes.c_void_p(mdhandle)
            if mdhandle:
                more = True
                while more:
                    tag_name = lib.FreeImage_GetTagKey(tag).decode('utf-8')
                    tag_type = lib.FreeImage_GetTagType(tag)
                    byte_size = lib.FreeImage_GetTagLength(tag)
                    char_ptr = ctypes.c_char * byte_size
                    tag_str = char_ptr.from_address(lib.FreeImage_GetTagValue(tag))
                    if tag_type == METADATA_DATATYPE.FIDT_ASCII:
                        tag_val = tag_str.value.decode('utf-8')
                    else:
                        tag_val = numpy.fromstring(tag_str,
                                dtype=METADATA_DATATYPE.dtypes[tag_type])
                        if len(tag_val) == 1:
                            tag_val = tag_val[0]
                    metadata[(model_name, tag_name)] = tag_val
                    more = lib.FreeImage_FindNextMetadata(mdhandle, ctypes.byref(tag))
                lib.FreeImage_FindCloseMetadata(mdhandle)
        return metadata
    
    
    ## Wrapper functions for writing
    
    # todo: filename, array seems a better signature ... and change to save?
    def write(self, array, filename, flags=0):
        """Write a (height, width) or (height, width, nchannels) array to
        a greyscale, RGB, or RGBA image, with file type deduced from the
        filename.
        The `flags` parameter should be one or more values from the IO_FLAGS
        class defined in this module, or-ed together with | as appropriate.
        (See the source-code comments for more details.)
        """
        lib = self._lib
        
        array = numpy.asarray(array)
        ftype = self.getFIF(filename, 'w')
        bitmap, fi_type = self._array_to_bitmap(array)
        try:
            if fi_type == FI_TYPES.FIT_BITMAP:
                can_write = lib.FreeImage_FIFSupportsExportBPP(ftype,
                                        lib.FreeImage_GetBPP(bitmap))
            else:
                can_write = lib.FreeImage_FIFSupportsExportType(ftype, fi_type)
            if not can_write:
                raise TypeError('Cannot save image of this format '
                                'to this file type')
            res = lib.FreeImage_Save(ftype, bitmap, efn(filename), flags)
            if not res:
                raise RuntimeError('Could not save file "%s": %s' 
                        % (filename. self._get_error_message()))
            else:
                self._show_any_warnings()
        finally:
            lib.FreeImage_Unload(bitmap)
    
    
    def write_multipage(self, arrays, filename, flags=0):
        """Write a list of (height, width) or (height, width, nchannels)
        arrays to a multipage greyscale, RGB, or RGBA image, with file type
        deduced from the filename.
        The `flags` parameter should be one or more values from the IO_FLAGS
        class defined in this module, or-ed together with | as appropriate.
        (See the source-code comments for more details.)
        """
        ftype = self.getFIF(filename, 'w')
        create_new = True
        read_only = False
        keep_cache_in_memory = True
        # Try opening
        multibitmap = self._lib.FreeImage_OpenMultiBitmap(ftype, efn(filename),
                                                    create_new, read_only,
                                                    keep_cache_in_memory,
                                                    0) # Set flags at close func
        if not multibitmap:
            raise ValueError('Could not open file "%s" for writing multi-page image: %s' 
                        % (filename, self._get_error_message()))
        else:
            self._show_any_warnings()
        
        # Process each bitmap
        try:
            for array in arrays:
                array = numpy.asarray(array)
                bitmap, fi_type = self._array_to_bitmap(array)
                self._reset_log()
                self._lib.FreeImage_AppendPage(multibitmap, bitmap) # no return value
                self._show_any_warnings()
        finally:
            # Write the image (i.e. flush), set flags here
            self._lib.FreeImage_CloseMultiBitmap(multibitmap, flags)
    
    
    def _array_to_bitmap(self, array):
        """Allocate a FreeImage bitmap and copy a numpy array into it.
    
        """
        lib = self._lib
        
        shape = array.shape
        dtype = array.dtype
        r,c = shape[:2]
        if len(shape) == 2:
            n_channels = 1
            w_shape = (c,r)
        elif len(shape) == 3:
            n_channels = shape[2]
            w_shape = (n_channels,c,r)
        else:
            n_channels = shape[0]
        try:
            fi_type = FI_TYPES.fi_types[(dtype.type, n_channels)]
        except KeyError:
            raise ValueError('Cannot write arrays of given type and shape.')
    
        itemsize = array.dtype.itemsize
        bpp = 8 * itemsize * n_channels
        bitmap = lib.FreeImage_AllocateT(fi_type, c, r, bpp, 0, 0, 0)
        bitmap = ctypes.c_void_p(bitmap)
        if not bitmap:
            raise RuntimeError('Could not allocate image for storage')
        try:
            def n(arr): # normalise to freeimage's in-memory format
                return arr.T[:,::-1]
            wrapped_array = self._wrap_bitmap_bits_in_array(bitmap, w_shape, dtype)
            # swizzle the color components and flip the scanlines to go to
            # FreeImage's BGR[A] and upside-down internal memory format
            if len(shape) == 3 and lib.FreeImage_IsLittleEndian() and \
                dtype.type == numpy.uint8:
                wrapped_array[0] = n(array[:,:,2])
                wrapped_array[1] = n(array[:,:,1])
                wrapped_array[2] = n(array[:,:,0])
                if shape[2] == 4:
                    wrapped_array[3] = n(array[:,:,3])
            else:
                wrapped_array[:] = n(array)
            if len(shape) == 2 and dtype.type == numpy.uint8:
                palette = lib.FreeImage_GetPalette(bitmap)
                palette = ctypes.c_void_p(palette)
                if not palette:
                    raise RuntimeError('Could not get image palette')
                ctypes.memmove(palette, GREY_PALETTE.ctypes.data, 1024)
            return bitmap, fi_type
        except: # Catch BaseException
            lib.FreeImage_Unload(bitmap)
            raise
    
    
    ## Generic wrapper functions
    
    
    def getFIF(self, filename, mode):
        """ Get the freeimage Format (FIF) from a given filename.
        If mode is 'r', will try to determine the format by reading
        the file, otherwise only the filename is used.
        
        This function also tests whether the format supports reading/writing.
        """
        lib = self._lib
        
        # Init
        ftype = -1
        if mode not in 'rw':
            raise ValueError('Invalid mode (must be "r" or "w").')
        
        # Try getting format from file. Note that some files do not have a 
        # header that allows reading the format from the file.
        if mode == 'r':
            ftype = lib.FreeImage_GetFileType(efn(filename), 0)
        # Try getting the format from the extension
        if ftype == -1:
            ftype = lib.FreeImage_GetFIFFromFilename(efn(filename))
        
        # Test if ok
        if ftype == -1:
            raise ValueError('Cannot determine format of file %s' % filename)
        elif mode == 'w' and not lib.FreeImage_FIFSupportsWriting(ftype):
            raise ValueError('Cannot write the format of file %s' % filename)
        elif mode == 'r' and not lib.FreeImage_FIFSupportsReading(ftype):
            raise ValueError('Cannot read the format of file %s' % filename)
        else:
            return ftype
    
    
    def _wrap_bitmap_bits_in_array(self, bitmap, shape, dtype):
        """Return an ndarray view on the data in a FreeImage bitmap. Only
        valid for as long as the bitmap is loaded (if single page) / locked
        in memory (if multipage).
        
        """
        pitch = self._lib.FreeImage_GetPitch(bitmap)
        height = shape[-1]
        byte_size = height * pitch
        itemsize = dtype.itemsize
        
        if len(shape) == 3:
            strides = (itemsize, shape[0]*itemsize, pitch)
        else:
            strides = (itemsize, pitch)
        bits = self._lib.FreeImage_GetBits(bitmap)
        array = numpy.ndarray(shape, dtype=dtype,
                                buffer=(ctypes.c_char*byte_size).from_address(bits),
                                strides=strides)
        return array
    
    
    def _get_type_and_shape(self, bitmap):
        lib = self._lib
        w = lib.FreeImage_GetWidth(bitmap)
        h = lib.FreeImage_GetHeight(bitmap)
        fi_type = lib.FreeImage_GetImageType(bitmap)
        if not fi_type:
            raise ValueError('Unknown image pixel type')
        dtype = FI_TYPES.dtypes[fi_type]
        if fi_type == FI_TYPES.FIT_BITMAP:
            bpp = lib.FreeImage_GetBPP(bitmap)
            if bpp == 8:
                extra_dims = []
            elif bpp == 24:
                extra_dims = [3]
            elif bpp == 32:
                extra_dims = [4]
            else:
                raise ValueError('Cannot convert %d BPP bitmap' % bpp)
        else:
            extra_dims = FI_TYPES.extra_dims[fi_type]
        return numpy.dtype(dtype), extra_dims + [w, h]
