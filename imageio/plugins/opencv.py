from ..core.v3_plugin_api import PluginV3, ImageProperties
from ..core import Request
from ..core.request import IOMode, InitializationError, URI_BYTES

import cv2
import numpy as np
from typing import Dict, List, Union, Optional, Any
from numpy.typing import ArrayLike
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
        if index is ...:
            retval, img = cv2.imreadmulti(self.file_handle)
            is_batch = True
        elif index == 0:
            img = cv2.imread(self.file_handle, **kwargs)
            retval = img is not None
            is_batch = False
        else:
            retval, img = cv2.imreadmulti(self.file_handle, index, 1)
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
        for idx in range(cv2.imcount(self.file_handle)):
            yield self.read(index=idx, **kwargs)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        is_batch: bool = False,
        params: List[int] = None,
    ) -> Optional[bytes]:
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

        # unfortunately, OpenCV doesn't allow reading shape without reading pixel data
        img = self.read(index=index, **kwargs)

        return ImageProperties(
            shape=img.shape,
            dtype=img.dtype,
            is_batch=(index is ...),
        )

    def metadata(self, index: int = 0, exclude_applied: bool = True) -> Dict[str, Any]:
        raise NotImplementedError("OpenCV does not support metadata.")
