"""Read/Write TIFF files using tifffile.

.. note::
    To use this plugin you need to have `tifffile
    <https://github.com/cgohlke/tifffile>`_ installed::

        pip install tifffile

This plugin wraps tifffile, a powerfull library to manipulate TIFF files. It
superseeds our previous tifffile plugin and aims to expose all the features of
tifffile.

The plugin treats individual TIFF series as ndimages. A series is a sequence of
TIFF pages that, when combined describe a meaningful unit, e.g., a volumetric
image (where each slice is stored on an individual page) or a multi-color stain
(where each stain is stored on an individual page). Different TIFF
flavors/variants use series in different ways and, as such, the resulting
behavior may vary depending on the program used to create a particular TIFF
file.

Methods
-------
.. note::
    Check the respective function for a list of supported kwargs and detailed
    documentation.

.. autosummary::
    :toctree:

    TifffilePlugin.read
    TifffilePlugin.iter
    TifffilePlugin.write
    TifffilePlugin.properties
    TifffilePlugin.metadata

Additional methods available inside the :func:`imopen <imageio.v3.imopen>`
context:

.. autosummary::
    :toctree:

    TifffilePlugin.iter_pages

"""

from io import BytesIO
from typing import Any, Dict, Optional, cast

import numpy as np
import tifffile

from ..core.request import URI_BYTES, InitializationError, Request
from ..core.v3_plugin_api import ImageProperties, PluginV3


class TifffilePlugin(PluginV3):
    """Support for tifffile as backend.

    Parameters
    ----------
    request : iio.Request
        A request object that represents the users intent. It provides a
        standard interface to access various the various ImageResources and
        serves them to the plugin as a file object (or file). Check the docs for
        details.
    kwargs : Any
        Additional kwargs are forwarded to tifffile's constructor, i.e.
        ``TiffFile`` or ``TiffWriter``.

    """

    def __init__(self, request: Request, **kwargs) -> None:
        super().__init__(request)
        self._fh = None

        if request.mode.io_mode == "r":
            try:
                self._fh = tifffile.TiffFile(request.get_file(), **kwargs)
            except tifffile.tifffile.TiffFileError:
                raise InitializationError("Tifffile can not read this file.")
        else:
            self._fh = tifffile.TiffWriter(request.get_file(), **kwargs)

    def read(
        self, *, index: int = 0, page: int = None, **kwargs
    ) -> np.ndarray:
        """Read a ndimage or page.

        The ndimage returned depends on the value of both ``index`` and
        ``page``. ``index`` selects the series to read and ``page`` allows
        selecting a single page from the selected series. If ``index=None``,
        ``page`` is understood as a flat index, i.e., the selection ignores
        individual series inside the file. If both ``index`` and ``page`` are
        ``None``, then all the series are read and returned as a batch.

        Parameters
        ----------
        index : int
            If ``int``, select the ndimage (series) located at that index inside
            the file and return ``page`` from it. If ``None`` and ``page`` is
            ``int`` read the page located at that (flat) index inside the file.
            If ``None`` and ``page=None``, read all ndimages from the file and
            return them as a batch.
        page : int
            If ``None`` return the full selected ndimage. If ``int``, read the
            page at the selected index and return it.
        kwargs : Any
            Additional kwargs are forwarded to TiffFile's as_array method.
        """

        if "key" not in kwargs:
            kwargs["key"] = page
        elif page is not None:
            raise ValueError("Can't use `page` and `key` at the same time.")

        if "series" in kwargs:
            raise ValueError("Can't use tiffile's `series` kwarg. Use `index` instead.")

        if index is None and page is None:
            # read all series in the file and return them as a batch
            ndimage = np.stack([x for x in self.iter(**kwargs)])
        else:
            ndimage = self._fh.asarray(series=index, **kwargs)

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
                shape=(n_series, *self._fh.series[0].shape),
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
