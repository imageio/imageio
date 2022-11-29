from typing import Any, Dict, cast, Optional

import numpy as np
import tifffile
from io import BytesIO

from ..core.request import Request, URI_BYTES
from ..core.v3_plugin_api import PluginV3, ImageProperties


class SERIES_DEFAULT:
    pass

class TifffilePlugin(PluginV3):
    """Read/Write TIFF files.

    Backend: `tifffile <https://github.com/cgohlke/tifffile>`_

    Provides support for a wide range of TIFF images using the tifffile
    backend.
    """

    def __init__(self, request: Request, **kwargs) -> None:
        super().__init__(request)

        if request.mode.io_mode == "r":
            self._fh = tifffile.TiffFile(request.get_file(), **kwargs)
        else:
            self._fh = tifffile.TiffWriter(request.get_file(), **kwargs)

    def read(self, *, index=None, series=SERIES_DEFAULT, **kwargs):
        if "key" not in kwargs:
            kwargs["key"] = index
        elif index is not None:
            raise ValueError("Can't use `index` and `key` at the same time.")

        if series is None and index is None:
            ndimage = np.stack([x for x in self.iter(**kwargs)])
        elif series is SERIES_DEFAULT and index is None:
            ndimage = self._fh.asarray(series=0, **kwargs)
        elif series is SERIES_DEFAULT and index is not None:
            ndimage = self._fh.asarray(series=None, **kwargs)
        else:
            ndimage = self._fh.asarray(series=series, **kwargs)

        return ndimage

    def iter(self, **kwargs):
        for sequence in self._fh.series:
            yield sequence.asarray(**kwargs)

    def write(self, ndimage, is_batch=False, **kwargs) -> Optional[bytes]:
        if not is_batch:
            ndimage = np.asarray(ndimage)[None, :]

        for image in ndimage:
            self._fh.write(image, **kwargs)

        if self._request._uri_type == URI_BYTES:
            self._fh.close()
            file = cast(BytesIO, self._request.get_file())
            return file.getvalue()

    def metadata(
        self, index: int = None, exclude_applied: bool = True
    ) -> Dict[str, Any]:
        metadata = {}
        if index is None:
            # return file-level metadata
            metadata["byteorder"] = self._fh.byteorder

            for flag in tifffile.TIFF.FILE_FLAGS:
                if hasattr(self._fh, "is_" + flag):
                    flag_value = getattr(self._fh, "is_" + flag)
                    metadata["is_" + flag] = flag_value

                    if flag_value and hasattr(self._fh, flag + "_metadata"):
                        flavor_metadata = getattr(self._fh, flag + "_metadata")
                        if isinstance(flavor_metadata, tuple):
                            metadata.update(flavor_metadata[0])
                        else:
                            metadata.update(flavor_metadata)

        else:
            page = self._fh.pages[index]
            metadata.update({tag.name: tag.value for tag in page.tags})
            metadata.update(
                {
                    # backwards compatibility with old plugin
                    "planar_configuration": page.planarconfig,
                    "resolution_unit": page.resolutionunit,
                    "resolution": page.resolution,
                    "compression": page.compression,
                    "predictor": page.predictor,
                    "orientation": None,  # TODO
                    "description1": page.description1,
                    "description": page.description,
                    "software": page.software,
                    "datetime": page.datetime,
                }
            )

            for flag in tifffile.TIFF.PAGE_FLAGS:
                if hasattr(page, "is_" + flag):
                    flag_value = getattr(page, "is_" + flag)
                    metadata["is_" + flag] = flag_value

        return metadata

    def properties(self, index: int = None, series: int = 0) -> ImageProperties:
        if index is None and series is None:
            n_series = len(self._fh.series)
            props = ImageProperties(
                shape=(n_series, *target_series.shape),
                dtype=self._fh.series[0].dtype,
                is_batch=True,
                spacing=self._fh.pages[0].resolution,
            )
        elif index is None:
            target_series = self._fh.series[series]
            props = ImageProperties(
                shape=target_series.shape,
                dtype=target_series.dtype,
                is_batch=False,
                spacing=target_series.pages[0].resolution,
            )
        else:
            target_page = self._fh.pages[index]
            props = ImageProperties(
                shape=target_page.shape,
                dtype=target_page.dtype,
                is_batch=False,
                spacing=target_page.resolution,
            )

        return props

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()

        super().close()

    def iter_pages(self, **kwargs):
        for sequence in self._fh.series:
            for page in sequence.pages:
                yield page.asarray(**kwargs)
