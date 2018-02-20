# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

from __future__ import absolute_import, print_function, division

from warnings import warn
import numpy as np
import threading

from .. import formats
from ..core import Format, image_as_uint

# Get info about pillow formats without having to import PIL
from .pillow_info import pillow_formats, pillow_docs

# todo: Pillow ImageGrab module supports grabbing the screen on Win and OSX.


GENERIC_DOCS = """
    Parameters for reading
    ----------------------
    
    pilmode : str
        From the Pillow documentation:
        
        * 'L' (8-bit pixels, grayscale)
        * 'P' (8-bit pixels, mapped to any other mode using a color palette)
        * 'RGB' (3x8-bit pixels, true color)
        * 'RGBA' (4x8-bit pixels, true color with transparency mask)
        * 'CMYK' (4x8-bit pixels, color separation)
        * 'YCbCr' (3x8-bit pixels, color video format)
        * 'I' (32-bit signed integer pixels)
        * 'F' (32-bit floating point pixels)
        
        PIL also provides limited support for a few special modes, including
        'LA' ('L' with alpha), 'RGBX' (true color with padding) and 'RGBa'
        (true color with premultiplied alpha).
        
        When translating a color image to grayscale (mode 'L', 'I' or 'F'),
        the library uses the ITU-R 601-2 luma transform::
        
            L = R * 299/1000 + G * 587/1000 + B * 114/1000
    as_gray : bool
        If True, the image is converted using mode 'F'. When `mode` is
        not None and `as_gray` is True, the image is first converted
        according to `mode`, and the result is then "flattened" using
        mode 'F'.
"""


class PillowFormat(Format):
    """
    Base format class for Pillow formats.
    """
    
    _pillow_imported = False
    _Image = None
    _modes = 'i'
    _description = ''

    def __init__(self, *args, **kwargs):
        super(PillowFormat, self).__init__(*args, **kwargs)
        # Used to synchronize _init_pillow(), see #244
        self._lock = threading.RLock()

    @property
    def plugin_id(self):
        """ The PIL plugin id.
        """
        return self._plugin_id  # Set when format is created
    
    def _init_pillow(self):
        with self._lock:
            if not self._pillow_imported:
                self._pillow_imported = True  # more like tried to import
                import PIL
                if not hasattr(PIL, 'PILLOW_VERSION'):  # pragma: no cover
                    raise ImportError('Imageio Pillow requires '
                                      'Pillow, not PIL!')
                from PIL import Image
                self._Image = Image
            elif self._Image is None:  # pragma: no cover
                raise RuntimeError('Imageio Pillow plugin requires '
                                   'Pillow lib.')
            Image = self._Image

        if self.plugin_id in ('PNG', 'JPEG', 'BMP', 'GIF', 'PPM'):
            Image.preinit()
        else:
            Image.init()
        return Image
    
    def _can_read(self, request):
        Image = self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if self.plugin_id in Image.OPEN:
                factory, accept = Image.OPEN[self.plugin_id]
                if accept:
                    if request.firstbytes and accept(request.firstbytes):
                        return True
    
    def _can_write(self, request):
        Image = self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if request.extension in self.extensions:
                if self.plugin_id in Image.SAVE:
                    return True
    
    class Reader(Format.Reader):
    
        def _open(self, pilmode=None, as_gray=False):
            Image = self.format._init_pillow()
            try:
                factory, accept = Image.OPEN[self.format.plugin_id]
            except KeyError:
                raise RuntimeError('Format %s cannot read images.' %
                                   self.format.name)
            self._fp = self.request.get_file()
            self._im = factory(self._fp, '')
            if hasattr(Image, '_decompression_bomb_check'):
                Image._decompression_bomb_check(self._im.size)
            pil_try_read(self._im)
            # Store args
            self._kwargs = dict(mode=pilmode, as_gray=as_gray,
                                is_gray=_palette_is_grayscale(self._im))
            # Set length
            self._length = 1
            if hasattr(self._im, 'n_frames'):
                self._length = self._im.n_frames
        
        def _close(self):
            save_pillow_close(self._im)
            # request object handled closing the _fp
        
        def _get_length(self):
            return self._length
        
        def _seek(self, index):
            try:
                self._im.seek(index)
            except EOFError:
                raise IndexError('Could not seek to index %i' % index)
        
        def _get_data(self, index):
            if index >= self._length:
                raise IndexError('Image index %i > %i' % (index, self._length))
            i = self._im.tell()
            if i > index:
                self._seek(index)  # just try
            else:
                while i < index:  # some formats need to be read in sequence
                    i += 1
                    self._seek(i)
            self._im.getdata()[0]
            im = pil_get_frame(self._im, **self._kwargs)
            return im, self._im.info
        
        def _get_meta_data(self, index):
            if not (index is None or index == 0):
                raise IndexError()
            return self._im.info
    
    class Writer(Format.Writer):
        
        def _open(self):
            Image = self.format._init_pillow()
            try:
                self._save_func = Image.SAVE[self.format.plugin_id]
            except KeyError:
                raise RuntimeError('Format %s cannot write images.' %
                                   self.format.name)
            self._fp = self.request.get_file()
            self._meta = {}
            self._written = False
        
        def _close(self):
            pass  # request object handled closing _fp
        
        def _append_data(self, im, meta):
            if self._written:
                raise RuntimeError('Format %s only supports single images.' %
                                   self.format.name)
            # Pop unit dimension for grayscale images
            if im.ndim == 3 and im.shape[-1] == 1:
                im = im[:, :, 0]
            self._written = True
            self._meta.update(meta)
            img = ndarray_to_pil(im, self.format.plugin_id)
            if 'bits' in self._meta:
                img = img.quantize()  # Make it a P image, so bits arg is used
            img.save(self._fp, format=self.format.plugin_id, **self._meta)
            save_pillow_close(img)
        
        def set_meta_data(self, meta):
            self._meta.update(meta)


class PNGFormat(PillowFormat):
    """A PNG format based on Pillow.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for reading
    ----------------------
    ignoregamma : bool
        Avoid gamma correction. Default False.
    
    Parameters for saving
    ---------------------
    optimize : bool
        If present and true, instructs the PNG writer to make the output file
        as small as possible. This includes extra processing in order to find
        optimal encoder settings.
    transparency: 
        This option controls what color image to mark as transparent.
    dpi: tuple of two scalars
        The desired dpi in each direction.
    pnginfo: PIL.PngImagePlugin.PngInfo
        Object containing text tags.
    compress_level: int
        ZLIB compression level, a number between 0 and 9: 1 gives best speed,
        9 gives best compression, 0 gives no compression at all. Default is 9.
        When ``optimize`` option is True ``compress_level`` has no effect
        (it is set to 9 regardless of a value passed).
    compression: int
        Compatibility with the freeimage PNG format. If given, it overrides
        compress_level.
    icc_profile:
        The ICC Profile to include in the saved file.
    bits (experimental): int
        This option controls how many bits to store. If omitted,
        the PNG writer uses 8 bits (256 colors).
    quantize: 
        Compatibility with the freeimage PNG format. If given, it overrides
        bits. In this case, given as a number between 1-256.
    dictionary (experimental): dict
        Set the ZLIB encoder dictionary.
    pilmode : str
        From the Pillow documentation:
        
        * 'L' (8-bit pixels, grayscale)
        * 'P' (8-bit pixels, mapped to any other mode using a color palette)
        * 'RGB' (3x8-bit pixels, true color)
        * 'RGBA' (4x8-bit pixels, true color with transparency mask)
        * 'CMYK' (4x8-bit pixels, color separation)
        * 'YCbCr' (3x8-bit pixels, color video format)
        * 'I' (32-bit signed integer pixels)
        * 'F' (32-bit floating point pixels)
        
        PIL also provides limited support for a few special modes, including
        'LA' ('L' with alpha), 'RGBX' (true color with padding) and 'RGBa'
        (true color with premultiplied alpha).
        
        When translating a color image to grayscale (mode 'L', 'I' or 'F'),
        the library uses the ITU-R 601-2 luma transform::
        
            L = R * 299/1000 + G * 587/1000 + B * 114/1000
    as_gray : bool
        If True, the image is converted using mode 'F'. When `mode` is
        not None and `as_gray` is True, the image is first converted
        according to `mode`, and the result is then "flattened" using
        mode 'F'.
    """
    
    class Reader(PillowFormat.Reader):
        def _open(self, pilmode=None, as_gray=False, ignoregamma=False):
            return PillowFormat.Reader._open(self,
                                             pilmode=pilmode, as_gray=as_gray)
        
        def _get_data(self, index):
            im, info = PillowFormat.Reader._get_data(self, index)
            if not self.request.kwargs.get('ignoregamma', False):
                try:
                    gamma = float(info['gamma'])
                except (KeyError, ValueError):
                    pass
                else:
                    scale = float(65536 if im.dtype == np.uint16 else 255)
                    gain = 1.0
                    im = ((im / scale) ** gamma) * scale * gain
            return im, info
                    
    # -- 
    
    class Writer(PillowFormat.Writer):
        def _open(self, compression=None, quantize=None, interlaced=False,
                  **kwargs):
            
            # Better default for compression
            kwargs['compress_level'] = kwargs.get('compress_level', 9)
            
            if compression is not None:
                if compression < 0 or compression > 9:
                    raise ValueError('Invalid PNG compression level: %r' %
                                     compression)
                kwargs['compress_level'] = compression
            if quantize is not None:
                for bits in range(1, 9):
                    if 2**bits == quantize:
                        break
                else:
                    raise ValueError('PNG quantize must be power of two, '
                                     'not %r' % quantize)
                kwargs['bits'] = bits
            if interlaced:
                warn('PIL PNG writer cannot produce interlaced images.')
            
            ok_keys = ('optimize', 'transparency', 'dpi', 'pnginfo', 'bits',
                       'compress_level', 'icc_profile', 'dictionary')
            for key in kwargs:
                if key not in ok_keys:
                    raise TypeError('Invalid arg for PNG writer: %r' % key)
            
            PillowFormat.Writer._open(self)
            self._meta.update(kwargs)
        
        def _append_data(self, im, meta):
            if str(im.dtype) == 'uint16' and (im.ndim == 2 or
                                              im.shape[-1] == 1):
                im = image_as_uint(im, bitdepth=16)
            else:
                im = image_as_uint(im, bitdepth=8)
            PillowFormat.Writer._append_data(self, im, meta)


class JPEGFormat(PillowFormat):
    """A JPEG format based on Pillow.
    
    This format supports grayscale, RGB and RGBA images.
    
    Parameters for reading
    ----------------------
    exifrotate : bool
        Automatically rotate the image according to exif flag. Default True.
    
    Parameters for saving
    ---------------------
    quality : scalar
        The compression factor of the saved image (1..100), higher
        numbers result in higher quality but larger file size. Default 75.
    progressive : bool
        Save as a progressive JPEG file (e.g. for images on the web).
        Default False.
    optimize : bool
        On saving, compute optimal Huffman coding tables (can reduce a few
        percent of file size). Default False.
    dpi : tuple of int
        The pixel density, ``(x,y)``.
    icc_profile : object
        If present and true, the image is stored with the provided ICC profile.
        If this parameter is not provided, the image will be saved with no
        profile attached.
    exif : dict
        If present, the image will be stored with the provided raw EXIF data.
    subsampling : str
        Sets the subsampling for the encoder. See Pillow docs for details.
    qtables : object
        Set the qtables for the encoder. See Pillow docs for details.
    pilmode : str
        From the Pillow documentation:
        
        * 'L' (8-bit pixels, grayscale)
        * 'P' (8-bit pixels, mapped to any other mode using a color palette)
        * 'RGB' (3x8-bit pixels, true color)
        * 'RGBA' (4x8-bit pixels, true color with transparency mask)
        * 'CMYK' (4x8-bit pixels, color separation)
        * 'YCbCr' (3x8-bit pixels, color video format)
        * 'I' (32-bit signed integer pixels)
        * 'F' (32-bit floating point pixels)
        
        PIL also provides limited support for a few special modes, including
        'LA' ('L' with alpha), 'RGBX' (true color with padding) and 'RGBa'
        (true color with premultiplied alpha).
        
        When translating a color image to grayscale (mode 'L', 'I' or 'F'),
        the library uses the ITU-R 601-2 luma transform::
        
            L = R * 299/1000 + G * 587/1000 + B * 114/1000
    as_gray : bool
        If True, the image is converted using mode 'F'. When `mode` is
        not None and `as_gray` is True, the image is first converted
        according to `mode`, and the result is then "flattened" using
        mode 'F'.
    """
    
    class Reader(PillowFormat.Reader):
        def _open(self, pilmode=None, as_gray=False, exifrotate=True):
            return PillowFormat.Reader._open(self,
                                             pilmode=pilmode, as_gray=as_gray)
        
        def _get_data(self, index):
            im, info = PillowFormat.Reader._get_data(self, index)
            
            # Handle exif
            if 'exif' in info:
                from PIL.ExifTags import TAGS
                info['EXIF_MAIN'] = {}
                for tag, value in self._im._getexif().items():
                    decoded = TAGS.get(tag, tag)
                    info['EXIF_MAIN'][decoded] = value
            
            im = self._rotate(im, info)
            return im, info
        
        def _rotate(self, im, meta):
            """ Use Orientation information from EXIF meta data to 
            orient the image correctly. Similar code as in FreeImage plugin.
            """
            if self.request.kwargs.get('exifrotate', True):
                try:
                    ori = meta['EXIF_MAIN']['Orientation']
                except KeyError:  # pragma: no cover
                    pass  # Orientation not available
                else:  # pragma: no cover - we cannot touch all cases
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
    
    class Writer(PillowFormat.Writer):
        def _open(self, quality=75, progressive=False, optimize=False,
                  **kwargs):
            
            # Check quality - in Pillow it should be no higher than 95
            quality = int(quality)
            if quality < 1 or quality > 100:
                raise ValueError('JPEG quality should be between 1 and 100.')
            quality = min(95, max(1, quality))
            
            kwargs['quality'] = quality
            kwargs['progressive'] = bool(progressive)
            kwargs['optimize'] = bool(progressive)
            
            PillowFormat.Writer._open(self)
            self._meta.update(kwargs)
        
        def _append_data(self, im, meta):
            if im.ndim == 3 and im.shape[-1] == 4:
                raise IOError('JPEG does not support alpha channel.')
            im = image_as_uint(im, bitdepth=8)
            PillowFormat.Writer._append_data(self, im, meta)
            return


def save_pillow_close(im):
    # see issue #216 and #300
    if hasattr(im, 'close'):
        if hasattr(getattr(im, 'fp', None), 'close'):
            im.close()


## Func from skimage

# This cells contains code from scikit-image, in particular from
# http://github.com/scikit-image/scikit-image/blob/master/
# skimage/io/_plugins/pil_plugin.py 
# The scikit-image license applies.


def pil_try_read(im):
    try:
        # this will raise an IOError if the file is not readable
        im.getdata()[0]
    except IOError as e:
        site = "http://pillow.readthedocs.org/en/latest/installation.html"
        site += "#external-libraries"
        pillow_error_message = str(e)
        error_message = ('Could not load "%s" \n'
                         'Reason: "%s"\n'
                         'Please see documentation at: %s'
                         % (im.filename, pillow_error_message, site))
        raise ValueError(error_message)


def _palette_is_grayscale(pil_image):
    if pil_image.mode != 'P':
        return False
    # get palette as an array with R, G, B columns
    palette = np.asarray(pil_image.getpalette()).reshape((256, 3))
    # Not all palette colors are used; unused colors have junk values.
    start, stop = pil_image.getextrema()
    valid_palette = palette[start:stop]
    # Image is grayscale if channel differences (R - G and G - B)
    # are all zero.
    return np.allclose(np.diff(valid_palette), 0)

    
def pil_get_frame(im, is_gray=None, as_gray=None, mode=None, dtype=None):
    """ 
    is_gray: Whether the image *is* gray (by inspecting its palette).
    as_gray: Whether the resulting image must be converted to gaey.
    mode: The mode to convert to.
    """
    
    if is_gray is None:
        is_gray = _palette_is_grayscale(im)
    
    frame = im
    
    # Convert ...
    if mode is not None:
        # Mode is explicitly given ...
        if mode != im.mode:
            frame = im.convert(mode)
    elif as_gray:
        pass  # don't do any auto-conversions (but do the explit one above)
    elif im.mode == 'P' and is_gray:
        # Paletted images that are already gray by their palette
        # are converted so that the resulting numpy array is 2D.
        frame = im.convert('L')
    elif im.mode == 'P':
        # Paletted images are converted to RGB/RGBA. We jump some loops to make
        # this work well.
        if im.info.get('transparency', None) is not None:
            # Let Pillow apply the transparency, see issue #210 and #246
            frame = im.convert('RGBA')
        elif im.palette.mode in ('RGB', 'RGBA'):
            # We can do this ourselves. Pillow seems to sometimes screw
            # this up if a  multi-gif has a pallete for each frame ...
            # Create palette array
            p = np.frombuffer(im.palette.getdata()[1], np.uint8)
            # Shape it.
            nchannels = len(im.palette.mode)
            p.shape = -1, nchannels
            if p.shape[1] == 3:
                p = np.column_stack((p, 255*np.ones(p.shape[0], p.dtype)))
            # Apply palette
            frame_paletted = np.array(im, np.uint8)
            try:
                frame = p[frame_paletted]
            except Exception:
                # Ok, let PIL do it. The introduction of the branch that
                # tests `im.info['transparency']` should make this happen
                # much less often, but let's keep it, to be safe.
                frame = im.convert('RGBA')
        else:
            # Let Pillow do it. Unlinke skimage, we always convert
            # to RGBA; palettes can be RGBA.
            if True:  # im.format == 'PNG' and 'transparency' in im.info:
                frame = im.convert('RGBA')
            else:
                frame = im.convert('RGB')
    elif 'A' in im.mode:
        frame = im.convert('RGBA')
    elif im.mode == 'CMYK':
        frame = im.convert('RGB')
    
    # Apply a post-convert if necessary
    if as_gray:
        frame = frame.convert('F')  # Scipy compat
    elif not isinstance(frame, np.ndarray) and frame.mode == '1':
        # Workaround for crash in PIL. When im is 1-bit, the call array(im)
        # can cause a segfault, or generate garbage. See
        # https://github.com/scipy/scipy/issues/2138 and
        # https://github.com/python-pillow/Pillow/issues/350.
        #
        # This converts im from a 1-bit image to an 8-bit image. 
        frame = frame.convert('L')
    
    # Convert to numpy array
    if im.mode.startswith('I;16'):
        # e.g. in16 PNG's
        shape = im.size
        dtype = '>u2' if im.mode.endswith('B') else '<u2'
        if 'S' in im.mode:
            dtype = dtype.replace('u', 'i')
        frame = np.fromstring(frame.tobytes(), dtype)
        frame.shape = shape[::-1]
    else:
        # Use uint16 for PNG's in mode I
        if im.format == 'PNG' and im.mode == 'I' and dtype is None:
            dtype = 'uint16'
        frame = np.array(frame, dtype=dtype)

    return frame


def ndarray_to_pil(arr, format_str=None):
    
    from PIL import Image
    
    if arr.ndim == 3:
        arr = image_as_uint(arr, bitdepth=8)
        mode = {3: 'RGB', 4: 'RGBA'}[arr.shape[2]]

    elif format_str in ['png', 'PNG']:
        mode = 'I;16'
        mode_base = 'I'

        if arr.dtype.kind == 'f':
            arr = image_as_uint(arr)

        elif arr.max() < 256 and arr.min() >= 0:
            arr = arr.astype(np.uint8)
            mode = mode_base = 'L'

        else:
            arr = image_as_uint(arr, bitdepth=16)

    else:
        arr = image_as_uint(arr, bitdepth=8)
        mode = 'L'
        mode_base = 'L'

    array_buffer = arr.tobytes()
    
    if arr.ndim == 2:
        im = Image.new(mode_base, arr.T.shape)
        im.frombytes(array_buffer, 'raw', mode)
    else:
        image_shape = (arr.shape[1], arr.shape[0])
        im = Image.frombytes(mode, image_shape, array_buffer)
    
    return im


## End of code from scikit-image


from .pillowmulti import GIFFormat, TIFFFormat

IGNORE_FORMATS = 'MPEG'

SPECIAL_FORMATS = dict(PNG=PNGFormat, JPEG=JPEGFormat,
                       GIF=GIFFormat, TIFF=TIFFFormat)


def register_pillow_formats():
    
    for id, summary, ext in pillow_formats:
        if id in IGNORE_FORMATS:
            continue
        FormatCls = SPECIAL_FORMATS.get(id, PillowFormat)
        summary = FormatCls._description or summary
        format = FormatCls(id + '-PIL', summary, ext, FormatCls._modes)
        format._plugin_id = id
        if FormatCls is PillowFormat or not FormatCls.__doc__:
            format.__doc__ = pillow_docs[id] + GENERIC_DOCS
        formats.add_format(format)


register_pillow_formats()
