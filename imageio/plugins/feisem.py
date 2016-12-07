# -*- coding: utf-8 -*-
# Copyright (c) 2016, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

from __future__ import absolute_import, unicode_literals

from .tifffile import TiffFormat

from .. import formats


class FEISEMFormat(TiffFormat):
    """Provide read support for TIFFs produced by an FEI SEM microscope."""

    class Reader(TiffFormat.Reader):
        def _get_data(self, index=0, discard_watermark=True,
                      watermark_height=70):
            """Get image and metadata from given index.

            FEI images usually (always?) contain a watermark at the
            bottom of the image, 70 pixels high. We discard this by
            default as it does not contain any information not present
            in the metadata.
            """
            im, meta = super()._get_data(self, index)
            if discard_watermark:
                im = im[:-watermark_height]
            return im, meta

        def _get_meta_data(self, index=None):
            """Read the metadata from an FEI SEM TIFF.

            This metadata is included as ASCII text at the end of the file.

            The index, if provided, is ignored.

            Returns
            -------
            metadata : dict
                Dictionary of metadata.
            """
            md = {'root': {}}
            current_tag = 'root'
            reading_metadata = False
            filename = self.request.get_local_filename()
            with open(filename, 'rb') as fin:
                for line in fin:
                    if not reading_metadata:
                        if not line.startswith(b'Date='):
                            continue
                        else:
                            reading_metadata = True
                    line = line.rstrip().decode()
                    if line.startswith('['):
                        current_tag = line.lstrip('[').rstrip(']')
                        md[current_tag] = {}
                    else:
                        if line and line != '\x00':  # ignore blank lines
                            key, val = line.split('=')
                            md[current_tag][key] = val
            if not md['root'] and len(md) == 1:
                raise ValueError(
                    'Input file %s contains no FEI metadata.' % filename)
            self._meta.update(md)
            return md


# Register plugin
format = FEISEMFormat('fei', 'FEI-SEM TIFF format',
                      extensions=['.tif', '.tiff'],
                      modes='iv')
formats.add_format(format)
