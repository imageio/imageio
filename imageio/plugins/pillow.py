# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

import numpy as np
from PIL import Image, UnidentifiedImageError, ImageSequence, ExifTags

from ..core.imopen import Plugin


def _is_multichannel(mode):
    multichannel = {
        "1": False,
        "L": False,
        "P": False,
        "RGB": True,
        "RGBA": True,
        "CMYK": True,
        "YCbCr": True,
        "LAB": True,
        "HSV": True,
        "I": False,
        "F": False,
        "LA": True,
        "PA": True,
        "RGBX": True,
        "RGBa": True,
        "La": False,
        "I;16": False,
        "I:16L": False,
        "I;16N": False,
        "BGR;15": True,
        "BGR;16": True,
        "BGR;24": True,
        "BGR;32": True,
    }

    return multichannel[mode]


def _exif_orientation_transform(orientation, mode):
    # get transformation that transforms an image from a
    # given EXIF orientation into the standard orientation

    # -1 if the mode has color channel, 0 otherwise
    axis = -2 if _is_multichannel(mode) else -1

    EXIF_ORIENTATION = {
        1: lambda x: x,
        2: lambda x: np.flip(x, axis=axis),
        3: lambda x: np.rot90(x, k=2),
        4: lambda x: np.flip(x, axis=axis - 1),
        5: lambda x: np.flip(np.rot90(x, k=3), axis=axis),
        6: lambda x: np.rot90(x, k=1),
        7: lambda x: np.flip(np.rot90(x, k=1), axis=axis),
        8: lambda x: np.rot90(x, k=3),
    }

    return EXIF_ORIENTATION[orientation]


class PillowPlugin(Plugin):
    def __init__(self, uri):
        """Instantiate a new Pillow Plugin Object

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        """
        self._uri = uri
        self._image = None

    def open(self):
        return

    def close(self):
        if self._image:
            self._image.close()

    def read(self, *, index=None, mode=None, rotate=False, apply_gamma=False):
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
        apply_gamma : {bool}
            If ``True`` and the image contains metadata about gamma, apply gamma
            correction to the image.

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
        if self._image is None:
            self._image = Image.open(self._uri)

        if index is not None:
            # will raise IO error if index >= number of frames in image
            self._image.seek(index)
            image = self._apply_transforms(self._image, mode, rotate, apply_gamma)
            return image
        else:
            iterator = self.iter(mode=mode, rotate=rotate, apply_gamma=apply_gamma)
            image = np.stack([im for im in iterator], axis=0)
            if image.shape[0] == 1:
                image = np.squeeze(image, axis=0)
            return image

    def iter(self, *, mode=None, rotate=False, apply_gamma=False):
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
        apply_gamma : {bool}
            If ``True`` and the image contains metadata about gamma, apply gamma
            correction to the image.
        """
        if self._image is None:
            self._image = Image.open(self._uri)

        for im in ImageSequence.Iterator(self._image):
            yield self._apply_transforms(im, mode, rotate, apply_gamma)

    def _apply_transforms(self, image, mode, rotate, apply_gamma):
        if mode is not None:
            image = image.convert(mode)
        image = np.asarray(image)

        meta = self.get_meta()
        if rotate and "Orientation" in meta:
            transformation = _exif_orientation_transform(
                meta["Orientation"], self._image.mode
            )
            image = transformation(image)

        if apply_gamma and "gamma" in meta:
            gamma = float(meta["gamma"])
            scale = float(65536 if image.dtype == np.uint16 else 255)
            gain = 1.0
            image = ((image / scale) ** gamma) * scale * gain + 0.4999
            image = np.round(image).astype(np.uint8)

        return image

    def write(self, image, *, mode="RGB", format=None, **kwargs):
        """
        Write an ndimage to the URI specified in path.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        If necessary, the image is broken down along the leading dimension to
        fit into individual frames of the chosen format. If the format doesn't
        support multiple frames, and IOError is raised.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage to write.
        mode : {str}
            Specify the image's color format; default is RGB. Possible modes can
            be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        format : {str, None}
            Optional format override.  If omitted, the format to use is
            determined from the filename extension. If a file object was used
            instead of a filename, this parameter must always be used.
        kwargs : ...
            Extra arguments to pass to pillow. If a
            writer doesn't recognise an option, it is silently ignored. The
            available options are described in the :doc:`image format
            documentation
            (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
            for each writer.

        """

        # ensure that the image has (at least) one batch dimension
        if image.ndim == 3 and _is_multichannel(mode):
            image = image[None, ...]
            save_all = False
        elif image.ndim == 2 and not _is_multichannel(mode):
            image = image[None, ...]
            save_all = False
        else:
            save_all = True

        pil_images = list()
        for frame in image:
            pil_frame = Image.fromarray(frame, mode=mode)
            if "bits" in kwargs:
                pil_frame = pil_frame.quantize(colors=2 ** kwargs["bits"])

            pil_images.append(pil_frame)

        pil_images[0].save(
            self._uri,
            save_all=save_all,
            append_images=pil_images[1:],
            format=format,
            **kwargs
        )

    def get_meta(self, *, index=None):
        """Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, return the metadata
            for the last read ndimage/frame.
        """
        if self._image is None:
            self._image = Image.open(self._uri)

        if index is not None:
            self._image.seek(index)

        metadata = self._image.info

        if self._image.mode == "P":
            metadata["palette"] = self._image.palette

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
        """Verify that plugin can read the given URI

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
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
