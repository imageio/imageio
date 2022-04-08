# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Read/Write images using Pillow/PIL.

Backend Library: `Pillow <https://pillow.readthedocs.io/en/stable/>`_

Plugin that wraps the the Pillow library. Pillow is a friendly fork of PIL
(Python Image Library) and supports reading and writing of common formats (jpg,
png, gif, tiff, ...). For, the complete list of features and supported formats
please refer to pillows official docs (see the Backend Library link).

Parameters
----------
request : Request
    A request object representing the resource to be operated on.

Methods
-------

.. autosummary::
    :toctree: _plugins/pillow

    PillowPlugin.read
    PillowPlugin.write
    PillowPlugin.iter
    PillowPlugin.get_meta

"""

from typing import Optional, Dict, Any
import numpy as np
from PIL import Image, UnidentifiedImageError, ImageSequence, ExifTags
from ..core.request import Request, IOMode, InitializationError, URI_BYTES
from ..core.v3_plugin_api import PluginV3, ImageProperties
import warnings


def _exif_orientation_transform(orientation, mode):
    # get transformation that transforms an image from a
    # given EXIF orientation into the standard orientation

    # -1 if the mode has color channel, 0 otherwise
    axis = -2 if Image.getmodebands(mode) > 1 else -1

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


class PillowPlugin(PluginV3):
    def __init__(self, request: Request) -> None:
        """Instantiate a new Pillow Plugin Object

        Parameters
        ----------
        request : {Request}
            A request object representing the resource to be operated on.

        """

        super().__init__(request)

        self._image = None

        if request.mode.io_mode == IOMode.read:
            try:
                with Image.open(request.get_file()):
                    # Check if it is generally possible to read the image.
                    # This will not read any data and merely try to find a
                    # compatible pillow plugin (ref: the pillow docs).
                    pass
            except UnidentifiedImageError:
                if request._uri_type == URI_BYTES:
                    raise InitializationError(
                        "Pillow can not read the provided bytes."
                    ) from None
                else:
                    raise InitializationError(
                        f"Pillow can not read {request.raw_uri}."
                    ) from None

            self._image = Image.open(self._request.get_file())
        else:
            extension = self.request.extension or self.request.format_hint
            if extension is None:
                warnings.warn(
                    "Can't determine file format to write as. You _must_"
                    " set `format` during write or the call will fail. Use "
                    "`format_hint` to supress this warning. ",
                    UserWarning,
                )
                return

            tirage = [Image.preinit, Image.init]
            for format_loader in tirage:
                format_loader()
                if extension in Image.registered_extensions().keys():
                    return

            raise InitializationError(
                f"Pillow can not write `{extension}` files."
            ) from None

    def close(self) -> None:
        if self._image:
            self._image.close()

        self._request.finish()

    def read(
        self, *, index=0, mode=None, rotate=False, apply_gamma=False
    ) -> np.ndarray:
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

        if index is not None:
            # will raise IO error if index >= number of frames in image
            self._image.seek(index)
            image = self._apply_transforms(self._image, mode, rotate, apply_gamma)
            return image
        else:
            iterator = self.iter(mode=mode, rotate=rotate, apply_gamma=apply_gamma)
            image = np.stack([im for im in iterator], axis=0)
            return image

    def iter(self, *, mode=None, rotate=False, apply_gamma=False) -> np.ndarray:
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

        for im in ImageSequence.Iterator(self._image):
            yield self._apply_transforms(im, mode, rotate, apply_gamma)

    def _apply_transforms(self, image, mode, rotate, apply_gamma) -> np.ndarray:
        if mode is not None:
            image = image.convert(mode)
        elif image.format == "GIF":
            # adjust for pillow9 changes
            # see: https://github.com/python-pillow/Pillow/issues/5929
            image = image.convert(image.palette.mode)
        image = np.asarray(image)

        meta = self.metadata(index=self._image.tell(), exclude_applied=False)
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

    def write(
        self, image: np.ndarray, *, mode=None, format=None, **kwargs
    ) -> Optional[bytes]:
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
        image : ndarray
            The ndimage to write.
        mode : {str, None}
            Specify the image's color format. If None (default), the mode is
            inferred from the array's shape and dtype. Possible modes can be
            found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        format : {str, None}
            Optional format override.  If omitted, the format to use is
            determined from the filename extension. If a file object was used
            instead of a filename, this parameter must always be used.
        kwargs : ...
            Extra arguments to pass to pillow. If a writer doesn't recognise an
            option, it is silently ignored. The available options are described
            in pillow's `image format documentation
            <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html>`_
            for each writer.

        Notes
        -----
        When writing batches of very narrow (2-4 pixels wide) gray images set
        the ``mode`` explicitly to avoid the batch being identified as a colored
        image.

        """

        extension = self.request.extension or self.request.format_hint

        save_args = {
            "format": format or Image.registered_extensions()[extension],
        }

        # check if ndimage is a batch of frames/pages (e.g. for writing GIF)
        # if mode is given, use it; otherwise fall back to image.ndim only
        if mode is not None:
            is_batch = (
                image.ndim > 3 if Image.getmodebands(mode) > 1 else image.ndim > 2
            )
        elif image.ndim == 2:
            is_batch = False
        elif image.ndim == 3 and image.shape[-1] in [2, 3, 4]:
            # Note: this makes a channel-last assumption
            # (pillow seems to make it as well)
            is_batch = False
        else:
            is_batch = True

        if not is_batch:
            image = image[None, ...]

        pil_frames = list()
        for frame in image:
            pil_frame = Image.fromarray(frame, mode=mode)
            if "bits" in kwargs:
                pil_frame = pil_frame.quantize(colors=2 ** kwargs["bits"])
            pil_frames.append(pil_frame)
        primary_image, other_images = pil_frames[0], pil_frames[1:]

        if is_batch:
            save_args["save_all"] = True
            save_args["append_images"] = other_images

        save_args.update(kwargs)
        primary_image.save(self._request.get_file(), **save_args)

        if self._request._uri_type == URI_BYTES:
            return self._request.get_file().getvalue()

    def get_meta(self, *, index=0) -> Dict[str, Any]:
        return self.metadata(index=index, exclude_applied=False)

    def metadata(self, index: int = 0, exclude_applied: bool = True) -> Dict[str, Any]:
        """Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, return the metadata
            for the last read ndimage/frame.
        """

        if index is not None and self._image.tell() != index:
            self._image.seek(index)

        metadata = self._image.info.copy()
        metadata["mode"] = self._image.mode
        metadata["shape"] = self._image.size

        if self._image.mode == "P":
            metadata["palette"] = self._image.palette

        if self._image.getexif():
            exif_data = {
                ExifTags.TAGS.get(key, "unknown"): value
                for key, value in dict(self._image.getexif()).items()
            }
            exif_data.pop("unknown", None)
            metadata.update(exif_data)

        if exclude_applied:
            metadata.pop("Orientation", None)

        return metadata

    def properties(self, index: int = 0) -> ImageProperties:
        """Standardized ndimage metadata
        Parameters
        ----------
        index : int
            The index of the ndimage for which to return properties. If the
            index is out of bounds a ``ValueError`` is raised. If ``None``,
            return the properties for the ndimage stack. If this is impossible,
            e.g., due to shape missmatch, an exception will be raised.

        Returns
        -------
        properties : ImageProperties
            A dataclass filled with standardized image metadata.

        """

        if index is None:
            self._image.seek(0)
        else:
            self._image.seek(index)

        if self._image.format == "GIF":
            # GIF mode is determined by pallette
            mode = self._image.palette.mode
        else:
            mode = self._image.mode

        dummy = np.asarray(Image.new(mode, (1, 1)))

        shape = list(dummy.shape)
        shape[:2] = self._image.size[::-1]
        shape = (self._image.n_frames, *shape) if index is None else tuple(shape)

        return ImageProperties(
            shape=shape,
            dtype=dummy.dtype,
            is_batch=True if index is None else False,
        )
