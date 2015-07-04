# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Storage of image data in tiff format.
"""

from __future__ import absolute_import, print_function, division

from .. import formats
from ..core import Format

import numpy as np

try:
    import tifffile as _tifffile
except ImportError:
    import _tifffile


TIFF_FORMATS = ('.tif', '.tiff', '.stk', '.lsm')


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
    photometric : {'minisblack', 'miniswhite', 'rgb'}
            The color space of the image data.
            By default this setting is inferred from the data shape.
    planarconfig : {'contig', 'planar'}
        Specifies if samples are stored contiguous or in separate planes.
        By default this setting is inferred from the data shape.
        'contig': last dimension contains samples.
        'planar': third last dimension contains samples.
    resolution : (float, float) or ((int, int), (int, int))
        X and Y resolution in dots per inch as float or rational numbers.
    description : str
        The subject of the image. Saved with the first page only.
    compress : int
        Values from 0 to 9 controlling the level of zlib compression.
        If 0, data are written uncompressed (default).
    volume : bool
        If True, volume data are stored in one tile (if applicable) using
        the SGI image_depth and tile_depth tags.
        Image width and depth must be multiple of 16.
        Few software can read this format, e.g. MeVisLab.
    writeshape : bool
        If True, write the data shape to the image_description tag
        if necessary and no other description is given.
    extratags: sequence of tuples
        Additional tags as [(code, dtype, count, value, writeonce)].

        code : int
            The TIFF tag Id.
        dtype : str
            Data type of items in 'value' in Python struct format.
            One of B, s, H, I, 2I, b, h, i, f, d, Q, or q.
        count : int
            Number of data values. Not used for string values.
        value : sequence
            'Count' values compatible with 'dtype'.
        writeonce : bool
            If True, the tag is written to the first page only.
    """

    def _can_read(self, request):
        if request.filename.lower().endswith(TIFF_FORMATS):
            return True  # We support any kind of image data
        else:
            return False

    def _can_write(self, request):
        if request.filename.lower().endswith(TIFF_FORMATS):
            return True  # We support any kind of image data
        else:
            return False

    # -- reader

    class Reader(Format.Reader):

        def _open(self):
            self._tf = _tifffile.TiffFile(self.request.filename)

        def _close(self):
            self._tf.close()

        def _get_length(self):
            print('get length', len(self._tf))
            print(len(self._tf.series), len(self._tf.pages))
            return len(self._tf)

        def _get_data(self, index):
            # Get data
            if index < 0 or index >= len(self._tf):
                raise IndexError(
                    'Index out of range while reading from tiff file')
            im = self._tf[index].asarray()
            # Return array and empty meta data
            return im, {}

        def _get_meta_data(self, index):
            raise RuntimeError('The tifffile format does not support meta data.')

    # -- writer

    class Writer(Format.Writer):

        def _open(self, bigtiff=None, byteorder=None, software=None,
                  **kwargs):
            self._parameters = kwargs
            self._tf = _tifffile.TiffWriter(self.request.filename,
                                            bigtiff, byteorder, software)

        def _close(self):
            self._tf.close()

        def _append_data(self, im, meta):
            # ignore metadata
            self._tf.save(np.asanyarray(im), **self._parameters)

        def set_meta_data(self, meta):
            raise RuntimeError('The tifffile format does not support meta data.')


# Register
format = TiffFormat('tifffile', "TIFF format", 'tif tiff stk lsm', 'iIvV')
formats.add_format(format)
