# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Storage of image data in tiff format.
"""

from __future__ import absolute_import, print_function, division

from .. import formats
from ..core import Format

_sitk = None  # Defer loading to load_lib() function.


def load_lib():
    global _sitk
    try:
        import SimpleITK as _sitk
    except ImportError:
        raise ImportError("SimpleITK could not be found. "
                          "Please try "
                          "  easy_install SimpleITK "
                          "or refer to "
                          "  http://simpleitk.org/ "
                          "for further instructions.")
    return _sitk


SITK_FORMATS = ('bmp', 'dicom', 'gdcm', 'gipl', 'ipl', 'jpeg', 'jpg',
                'mhd', 'nhdr', 'nrrd', 'png', 'tiff', 'tif', 'vtk')


class SitkFormat(Format):

    """

    Parameters for reading
    ----------------------
    None.

    Parameters for saving
    ---------------------
    None.

    """

    def _can_read(self, request):
        # We support any kind of image data
        return request.filename.lower().endswith(SITK_FORMATS)

    def _can_write(self, request):
        # We support any kind of image data
        return request.filename.lower().endswith(SITK_FORMATS)

    # -- reader

    class Reader(Format.Reader):

        def _open(self, **kwargs):
            if not _sitk:
                load_lib()
            self._img = _sitk.ReadImage(self.request.get_local_filename())

        def _get_length(self):
            return 1

        def _get_data(self, index):
            # Get data
            if index != 0:
                raise IndexError(
                    'Index out of range while reading from simpleitk file')

            # Return array and empty meta data
            meta = self._get_meta_data(index)
            return _sitk.GetArrayFromImage(self._img), meta

        def _get_meta_data(self, index):
            _sitk.GetMetaData(self._img)

    # -- writer
    class Writer(Format.Writer):

        def _open(self):
            if not _sitk:
                load_lib()

        def _close(self):
            pass

        def _append_data(self, im, meta):
            _sitk_img = _sitk.GetImageFromArray(im, isVector=True)
            _sitk.WriteImage(_sitk_img, self.request.get_local_filename())

        def set_meta_data(self, meta):
            raise RuntimeError('The simpleitk format does not support '
                               ' meta data.')

# Register
title = "Insight Segmentation and Registration Toolkit (ITK) format"
format = SitkFormat('simpleitk', title, ' '.join(SITK_FORMATS), 'iIvV')
formats.add_format(format)
