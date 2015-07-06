# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Storage of image data in tiff format.
"""

from __future__ import absolute_import, print_function, division

from .. import formats
from ..core import Format

import numpy as np

tifffile = None  # Defer loading to lib() function.


def lib():
    global tifffile
    try:
        import tifffile
    except ImportError:
        from . import _tifffile as tifffile
    return tifffile


TIFF_FORMATS = ('.tif', '.tiff', '.stk', '.lsm')
WRITE_METADATA_KEYS = ('photometric', 'planarconfig', 'resolution',
                       'description', 'compress', 'volume', 'writeshape',
                       'extratags')
READ_METADATA_KEYS = ('planar_configuration', 'is_fluoview', 'is_nih',
                      'is_contiguous', 'is_micromanager', 'is_ome',
                      'is_palette', 'is_reduced', 'is_rgb', 'is_sgi',
                      'is_shaped', 'is_stk', 'is_tiled',
                      'resolution_unit', 'compression',
                      'fill_order', 'orientation', 'predictor')


class TiffFormat(Format):

    """ Provides support for a wide range of Tiff images.

    Parameters for reading
    ----------------------
    None

    Parameters for saving
    ---------------------
    bigtiff : bool
        If True, the BigTIFF format is used.
    byteorder : {'<', '>'}
        The endianness of the data in the file.
        By default this is the system's native byte order.
    software : str
        Name of the software used to create the image.
        Saved with the first page only.
    """

    def _can_read(self, request):
        # We support any kind of image data
        return request.filename.lower().endswith(TIFF_FORMATS)

    def _can_write(self, request):
        # We support any kind of image data
        return request.filename.lower().endswith(TIFF_FORMATS)

    # -- reader

    class Reader(Format.Reader):

        def _open(self):
            self._tf = lib().TiffFile(self.request.get_file())
            # metadata is the same for all images
            self._meta = {}

        def _close(self):
            self._tf.close()

        def _get_length(self):
            return len(self._tf)

        def _get_data(self, index):
            # Get data
            if index < 0 or index >= len(self._tf):
                raise IndexError(
                    'Index out of range while reading from tiff file')
            im = self._tf[index].asarray()
            meta = self._meta or self._get_meta_data(index)
            # Return array and empty meta data
            return im, meta

        def _get_meta_data(self, index):
            page = self._tf[index or 0]
            for key in READ_METADATA_KEYS:
                try:
                    self._meta[key] = getattr(page, key)
                except:
                    pass
            return self._meta

    # -- writer
    class Writer(Format.Writer):

        def _open(self, bigtiff=None, byteorder=None, software=None):
            self._meta = {}
            self._tf = lib().TiffWriter(self.request.get_local_filename(),
                                        bigtiff, byteorder, software)

        def _close(self):
            self._tf.close()

        def _append_data(self, im, meta):
            meta = meta or self._meta
            print(meta)
            self._tf.save(np.asanyarray(im), **meta)

        def set_meta_data(self, meta):
            self._meta = {}
            for (key, value) in meta.items():
                if key in WRITE_METADATA_KEYS:
                    self._meta[key] = value

# Register
format = TiffFormat('tiff', "TIFF format", 'tif tiff stk lsm', 'iIvV')
formats.add_format(format)
