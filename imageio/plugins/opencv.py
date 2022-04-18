"""Read/Write images using OpenCV.

Backend Library: `OpenCV <https://opencv.org/>`_

This plugin wraps OpenCV (also known as ``cv2``), a popular image processing
library. Currently, it exposes OpenCVs image reading capability (no video or GIF
support yet); however, this may be added in future releases.

Methods
-------
.. note::
    Check the respective function for a list of supported kwargs and their
    documentation.

.. autosummary::
    :toctree:

    OpenCVPlugin.read
    OpenCVPlugin.iter
    OpenCVPlugin.write
    OpenCVPlugin.properties
    OpenCVPlugin.metadata

Pixel Formats (Colorspaces)
---------------------------

OpenCV is known to process images in BGR; however, most of the python echosystem
(in particular matplotlib and other pydata libraries) use the RGB. As such,
images are converted to RGB by default.

"""


from ..core.v3_plugin_api import PluginV3, ImageProperties
from ..core import Request
from ..core.request import IOMode, InitializationError, URI_BYTES

import cv2
import numpy as np
from typing import Dict, List, Union, Optional, Any
from ..typing import ArrayLike
from pathlib import Path


class OpenCVPlugin(PluginV3):
    def __init__(self, request: Request) -> None:
        super().__init__(request)

        self.file_handle = request.get_local_filename()
        if request._uri_type is URI_BYTES:
            self.filename = "<bytes>"
        else:
            self.filename = request.raw_uri

        mode = request.mode.io_mode
        if mode == IOMode.read and not cv2.haveImageReader(self.file_handle):
            raise InitializationError(f"OpenCV can't read `{self.filename}`.")
        elif mode == IOMode.write and not cv2.haveImageWriter(self.file_handle):
            raise InitializationError(f"OpenCV can't write to `{self.filename}`.")

    def read(self, *, index: int = 0, **kwargs) -> np.ndarray:
        """Read an image from the ImageResource.

        Parameters
        ----------
        index : int, Ellipsis
            The index of the image to read for formats that may contain more
            than one image, e.g. ``index=5`` reads the 5th image in the file. If
            ``...``, read all images in the ImageResource and stack them along a
            new, prepended, batch dimension. Defaults to 0.
        kwargs
            Additional kwargs are forwarded to OpenCVs ``imread`` or
            ``imreadmulti`` function.

        Returns
        -------
        ndimage : np.ndarray
            The decoded image as a numpy array.

        """
        if index is ...:
            retval, img = cv2.imreadmulti(self.file_handle, **kwargs)
            is_batch = True
        elif index == 0:
            img = cv2.imread(self.file_handle, **kwargs)
            retval = img is not None
            is_batch = False
        else:
            retval, img = cv2.imreadmulti(self.file_handle, index, 1, **kwargs)
            img = img[0] if retval else None
            is_batch = False

        if retval is False:
            raise ValueError(f"Could not read index `{index}` from `{self.filename}`.")

        if is_batch:
            img = np.stack([cv2.cvtColor(x, cv2.COLOR_BGR2RGB) for x in img])
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        return img

    def iter(self, **kwargs) -> np.ndarray:
        """Yield images from the ImageResource.

        Parameters
        ----------
        kwargs
            All kwargs are forwarded to OpenCVs ``imreadmulti`` function.

        Yields
        -------
        ndimage : np.ndarray
            The decoded image as a numpy array.

        """
        for idx in range(cv2.imcount(self.file_handle)):
            yield self.read(index=idx, **kwargs)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        is_batch: bool = False,
        params: List[int] = None,
    ) -> Optional[bytes]:
        """Save an ndimage in the ImageResource.

        Parameters
        ----------
        ndimage : ArrayLike, List[ArrayLike]
            The image data that will be written to the file. It is either a
            single image, a batch of images, or a list of images.
        is_batch : bool
            If True, the provided ndimage is a batch of images. If False (default), the
            provided ndimage is a single image. If the provided ndimage is a list of images,
            this parameter has no effect.
        params : List[int]
            A list of parameters that will be passed to OpenCVs imwrite or
            imwritemulti functions. Possible values are documented in the
            `OpenCV documentation
            <https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html#gabbc7ef1aa2edfaa87772f1202d67e0ce>`_.

        Returns
        -------
        encoded_image : bytes, None
            If the ImageResource is ``"<bytes>"`` the call to write returns the
            encoded image as a bytes string. Otherwise it returns None.

        """

        if isinstance(ndimage, list):
            ndimage = np.stack(ndimage, axis=0)
        elif not is_batch:
            ndimage = ndimage[None, ...]

        if ndimage[0].ndim == 2:
            n_channels = 1
        else:
            n_channels = ndimage[0].shape[-1]

        if n_channels == 1:
            ndimage_cv2 = [x for x in ndimage]
        elif n_channels == 4:
            ndimage_cv2 = [cv2.cvtColor(x, cv2.COLOR_RGBA2BGRA) for x in ndimage]
        else:
            ndimage_cv2 = [cv2.cvtColor(x, cv2.COLOR_RGB2BGR) for x in ndimage]

        retval = cv2.imwritemulti(self.file_handle, ndimage_cv2, params)

        if retval is False:
            # not sure what scenario would trigger this, but
            # it can occur theoretically.
            raise IOError("OpenCV failed to write.")  # pragma: no cover

        if self.request._uri_type == URI_BYTES:
            return Path(self.file_handle).read_bytes()

    def properties(self, index: int = 0, **kwargs) -> ImageProperties:
        """Standardized image metadata.

        Parameters
        ----------
        index : int, Ellipsis
            The index of the image to read metadata for. See ``read`` for details.
            Defaults to 0.
        kwargs
            Additional kwargs are forwarded to OpenCVs ``imread`` or
            ``imreadmulti`` function.

        Returns
        -------
        props : ImageProperties
            A dataclass filled with standardized image metadata.

        Notes
        -----
        Reading properties with OpenCV involves decoding pixel data, because
        OpenCV doesn't provide a direct way to access metadata.

        """

        # unfortunately, OpenCV doesn't allow reading shape without reading pixel data
        img = self.read(index=index, **kwargs)

        return ImageProperties(
            shape=img.shape,
            dtype=img.dtype,
            is_batch=(index is ...),
        )

    def metadata(self, index: int = 0, exclude_applied: bool = True) -> Dict[str, Any]:
        """Format-specific metadata.

        .. warning::
            OpenCV does not support reading metadata. When called, this function
            will raise a ``NotImplementedError``.

        """
        raise NotImplementedError("OpenCV does not support metadata.")
