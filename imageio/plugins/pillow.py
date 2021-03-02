# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

import numpy as np
from PIL import (
    Image, UnidentifiedImageError, ImageSequence, ExifTags
)

from ..core.imopen import Plugin


def _exif_orientation_transform(orientation, mode):
    # get transformation that transforms an image from a
    # given EXIF orientation into the standard orientation

    # -1 if the mode has color channel, 0 otherwise
    axis_offset = {
        "1": -1,
        "L": -1,
        "P": -1,
        "RGB": -2,
        "RGBA": -2,
        "CMYK": -2,
        "YCbCr": -2,
        "LAB": -2,
        "HSV": -2,
        "I": -1,
        "F": -1,
        "LA": -2,
        "PA": -2,
        "RGBX": -2,
        "RGBa": -2,
        "La": -1,
        "I;16": -1,
        "I:16L": -1,
        "I;16N": -1,
        "BGR;15": -2,
        "BGR;16": -2,
        "BGR;24": -2,
        "BGR;32": -2
    }

    axis = axis_offset[mode]

    EXIF_ORIENTATION = {
        1: lambda x: x,
        2: lambda x: np.flip(x, axis=axis),
        3: lambda x: np.rot90(x, k=2),
        4: lambda x: np.flip(x, axis=axis - 1),
        5: lambda x: np.flip(np.rot90(x, k=3), axis=axis),
        6: lambda x: np.rot90(x, k=1),
        7: lambda x: np.flip(np.rot90(x, k=1), axis=axis),
        8: lambda x: np.rot90(x, k=3)
    }

    return EXIF_ORIENTATION[orientation]


class PillowPlugin(Plugin):
    def __init__(self, uri):
        """ Instantiate a new Pillow Plugin Object

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        """
        self._uri = uri
        self._image = None

    def close(self):
        if self._image:
            self._image.close()

    def read(self, *, index=None, mode=None, rotate=False, formats=None):
        """
        Parses the given URI and creates a ndarray from it.

        Parameters
        ----------
        index : {integer}
            If the URI contains a list of ndimages (multiple frames) return the
            index-th image/frame. If None, read all ndimages (frames) in the URI
            and attempt to stack them along a new 0-th axis (equivalent to
            np.stack(imgs, axis=0))
        mode : {str, None}
            Convert the image to the given mode before returning it. If None,
            the mode will be left unchanged. Possible modes can be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        rotate : {bool}
            If set to ``True`` and the image contains an EXIF orientation tag,
            apply the orientation before returning the ndimage.
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.

        Returns
        -------
        ndimage : ndarray
            A numpy array containing the loaded image data

        Notes
        -----
        If you open a GIF - or any other format using color pallets - you may
        wish to manually set the `mode` parameter. Otherwise, the numbers in
        the returned image will refer to the entries in the color pallet, which
        is discarded during conversion to ndarray.

        """
        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        if index is not None:
            # will raise IO error if index >= number of frames in image
            self._image.seek(index)

            if mode is not None:
                image = np.asarray(self._image.convert(mode))
            else:
                image = np.asarray(self._image)

            meta = self.get_meta()
            if rotate and "Orientation" in meta:
                transformation = _exif_orientation_transform(
                    meta["Orientation"],
                    self._image.mode
                )
                image = transformation(image)
            return image
        else:
            iterator = self.iter(mode=mode, formats=formats, rotate=rotate)
            image = np.stack([im for im in iterator], axis=0)
            if image.shape[0] == 1:
                image = np.squeeze(image, axis=0)
            return image

    def iter(self, *, mode=None, rotate=False, formats=None):
        """
        Iterate over all ndimages/frames in the URI

        Parameters
        ----------
        mode : {str, None}
            Convert the image to the given mode before returning it. If None,
            the mode will be left unchanged. Possible modes can be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        rotate : {bool}
            If set to ``True`` and the image contains an EXIF orientation tag,
            apply the orientation before returning the ndimage.
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.
        """

        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        for im in ImageSequence.Iterator(self._image):
            # import pdb; pdb.set_trace()
            if mode is not None:
                im = im.convert(mode)
            im = np.asarray(im)

            meta = self.get_meta()
            if rotate and "Orientation" in meta:
                transformation = _exif_orientation_transform(
                    meta["Orientation"],
                    self._image.mode
                )
                im = transformation(im)

            yield im

    def write(self, image, *, mode=None, format=None, **kwargs):
        """
        Write an ndimage to the URI specified in path.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage or list of ndimages to write.
        mode : {str, None}
            Convert the image to the given mode before returning it. If None,
            the mode will be left unchanged. Possible modes can be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        format : {str, None}
            Optional format override.  If omitted, the format to use is
            determined from the filename extension. If a file object was used
            instead of a filename, this parameter must always be used.
        kwargs : ...
            Extra arguments to pass to the writer. If a writer doesn't
            recognise an option, it is silently ignored. The available options
            are described in the :doc:`image format documentation
            (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
            for each writer.

        """

        pil_image = Image.fromarray(image, mode=mode)

        if "bits" in kwargs:
            pil_image = pil_image.quantize(colors=2**kwargs["bits"])

        pil_image.save(self._uri, format=format, **kwargs)

    def get_meta(self, *, index=None, formats=None):
        """ Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, return the metadata
            for the last read ndimage/frame.
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.
        """
        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        if index is not None:
            self._image.seek(index)

        metadata = self._image.info

        if self._image.getexif():
            exif_data = {
                ExifTags.TAGS.get(key, "unknown"): value
                for key, value in dict(self._image.getexif()).items()
            }
            exif_data.pop("unknown", None)
            metadata.update(exif_data)

        return self._image.info

    @classmethod
    def can_open(cls, uri):
        """ Verify that plugin can read the given URI

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        Returns
        -------
        readable : bool
            True if the URI can be read by the plugin. False otherwise.

        """
        try:
            with Image.open(uri):
                # Check if it is generally possible to read the image.
                # This will not read any data and merely try to find a
                # compatible pillow plugin as per the pillow docs.
                pass
        except UnidentifiedImageError:
            return False

        return True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
