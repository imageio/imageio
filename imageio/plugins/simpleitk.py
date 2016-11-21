# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Storage of image data in tiff format.
"""

from __future__ import absolute_import, print_function, division

from .. import formats
from ..core import Format, has_module

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


# Split up in real ITK and all supported formats.
ITK_FORMATS = ('.gipl', '.ipl', '.mha', '.mhd', '.nhdr', '.nii', '.nrrd',
               '.vtk')
ALL_FORMATS = ITK_FORMATS + ('.bmp', '.jpeg', '.jpg', '.png', '.tiff', '.tif',
                             '.dicom', '.gdcm')


class ItkFormat(Format):
    """ The ItkFormat uses the simpleITK library to support a range of
    ITK-related formats. It also supports a few common formats that are
    also supported by the freeimage plugin (e.g. PNG and JPEG).
    
    This format requires the ``simpleITK`` package.

    Parameters for reading
    ----------------------
    None.

    Parameters for saving
    ---------------------
    None.

    """

    def _can_read(self, request):
        # If the request is a format that only this plugin can handle,
        # we report that we can do it; a useful error will be raised
        # when simpleitk is not installed. For the more common formats
        # we only report that we can read if the library is installed.
        if request.filename.lower().endswith(ITK_FORMATS):
            return True
        if has_module('SimpleITK'):
            return request.filename.lower().endswith(ALL_FORMATS)

    def _can_write(self, request):
        if request.filename.lower().endswith(ITK_FORMATS):
            return True
        if has_module('SimpleITK'):
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
