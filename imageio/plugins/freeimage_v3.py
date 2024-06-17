# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

"""Read/Write images using FreeImage.

Backend Library: `FreeImage <https://freeimage.sourceforge.io/>`_

.. note::
    To use this plugin you have to install its backend::

        imageio_download_bin freeimage

    or you can download the backend using the function::

        imageio.plugins.freeimage.download()

Each Freeimage format has the ``flags`` keyword argument. See the `Freeimage
documentation <https://freeimage.sourceforge.io/>`_ for more information.

Parameters
----------
request : Request
    A request object representing the resource to be operated on.

Methods
-------

.. autosummary::
    :toctree: _plugins/pillow

    FreeimagePlugin.read
    FreeimagePlugin.write
    FreeimagePlugin.iter
    FreeimagePlugin.metadata
    FreeimagePlugin.properties

"""

from typing import Any, Dict, Iterator, List, Optional, Union

import numpy
import numpy as np

from ._freeimage import fi, FIBitmap, FIMultipageBitmap, IO_FLAGS
from ..core import image_as_uint
from ..core.request import URI_BYTES, InitializationError, Request, IOMode
from ..core.v3_plugin_api import ImageProperties, PluginV3
from ..typing import ArrayLike


class FreeimagePlugin(PluginV3):
    @staticmethod
    def flags(_fif: int, _io_mode: IOMode, _flags: int = 0, **kwargs) -> int:
        if _fif == 0:  # BMP
            if _io_mode == IOMode.write:
                _flags |= IO_FLAGS.BMP_SAVE_RLE if kwargs.get('compression', False) else IO_FLAGS.BMP_DEFAULT
        elif _fif == 1:  # ICO
            if _io_mode == IOMode.read:
                _flags |= IO_FLAGS.ICO_MAKEALPHA if kwargs.get('makealpha', True) else 0
        elif _fif == 2:  # JPG
            if _io_mode == IOMode.read:
                _flags |= IO_FLAGS.JPEG_EXIFROTATE if kwargs.get('exifrotate', True) and kwargs.get('exifrotate', True) != 2 else 0
                _flags |= IO_FLAGS.JPEG_ACCURATE if not kwargs.get('quickread', False) else 0
            else:
                quality = int(kwargs.get('quality', 75))
                # Test quality
                if quality < 1 or quality > 100:
                    raise ValueError("JPEG quality should be between 1 and 100.")
                # Build flags from kwargs
                _flags |= quality
                _flags |= IO_FLAGS.JPEG_PROGRESSIVE if kwargs.get('progressive', False) else 0
                _flags |= IO_FLAGS.JPEG_OPTIMIZE if kwargs.get('optimize', False) else 0
                _flags |= IO_FLAGS.JPEG_BASELINE if kwargs.get('baseline', False) else 0
        elif _fif == 13:  # PNG
            if _io_mode == IOMode.read:
                _flags |= IO_FLAGS.PNG_IGNOREGAMMA if kwargs.get('ignoregamma', True) else 0
            else:
                _flags |= IO_FLAGS.PNG_INTERLACED if kwargs.get('interlaced', False) else 0
                compression_map = {
                    0: IO_FLAGS.PNG_Z_NO_COMPRESSION,
                    1: IO_FLAGS.PNG_Z_BEST_SPEED,
                    6: IO_FLAGS.PNG_Z_DEFAULT_COMPRESSION,
                    9: IO_FLAGS.PNG_Z_BEST_COMPRESSION,
                }
                try:
                    _flags |= compression_map[kwargs.get('compression', 9)]
                except KeyError:
                    raise ValueError("Png compression must be 0, 1, 6, or 9.")
        elif _fif == 25:  # GIF
            if _io_mode == IOMode.write:
                _flags |= IO_FLAGS.GIF_PLAYBACK if kwargs.get('playback', True) else 0
        elif _fif in [7, 8, 11, 12, 14, 15]:  # PBM, PGM, PPM
            if _io_mode == IOMode.write:
                _flags |= IO_FLAGS.PNM_SAVE_ASCII if kwargs.get('use_ascii', True) else 0

        return _flags

    def __init__(self, request: Request, flags: int = 0, **kwargs) -> None:
        super().__init__(request)
        self._bm, self._io_mode = None, request.mode.io_mode

        _fif = -1
        if fi.has_lib():
            try:
                _fif = fi.getFIF(request.filename, self._io_mode.value, request.firstbytes if self._io_mode == IOMode.read else None)
            except Exception as e:
                _fif = -1

        if _fif < 0 or (_fif == 6 and self._io_mode == IOMode.write):
            if request._uri_type == URI_BYTES:
                raise InitializationError(f"Freeimage can not {self._io_mode.name} the provided bytes.") from None
            else:
                raise InitializationError(f"Freeimage can not {self._io_mode.name} {request.raw_uri}.") from None

        _flags = self.flags(_fif, self._io_mode, flags, **kwargs)
        self._bm = (fi.create_multipage_bitmap if _fif in [1, 6, 25] else fi.create_bitmap)(request.filename, _fif, _flags)
        self._kwargs = kwargs
        if _fif == 25 and self._io_mode == IOMode.write:
            self._bm.set_meta_data({'ANIMATION': {'Loop': np.array([kwargs.get('loop', 0)]).astype(np.uint32)}})
        else:
            self._bm.set_meta_data({})
        # print(inspect.currentframe().f_code.co_name, self._kwargs)

    def close(self) -> None:
        if self._bm is not None:
            self._bm.close()
        super().close()

    def update_flags(self, flags: int = 0, **kwargs):
        self._kwargs.update(kwargs)
        _new_flags = self.flags(self._bm._ftype, self._io_mode, flags, **self._kwargs)
        if _new_flags != self._bm._flags:
            _fif = self._bm._ftype
            _meta = self._bm.get_meta_data()
            self._bm.close()
            self._bm = (fi.create_multipage_bitmap if _fif in [1, 6, 25] else fi.create_bitmap)(self.request.filename, _fif, _new_flags)
            self._bm.set_meta_data(_meta)

    def iter(self, *, flags: int = 0, **kwargs) -> Iterator[np.ndarray]:
        self.update_flags(flags, **kwargs)
        # print(inspect.currentframe().f_code.co_name, self._kwargs)

        self._bm.load_from_filename(self.request.filename)
        if isinstance(self._bm, FIBitmap):
            for index in range(1):
                yield self._bm.get_image_data()
            raise StopIteration
        elif isinstance(self._bm, FIMultipageBitmap):
            for index in range(len(self._bm)):
                yield self._bm.get_page(index).get_image_data()
            raise StopIteration
        else:
            raise InitializationError('Can not iterate with current settings.')

    def read_common(self, *, index: Optional[int] = 0, flags: int = 0, **kwargs):
        self._bm.load_from_filename(self.request.filename)
        if isinstance(self._bm, FIMultipageBitmap) and index is None:
            return numpy.stack([ndimage for ndimage in self.iter()], axis=0)
        elif isinstance(self._bm, FIMultipageBitmap) and isinstance(index, int):
            return self._bm.get_page(index).get_image_data()
        elif isinstance(self._bm, FIBitmap) and index == 0:
            return self._bm.get_image_data()
        elif isinstance(self._bm, FIBitmap) and index != 0:
            raise IndexError('This format only supports singleton images.')
        else:
            raise RuntimeError('Can not read image with unknown error. Please check the settings and contact with author if necessary.')

    def write_common(self, ndimage: Union[ArrayLike, List[ArrayLike]], *, flags: int = 0, **kwargs):
        if isinstance(self._bm, FIBitmap) and isinstance(ndimage, ArrayLike):
            self._bm.allocate(ndimage)
            self._bm.set_image_data(ndimage)
        elif isinstance(self._bm, FIBitmap) and isinstance(ndimage, List) and len(ndimage) == 1:
            self._bm.allocate(ndimage[0])
            self._bm.set_image_data(ndimage[0])
        elif isinstance(self._bm, FIBitmap) and isinstance(ndimage, List) and len(ndimage) != 1:
            if len(ndimage) > 1:
                raise RuntimeError('Can not write singleton image with multiple image data.')
        elif isinstance(self._bm, FIMultipageBitmap):
            if ndimage is not None:
                for nd_item in ndimage if isinstance(ndimage, List) else [ndimage]:
                    _ap = fi.create_bitmap(self._bm._filename, self._bm._ftype, self._bm._flags)
                    _ap.allocate(nd_item), _ap.set_image_data(nd_item)
                    _ap.set_meta_data({})
                    self._bm.append_bitmap(_ap)
        self._bm.save_to_filename(self.request.filename)

    def write_gif_sp(self, ndimage: Union[ArrayLike, List[ArrayLike]], *, flags: int = 0, **kwargs):
        def gif_get_sub_rectangles(prev, curr):
            """
            Calculate the minimal rectangles that need updating each frame.
            Returns a two-element tuple containing the cropped images and a
            list of x-y positions.
            """
            # Get difference, sum over colors
            diff = np.abs(curr - prev)
            if diff.ndim == 3:
                diff = diff.sum(2)
            # Get begin and end for both dimensions
            X = np.argwhere(diff.sum(0))
            Y = np.argwhere(diff.sum(1))
            # Get rect coordinates
            if X.size and Y.size:
                x0, x1 = int(X[0]), int(X[-1]) + 1
                y0, y1 = int(Y[0]), int(Y[-1]) + 1
            else:  # No change ... make it minimal
                x0, x1 = 0, 2
                y0, y1 = 0, 2
            # Cut out and return
            return curr[y0:y1, x0:x1], (x0, y0)

        # Check palettesize
        palettesize = kwargs.get('palettesize', 256)
        if palettesize < 2 or palettesize > 256:
            raise ValueError("GIF quantize param must be 2..256")
        if palettesize not in [2, 4, 8, 16, 32, 64, 128, 256]:
            palettesize = 2 ** int(np.log2(128) + 0.999)
            logger.warning("Warning: palettesize (%r) modified to a factor of "  "two between 2-256." % palettesize)

        # Check quantizer
        quantizer = {"wu": 0, "nq": 1}.get(kwargs.get('quantizer', 'Wu').lower(), None)
        if quantizer is None:
            raise ValueError('Invalid quantizer, must be "wu" or "nq".')

        # Check frametime
        duration = kwargs.get('duration', None)
        if duration is None:
            _frametime = [int(1000 / float(fps) + 0.5)]
        elif isinstance(duration, list):
            _frametime = [int(1000 * d) for d in duration]
        elif isinstance(duration, (float, int)):
            _frametime = [int(1000 * duration)]
        else:
            raise ValueError("Invalid value for duration: %r" % duration)

        # Check subrectangles
        _subrectangles = bool(kwargs.get('subrectangles', False))

        # Prepare meta data
        meta = meta.copy()
        meta_a = meta["ANIMATION"] = {}

        # If this is the first frame, assign it our "global" meta data
        if len(self._bm) == 0:
            meta.update(self._bm.get_meta_data())
            meta_a = meta["ANIMATION"]

        # Set frame time
        index = len(self._bm)
        if index < len(_frametime):
            ft = _frametime[index]
        else:
            ft = _frametime[-1]
        meta_a["FrameTime"] = np.array([ft]).astype(np.uint32)

        # Check array
        if im.ndim == 3 and im.shape[-1] == 4:
            im = im[:, :, :3]

        # Process subrectangles
        _prev_im = None
        im_uncropped = im
        if _subrectangles and _prev_im is not None:
            im, xy = gif_get_sub_rectangles(_prev_im, im)
            meta_a["DisposalMethod"] = np.array([1]).astype(np.uint8)
            meta_a["FrameLeft"] = np.array([xy[0]]).astype(np.uint16)
            meta_a["FrameTop"] = np.array([xy[1]]).astype(np.uint16)
        _prev_im = im_uncropped

        # Set image data
        sub2 = sub1 = bitmap
        sub1.allocate(im)
        sub1.set_image_data(im)

        # Quantize it if its RGB
        if im.ndim == 3 and im.shape[-1] == 3:
            sub2 = sub1.quantize(_quantizer, _palettesize)

        # Set meta data and return
        sub2.set_meta_data(meta)
        return sub2

    def read(self, *, index: Optional[int] = 0, flags: int = 0, **kwargs) -> np.ndarray:
        self.update_flags(flags, **kwargs)
        # print(inspect.currentframe().f_code.co_name, self._kwargs)

        # Read
        ndimage = self.read_common(index=index, flags=flags, **self._kwargs)

        # Post
        if self._bm._ftype == 2:  # JPG
            if self._kwargs.get("exifrotate", None) == 2:
                try:
                    ori = self._bm.get_meta_data()["EXIF_MAIN"]["Orientation"]
                except KeyError:  # pragma: no cover
                    pass  # Orientation not available
                else:  # pragma: no cover - we cannot touch all cases
                    # www.impulseadventure.com/photo/exif-orientation.html
                    if ori in [1, 2]:
                        pass
                    if ori in [3, 4]:
                        ndimage = np.rot90(ndimage, 2)
                    if ori in [5, 6]:
                        ndimage = np.rot90(ndimage, 3)
                    if ori in [7, 8]:
                        ndimage = np.rot90(ndimage)
                    if ori in [2, 4, 5, 7]:  # Flipped cases (rare)
                        ndimage = np.fliplr(ndimage)

        # Return
        return ndimage

    def write(self, ndimage: Union[ArrayLike, List[ArrayLike]], *, flags: int = 0, **kwargs) -> None:
        self.update_flags(flags, **kwargs)
        # print(inspect.currentframe().f_code.co_name, self._kwargs)

        # Pre Procs
        if self._bm._ftype == 2:  # JPG
            if ndimage.ndim == 3 and ndimage.shape[-1] == 4:
                raise IOError("JPEG does not support alpha channel.")

        if self._bm._ftype in [0, 2]:  # BMP & JPG
            ndimage = image_as_uint(ndimage, bitdepth=8)
        elif self._bm._ftype == 13:  # PNG
            if str(ndimage.dtype) == "uint16":
                ndimage = image_as_uint(ndimage, bitdepth=16)
            else:
                ndimage = image_as_uint(ndimage, bitdepth=8)

        # Write
        if self._bm._ftype == 25:  # GIF:
            self.write_gif_sp(ndimage=ndimage, flags=flags, **self._kwargs)
        else:
            self.write_common(ndimage=ndimage, flags=flags, **self._kwargs)

        # Post
        if self._bm._ftype == 13:  # PNG
            q = int(self._kwargs.get("quantize", False))
            if not q:
                pass
            elif not (ndimage.ndim == 3 and ndimage.shape[-1] == 3):
                raise ValueError("Can only quantize RGB images")
            elif q < 2 or q > 256:
                raise ValueError("PNG quantize param must be 2..256")
            else:
                bm = self._bm.quantize(0, q)
                self._bm.close()
                self._bm = bm

    def metadata(self, index: Optional[int] = 0, exclude_applied: bool = True) -> Dict[str, Any]:
        self._bm.load_from_filename(self.request.filename)
        if isinstance(self._bm, FIMultipageBitmap) and index is None:
            return self._bm.get_meta_data()
        elif isinstance(self._bm, FIMultipageBitmap) and isinstance(index, int):
            return self._bm.get_page(index).get_meta_data()
        elif isinstance(self._bm, FIBitmap) and index == 0:
            return self._bm.get_meta_data()
        elif isinstance(self._bm, FIBitmap) and index != 0:
            raise IndexError(f'Index {index} is out of range. This format only supports singleton images.')
        else:
            raise RuntimeError('Can not read image with unknown error. Please check the settings and contact with author if necessary.')

    def properties(self, index: Optional[int] = 0) -> ImageProperties:
        self._bm.load_from_filename(self.request.filename)
        if isinstance(self._bm, FIMultipageBitmap) and index is None:
            result = numpy.stack([ndimage for ndimage in self.iter()], axis=0)
            return ImageProperties(shape=result.shape, dtype=result.dtype, n_images=result.shape[0], is_batch=True)
        elif isinstance(self._bm, FIMultipageBitmap) and isinstance(index, int):
            result = self._bm.get_page(index).get_image_data()
            return ImageProperties(shape=result.shape, dtype=result.dtype, n_images=1, is_batch=False)
        elif isinstance(self._bm, FIBitmap) and index == 0:
            result = self._bm.get_image_data()
            return ImageProperties(shape=result.shape, dtype=result.dtype, n_images=1, is_batch=False)
        elif isinstance(self._bm, FIBitmap) and index != 0:
            raise IndexError(f'Index {index} is out of range. '
                             f'This format only supports singleton images.')
        else:
            raise RuntimeError('Can not read image with unknown error.'
                               'Please check the settings and contact with author if necessary.')
