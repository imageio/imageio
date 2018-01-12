# -*- coding: utf-8 -*-
# Copyright (c) 2018, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.
#

""" Lytro Illum Plugin.
    Plugin to read Lytro Illum .lfr and .raw files as produced
    by the Lytro Illum light field camera.
"""
#
#
# This code is based on work by
# David Uhlig and his lfr_reader
#   (https://www.iiit.kit.edu/uhlig.php)
# Donald Dansereau and his Matlab LF Toolbox
#   (http://dgd.vision/Tools/LFToolbox/)
# and Behnam Esfahbod and his Python LFP-Reader
#   (https://github.com/behnam/python-lfp-reader/)


from __future__ import absolute_import, print_function, division
import os
import json
import struct

import numpy as np

from .. import formats
from ..core import Format


# Sensor size of Lytro Illum light field camera sensor
LYTRO_IMAGE_SIZE = (5368, 7728)

# Parameter of lfr file format
HEADER_LENGTH = 12
SIZE_LENGTH = 4  # = 16 - header_length
SHA1_LENGTH = 45  # = len("sha1-") + (160 / 4)
PADDING_LENGTH = 35  # = (4*16) - header_length - size_length - sha1_length
DATA_CHUNKS = 11


class LytroFormat(Format):
    """ Base class for Lytro format.
    The subclasses LytroLfrFormat and LytroRawFormat implement
    the Lytro-LFR and Lytro-RAW format respectively.
    Writing is not supported.

    """

    # Only single images are supported.
    _modes = 'i'

    def _can_read(self, request):
        # Check if mode and extensions are supported by the format
        if request.mode[1] in (self.modes + '?'):
            if request.filename.lower().endswith(self.extensions):
                return True

    def _can_write(self, request):
        # Writing of Lytro RAW and LFR files is not supported
        return False

    # -- writer

    class Writer(Format.Writer):

        def _open(self, flags=0):
            self._fp = self.request.get_file()

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._fp
            pass

        def _append_data(self, im, meta):
            # Process the given data and meta data.
            raise RuntimeError('The lytro format cannot write image data.')

        def _set_meta_data(self, meta):
            # Process the given meta data (global for all images)
            # It is not mandatory to support this.
            raise RuntimeError('The lytro format cannot write meta data.')


class LytroRawFormat(LytroFormat):
    """ This is the Lytro Illum RAW format.
    The raw format is a 10bit image format as used by the Lytro Illum
    light field camera. The format will read the specified raw file and will
    try to load a .txt or .json file with the associated meta data.
    This format does not support writing.


    Parameters for reading
    ----------------------
    None

    """

    @staticmethod
    def rearrange_bits(array):
        # Do bit rearrangement for the 10-bit lytro raw format
        # Normalize output to 1.0 as float64
        t0 = array[0::5]
        t1 = array[1::5]
        t2 = array[2::5]
        t3 = array[3::5]
        lsb = array[4::5]

        t0 = np.left_shift(t0, 2) + np.bitwise_and(lsb, 3)
        t1 = np.left_shift(t1, 2) + np.right_shift(
            np.bitwise_and(lsb, 12), 2)
        t2 = np.left_shift(t2, 2) + np.right_shift(
            np.bitwise_and(lsb, 48), 4)
        t3 = np.left_shift(t3, 2) + np.right_shift(
            np.bitwise_and(lsb, 192), 6)

        image = np.zeros(LYTRO_IMAGE_SIZE, dtype=np.uint16)
        image[:, 0::4] = t0.reshape(
            (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
        image[:, 1::4] = t1.reshape(
            (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
        image[:, 2::4] = t2.reshape(
            (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))
        image[:, 3::4] = t3.reshape(
            (LYTRO_IMAGE_SIZE[0], LYTRO_IMAGE_SIZE[1] // 4))

        # Normalize data to 1.0 as 64-bit float.
        # Division is by 1023 as the Lytro saves 10-bit raw data.
        return np.divide(image, 1023).astype(np.float64)

    # -- reader

    class Reader(Format.Reader):

        def _open(self):
            self._file = self.request.get_file()
            self._data = None

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._file
            del self._data

        def _get_length(self):
            # Return the number of images.
            return 1

        def _get_data(self, index):
            # Return the data and meta data for the given index

            if index not in [0, 'None']:
                raise IndexError('Lytro file contains only one dataset')

            # Read all bytes
            if self._data is None:
                self._data = self._file.read()

            # Read bytes from string and convert to uint16
            raw = np.frombuffer(self._data, dtype=np.uint8).astype(np.uint16)

            # Rearrange bits
            img = LytroRawFormat._rearrange_bits(raw)

            # Return image and meta data
            return img, self._get_meta_data(index=0)

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
    """ This is the Lytro Illum LFR format.
    The lfr is a image and meta data container format as used by the
    Lytro Illum light field camera.
    The format will read the specified lfr file.
    This format does not support writing.

    Parameters for reading
    ----------------------
    None

    """

    # -- reader

    class Reader(Format.Reader):

        def _open(self):
            self._file = self.request.get_file()
            self._data = None
            self._chunks = {}
            self._content = None

            self._find_header()
            self._find_chunks()
            self._find_meta()

            try:
                # Get sha1 dict and check if it is in dictionary of data chunks
                chunk_dict = self._content['frames'][0]['frame']
                if chunk_dict['metadataRef'] in self._chunks and \
                        chunk_dict['imageRef'] in self._chunks and \
                        chunk_dict['privateMetadataRef'] in self._chunks:

                    # Read raw image data byte buffer
                    data_pos, size = self._chunks[chunk_dict['imageRef']]
                    self._file.seek(data_pos, 0)
                    self.raw_image_data = self._file.read(size)

                    # Read meta data
                    data_pos, size = self._chunks[chunk_dict['metadataRef']]
                    self._file.seek(data_pos, 0)
                    metadata = self._file.read(size)
                    self.metadata = json.loads(metadata.decode('ASCII'))

                    # Read private metadata
                    data_pos, size = self._chunks[
                        chunk_dict['privateMetadataRef']]
                    self._file.seek(data_pos, 0)
                    serial_numbers = self._file.read(size)
                    self.serial_numbers = json.loads(
                        serial_numbers.decode('ASCII'))

                    # Add private meta data to meta data dict
                    self.metadata['privateMetadata'] = self.serial_numbers

            except KeyError:
                raise RuntimeError(
                    "The specified file is not a valid LFR file.")

        def _close(self):
            # Close the reader.
            # Note that the request object will close self._file
            del self._data

        def _get_length(self):
            # Return the number of images. Can be np.inf
            return 1

        def _find_header(self):
            """
            Checks if file has correct header and skip it.
            """
            file_header = b'\x89LFP\x0D\x0A\x1A\x0A\x00\x00\x00\x01'
            # Read and check header of file
            header = self._file.read(HEADER_LENGTH)
            if header != file_header:
                raise RuntimeError("The LFR file header is invalid.")

            # Read first bytes to skip header
            self._file.read(SIZE_LENGTH)

        def _find_chunks(self):
            """
            Gets start position and size of data chunks in file.
            """
            chunk_header = b'\x89LFC\x0D\x0A\x1A\x0A\x00\x00\x00\x00'

            for i in range(0, DATA_CHUNKS):
                data_pos, size, sha1 = self._get_chunk(chunk_header)
                self._chunks[sha1] = (data_pos, size)

        def _find_meta(self):
            """
            Gets a data chunk that contains information over content
            of other data chunks.
            """
            meta_header = b'\x89LFM\x0D\x0A\x1A\x0A\x00\x00\x00\x00'
            data_pos, size, sha1 = self._get_chunk(meta_header)

            # Get content
            self._file.seek(data_pos, 0)
            data = self._file.read(size)
            self._content = json.loads(data.decode('ASCII'))

        def _get_chunk(self, header):
            """
            Checks if chunk has correct header and skips it.
            Finds start position and length of next chunk and reads
            sha1-string that identifies the following data chunk.

            Parameters
            ----------
            header : bytes
                Byte string that identifies start of chunk.

            Returns
            -------
                data_pos : int
                    Start position of data chunk in file.
                size : int
                    Size of data chunk.
                sha1 : str
                    Sha1 value of chunk.

            """
            # Read and check header of chunk
            header_chunk = self._file.read(HEADER_LENGTH)
            if header_chunk != header:
                raise RuntimeError("The LFR chunk header is invalid.")

            data_pos = None
            sha1 = None

            # Read size
            size = struct.unpack(">i", self._file.read(SIZE_LENGTH))[0]
            if size > 0:
                # Read sha1
                sha1 = str(self._file.read(SHA1_LENGTH).decode('ASCII'))
                # Skip fixed null chars
                self._file.read(PADDING_LENGTH)
                # Find start of data and skip data
                data_pos = self._file.tell()
                self._file.seek(size, 1)
                # Skip extra null chars
                ch = self._file.read(1)
                while ch == b'\0':
                    ch = self._file.read(1)
                self._file.seek(-1, 1)

            return data_pos, size, sha1

        def _get_data(self, index):
            # Return the data and meta data for the given index
            if index not in [0, None]:
                raise IndexError(
                    'Lytro lfr file contains only one dataset')

            # Read bytes from string and convert to uint16
            raw = np.frombuffer(self.raw_image_data, dtype=np.uint8).astype(
                np.uint16)
            im = LytroRawFormat.rearrange_bits(raw)

            # Return array and dummy meta data
            return im, self.metadata

        def _get_meta_data(self, index):
            # Get the meta data for the given index. If index is None,
            # it returns the global meta data.
            if index not in [0, None]:
                raise IndexError(
                    'Lytro meta data file contains only one dataset')

            return self.metadata


# Create the formats
SPECIAL_CLASSES = {'lytro-raw': LytroRawFormat,
                   'lytro-lfr': LytroLfrFormat
                   }

# Supported Formats.
# Only single image files supported.
file_formats = [
    ('LYTRO-RAW', 'Lytro Illum raw image file', 'raw', 'i'),
    ('LYTRO-LFR', 'Lytro Illum lfr image file', 'lfr', 'i')
]


def _create_predefined_lytro_formats():
    for name, des, ext, i in file_formats:
        # Get format class for format
        FormatClass = SPECIAL_CLASSES.get(name.lower(), LytroFormat)
        if FormatClass:
            # Create Format and add
            format = FormatClass(name, des, ext, i)
            formats.add_format(format)


# Register all created formats.
_create_predefined_lytro_formats()
