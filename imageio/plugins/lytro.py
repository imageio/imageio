# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Lytro Illum Plugin.
    Plugin to read Lytro Illum .lfr and .raw files as produced
    by the Lytro Illum light field camera.
"""

from __future__ import absolute_import, print_function, division
import os
import json

import numpy as np

from .. import formats
from ..core import Format



# Sensor size of Lytro Illum Lightfieldcamera
LYTRO_IMAGE_SIZE = (5368, 7728)

# Parameter of file format
HEADER_LENGTH = 12
SIZE_LENGTH = 4  # = 16 - header_length
SHA1_LENGTH = 45  # = len("sha1-") + (160 / 4)
PADDING_LENGTH = 35  # = (4 * 16) - header_length - size_length - sha1_length

FILE_HEADER = b'\x89LFP\x0D\x0A\x1A\x0A\x00\x00\x00\x01'
CHUNK_HEADER = b'\x89LFC\x0D\x0A\x1A\x0A\x00\x00\x00\x00'
META_HEADER = b'\x89LFM\x0D\x0A\x1A\x0A\x00\x00\x00\x00'



class LytroFormat(Format):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or write a file. When
    explicitly asked to read, it will simply read the bytes. When
    explicitly asked to write, it will raise an error.

    This documentation is shown when the user does ``help('thisformat')``.

    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.

    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.

    """

    # Only single images are supported.
    _modes = 'i'

    def _can_read(self, request):
        # This method is called when the format manager is searching
        # for a format to read a certain image. Return True if this format
        # can do it.
        #
        # The format manager is aware of the extensions and the modes
        # that each format can handle. It will first ask all formats
        # that *seem* to be able to read it whether they can. If none
        # can, it will ask the remaining formats if they can: the
        # extension might be missing, and this allows formats to provide
        # functionality for certain extensions, while giving preference
        # to other plugins.
        #
        # If a format says it can, it should live up to it. The format
        # would ideally check the request.firstbytes and look for a
        # header of some kind.
        #
        # The request object has:
        # request.filename: a representation of the source (only for reporting)
        # request.firstbytes: the first 256 bytes of the file.
        # request.mode[0]: read or write mode
        # request.mode[1]: what kind of data the user expects: one of 'iIvV?'

        if request.mode[1] in (self.modes + '?'):
            if request.filename.lower().endswith(self.extensions):
                return True

    def _can_write(self, request):
        # This method is called when the format manager is searching
        # for a format to write a certain image. It will first ask all
        # formats that *seem* to be able to write it whether they can.
        # If none can, it will ask the remaining formats if they can.
        #
        # Return True if the format can do it.

        # In most cases, this code does suffice:
        # if request.mode[1] in (self.modes + '?'):
        #     if request.filename.lower().endswith(self.extensions):
        #         return True
        return False

    # -- writer

    class Writer(Format.Writer):

        def _open(self, flags=0):
            # Specify kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to write the data.
            # Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            self._fp = self.request.get_file()

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._fp
            pass

        def _append_data(self, im, meta):
            # Process the given data and meta data.
            raise RuntimeError('The lytro format cannot write image data.')

        def set_meta_data(self, meta):
            # Process the given meta data (global for all images)
            # It is not mandatory to support this.
            raise RuntimeError('The lytro format cannot write meta data.')

class LytroRawFormat(LytroFormat):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or write a file. When
    explicitly asked to read, it will simply read the bytes. When
    explicitly asked to write, it will raise an error.

    This documentation is shown when the user does ``help('thisformat')``.

    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.

    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.

    """

    # -- reader

    class Reader(Format.Reader):

        def _open(self, some_option=False, length=1):
            # Specify kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to get access to the
            # data. Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            # self._fp = self.request.get_file()
            self._fp = open(self.request.get_local_filename(), 'rb')
            self._length = length  # passed as an arg in this case for testing
            self._data = None

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._fp
            pass

        def _get_length(self):
            # Return the number of images. Can be np.inf
            return self._length

        def _get_data(self, index):
            # Return the data and meta data for the given index
            if index not in [0, 'None']:
                raise IndexError('Lytro file contains only one dataset')

            # Read all bytes
            if self._data is None:
                self._data = self._fp.read()

            # Read bytes from string and convert to uint16
            raw = np.fromstring(self._data, dtype=np.uint8).astype(np.uint16)

            # Do bit rearrangement
            t0 = raw[0::5]
            t1 = raw[1::5]
            t2 = raw[2::5]
            t3 = raw[3::5]
            lsb = raw[4::5]

            t0 = np.left_shift(t0, 2) + np.bitwise_and(lsb, 3)
            t1 = np.left_shift(t1, 2) \
                 + np.right_shift(np.bitwise_and(lsb, 12), 2)
            t2 = np.left_shift(t2, 2) \
                 + np.right_shift(np.bitwise_and(lsb, 48), 4)
            t3 = np.left_shift(t3, 2) \
                 + np.right_shift(np.bitwise_and(lsb, 192), 6)

            image = np.zeros(LYTRO_IMAGE_SIZE, dtype=np.uint16)
            image[:, 0::4] = t0.reshape(
                (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
            image[:, 1::4] = t1.reshape(
                (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
            image[:, 2::4] = t2.reshape(
                (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
            image[:, 3::4] = t3.reshape(
                (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))

            # Return array and dummy meta data
            return image, self._get_meta_data(index=0)

        def _get_meta_data(self, index):
            # Get the meta data for the given index. If index is None, it
            # should return the global meta data.

            if index not in [0, None]:
                raise IndexError(
                    'Lytro meta data file contains only one dataset')

            # Try to read meta data from meta data file corresponding
            # to the raw data file, extension in [.txt, .TXT, .json, .JSON]
            filename_base = os.path.splitext(
                self.request.get_local_filename())[0]

            meta_data = None

            for ext in ['.txt', '.TXT', '.json', '.JSON']:
                if os.path.isfile(filename_base + ext):
                    meta_data = json.load(open(filename_base + ext))

            if meta_data is not None:
                return meta_data

            else:
                print("No metadata file found for provided raw file.")
                return {}

class LytroLfrFormat(LytroFormat):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or write a file. When
    explicitly asked to read, it will simply read the bytes. When
    explicitly asked to write, it will raise an error.

    This documentation is shown when the user does ``help('thisformat')``.

    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.

    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.

    """

    # -- reader

    class Reader(Format.Reader):

        def _open(self, some_option=False, length=1):
            # Specify kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to get access to the
            # data. Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            self._fp = self.request.get_file()
            self._length = length  # passed as an arg in this case for testing
            self._data = None

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._fp
            pass

        def _get_length(self):
            # Return the number of images. Can be np.inf
            return self._length

        def _get_data(self, index):
            # Return the data and meta data for the given index
            if index >= self._length:
                raise IndexError('Image index %i > %i' % (index, self._length))
            # Read all bytes
            if self._data is None:
                self._data = self._fp.read()
            # Put in a numpy array
            im = np.frombuffer(self._data, 'uint8')
            im.shape = len(im), 1
            # Return array and dummy meta data
            return im, {}

        def _get_meta_data(self, index):
            # Get the meta data for the given index. If index is None, it
            # should return the global meta data.
            return {}  # This format does not support meta data




## Create the formats

SPECIAL_CLASSES = {'lytro-raw': LytroRawFormat,
                   'lytro-lfr': LytroLfrFormat
                   }

# Supported Formats.
# Only single image files supported.
file_formats = [
    ('LYTRO-RAW', 'Lytro Illum raw image file', 'raw', 'i'),
    ('LYTRO-LFR', 'Lytro Illum lfr image file', 'lfr', 'i')
]
#
# fiformats = LytroFormat('lytro-lfr',  # short name
#                      'Lytro raw lfr data format.',  # one line descr.
#                      '.lfr .raw',  # list of extensions
#                      'i'  # modes, characters in iIvV
#                      )

# formats.add_format(format)


def _create_predefined_freeimage_formats():
    for name, des, ext, i in file_formats:
        # Get format class for format
        FormatClass = SPECIAL_CLASSES.get(name.lower(), LytroFormat)
        if FormatClass:
            # Create Format and add
            format = FormatClass(name, des, ext, i)
            formats.add_format(format)


# Register all created formats.
_create_predefined_freeimage_formats()
