# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Storage of image data in tiff format.
"""

from __future__ import absolute_import, print_function, division

from .. import formats
from ..core import Format

_itk = None  # Defer loading to load_lib() function.


def load_lib():
    global _itk
    try:
        import SimpleITK as _itk
    except ImportError:
        raise ImportError("SimpleITK could not be found. "
                          "Please try "
                          "  easy_install SimpleITK "
                          "or refer to "
                          "  http://simpleitk.org/ "
                          "for further instructions.")
    return _itk


# Split up in real ITK and all supported formats. Right now we say we
# can do all. But we could also only publish the ITK_FORMATS, yet check
# on ALL_FORMATS in _can_read.
ITK_FORMATS = ('.gipl', '.ipl', '.mhd', '.nhdr', '.nrrd', '.vtk', 
               '.dicom', '.gdcm')
ALL_FORMATS = ITK_FORMATS + ('.bmp', '.jpeg', '.jpg', '.png', '.tiff', '.tif')


class ItkFormat(Format):

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
        return request.filename.lower().endswith(ALL_FORMATS)

    def _can_write(self, request):
        # We support any kind of image data
        return request.filename.lower().endswith(ALL_FORMATS)

    # -- reader

    class Reader(Format.Reader):

        def _open(self, **kwargs):
            if not _itk:
                load_lib()
            self._img = _itk.ReadImage(self.request.get_local_filename())

        def _get_length(self):
            return 1

        def _close(self):
            pass

        def _get_data(self, index):
            # Get data
            if index != 0:
                raise IndexError(
                    'Index out of range while reading from itk file')

            # Return array and empty meta data
            return _itk.GetArrayFromImage(self._img), {}

        def _get_meta_data(self, index):
            raise RuntimeError('The itk format does not support '
                               ' meta data.')

    # -- writer
    class Writer(Format.Writer):

        def _open(self):
            if not _itk:
                load_lib()

        def _close(self):
            pass

        def _append_data(self, im, meta):
            _itk_img = _itk.GetImageFromArray(im, isVector=True)
            _itk.WriteImage(_itk_img, self.request.get_local_filename())

        def set_meta_data(self, meta):
            raise RuntimeError('The itk format does not support '
                               ' meta data.')

# Register
title = "Insight Segmentation and Registration Toolkit (ITK) format"
format = ItkFormat('itk', title, ' '.join(ALL_FORMATS), 'iIvV')
formats.add_format(format)
