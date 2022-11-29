from typing import Any, Dict

import numpy as np
import tifffile

from ..core.request import Mode, Request
from ..core.v3_plugin_api import PluginV3


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

    def read(self, *, index=None, **kwargs):
        if "key" not in kwargs:
            kwargs["key"] = index
        elif index is not None:
            raise ValueError("Can't use `index` and `key` at the same time.")

        return self._fh.asarray(**kwargs)

    def write(self, ndimage, is_batch=False, **kwargs):
        if not is_batch:
            ndimage = np.asarray(ndimage)[None, :]

        for image in ndimage:
            self._fh.write(image, **kwargs)

    def iter(self, **kwargs):
        for sequence in self._fh.series:
            yield sequence.asarray(**kwargs)

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
                    "planar_configuration": page.planarconfig.name,
                    "resolution_unit": page.resolutionunit,
                    "resolution": page.resolution,
                    "compression": page.compression.value,
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

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()

        super().close()

    def iter_pages(self, **kwargs):
        for sequence in self._fh.series:
            for page in sequence.pages:
                yield page.asarray(**kwargs)
