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

from io import BytesIO
from typing import Callable, Optional, Dict, Any, Tuple, cast, Iterator, Union, List
import numpy as np
from PIL import Image, UnidentifiedImageError, ImageSequence, ExifTags  # type: ignore
from ..core.request import Request, IOMode, InitializationError, URI_BYTES
from ..core.v3_plugin_api import PluginV3, ImageProperties
import warnings
from ..typing import ArrayLike


def _exif_orientation_transform(orientation: int, mode: str) -> Callable:
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

        self._image: Image = None

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
                    "`extension` to supress this warning. ",
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
        self, *, index=None, mode=None, rotate=False, apply_gamma=False
    ) -> np.ndarray:
        """
        Parses the given URI and creates a ndarray from it.

        Parameters
        ----------
        index : {integer}
            If the ImageResource contains multiple ndimages, and index is an
            integer, select the index-th ndimage from among them and return it.
            If index is an ellipsis (...), read all ndimages in the file and
            stack them along a new batch dimension and return them. If index is
            None, this plugin reads the first image of the file (index=0) unless
            the image is a GIF or APNG, in which case all images are read
            (index=...).
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

        if index is None:
            if self._image.format == "GIF":
                index = Ellipsis
            elif self._image.custom_mimetype == "image/apng":
                index = Ellipsis
            else:
                index = 0

        if isinstance(index, int):
            # will raise IO error if index >= number of frames in image
            self._image.seek(index)
            image = self._apply_transforms(self._image, mode, rotate, apply_gamma)
            return image
        else:
            iterator = self.iter(mode=mode, rotate=rotate, apply_gamma=apply_gamma)
            image = np.stack([im for im in iterator], axis=0)
            return image

    def iter(
        self, *, mode: str = None, rotate: bool = False, apply_gamma: bool = False
    ) -> Iterator[np.ndarray]:
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
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        mode: str = None,
        format: str = None,
        is_batch: bool = None,
        **kwargs,
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
        image : ndarray or list
            The ndimage to write. If a list is given each element is expected to
            be an ndimage.
        mode : str
            Specify the image's color format. If None (default), the mode is
            inferred from the array's shape and dtype. Possible modes can be
            found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        format : str
            Optional format override. If omitted, the format to use is
            determined from the filename extension. If a file object was used
            instead of a filename, this parameter must always be used.
        is_batch : bool
            Explicitly tell the writer that ``image`` is a batch of images
            (True) or not (False). If None, the writer will guess this from the
            provided ``mode`` or ``image.shape``. While the latter often works,
            it may cause problems for small images due to aliasing of spatial
            and color-channel axes.
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
        if "fps" in kwargs:
            raise TypeError(
                "The keyword `fps` is no longer supported. Use `duration`"
                "(in ms) instead, e.g. `fps=60` == `duration=1/60/1000`."
            )

        extension = self.request.extension or self.request.format_hint

        save_args = {
            "format": format or Image.registered_extensions()[extension],
        }

        if isinstance(ndimage, list):
            ndimage = np.stack(ndimage, axis=0)
            is_batch = True
        else:
            ndimage = np.asarray(ndimage)

        # check if ndimage is a batch of frames/pages (e.g. for writing GIF)
        # if mode is given, use it; otherwise fall back to image.ndim only
        if is_batch is not None:
            pass
        elif mode is not None:
            is_batch = (
                ndimage.ndim > 3 if Image.getmodebands(mode) > 1 else ndimage.ndim > 2
            )
        elif ndimage.ndim == 2:
            is_batch = False
        elif ndimage.ndim == 3 and ndimage.shape[-1] in [2, 3, 4]:
            # Note: this makes a channel-last assumption
            # (pillow seems to make it as well)
            is_batch = False
        else:
            is_batch = True

        if not is_batch:
            ndimage = ndimage[None, ...]

        pil_frames = list()
        for frame in ndimage:
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
            file = cast(BytesIO, self._request.get_file())
            return file.getvalue()

        return None

    def get_meta(self, *, index=0) -> Dict[str, Any]:
        return self.metadata(index=index, exclude_applied=False)

    def metadata(
        self, index: int = None, exclude_applied: bool = True
    ) -> Dict[str, Any]:
        """Read ndimage metadata.

        Parameters
        ----------
        index : {integer, None}
            If the ImageResource contains multiple ndimages, and index is an
            integer, select the index-th ndimage from among them and return its
            metadata. If index is an ellipsis (...), read and return global
            metadata. If index is None, this plugin reads metadata from the
            first image of the file (index=0) unless the image is a GIF or APNG,
            in which case global metadata is read (index=...).

        Returns
        -------
        metadata : dict
            A dictionary of format-specific metadata.

        """

        if index is None:
            if self._image.format == "GIF":
                index = Ellipsis
            elif self._image.custom_mimetype == "image/apng":
                index = Ellipsis
            else:
                index = 0

        if isinstance(index, int) and self._image.tell() != index:
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

    def properties(self, index: int = None) -> ImageProperties:
        """Standardized ndimage metadata
        Parameters
        ----------
        index : int
            If the ImageResource contains multiple ndimages, and index is an
            integer, select the index-th ndimage from among them and return its
            properties. If index is an ellipsis (...), read and return the
            properties of all ndimages in the file stacked along a new batch
            dimension. If index is None, this plugin reads and returns the
            properties of the first image (index=0) unless the image is a GIF or
            APNG, in which case it reads and returns the properties all images
            (index=...).

        Returns
        -------
        properties : ImageProperties
            A dataclass filled with standardized image metadata.

        Notes
        -----
        This does not decode pixel data and is 394fast for large images.

        """

        if index is None:
            if self._image.format == "GIF":
                index = Ellipsis
            elif self._image.custom_mimetype == "image/apng":
                index = Ellipsis
            else:
                index = 0

        if index is Ellipsis:
            self._image.seek(0)
        else:
            self._image.seek(index)

        if self._image.format == "GIF":
            # GIF mode is determined by pallette
            mode = self._image.palette.mode
        else:
            mode = self._image.mode

        width: int = self._image.width
        height: int = self._image.height
        shape: Tuple[int, ...] = (height, width)

        n_frames: int = self._image.n_frames
        if index is ...:
            shape = (n_frames, *shape)

        dummy = np.asarray(Image.new(mode, (1, 1)))
        pil_shape: Tuple[int, ...] = dummy.shape
        if len(pil_shape) > 2:
            shape = (*shape, *pil_shape[2:])

        return ImageProperties(
            shape=shape,
            dtype=dummy.dtype,
            is_batch=True if index is Ellipsis else False,
        )
