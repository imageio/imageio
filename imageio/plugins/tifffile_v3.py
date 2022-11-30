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
image (where each slice is stored on an individual page) or a multi-color
staining picture (where each stain is stored on an individual page). Different
TIFF flavors/variants use series in different ways and, as such, the resulting
reading behavior may vary depending on the program used while creating a
particular TIFF file.

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
import warnings
import datetime

import numpy as np
import tifffile

from ..core.request import URI_BYTES, InitializationError, Request
from ..core.v3_plugin_api import ImageProperties, PluginV3
from ..typing import ArrayLike


def _get_resolution(page):
    """Get the resolution in a py3.7 compatible way"""

    metadata = {
        # uncomment once py 3.7 reached EoL - in fact, refactor this
        # function :)
        # "resolution_unit": page.resolutionunit,
        # "resolution": page.resolution,
    }

    if 296 in page.tags:
        metadata["resolution_unit"] = page.tags[296].value.value

    if 282 in page.tags and 283 in page.tags and 296 in page.tags:
        resolution_x = page.tags[282].value
        resolution_y = page.tags[283].value
        if resolution_x[1] == 0 or resolution_y[1] == 0:
            warnings.warn(
                "Ignoring resulution metadata, "
                "because at least one direction has a 0 denominator.",
                RuntimeWarning,
            )
        else:
            metadata["resolution"] = (
                resolution_x[0] / resolution_x[1],
                resolution_y[0] / resolution_y[1],
            )

    return metadata


def _get_datatime(page):
    """Get the datetime in a python 3.7 compatible way"""

    metadata = {
        # uncomment once python 3.7 is EoL
        # "datetime": page.datetime,
    }

    try:
        metadata["datetime"] = datetime.datetime.strptime(
            page.tags[306].value, "%Y:%m:%d %H:%M:%S"
        )
    except KeyError:
        pass

    return metadata


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

    # ---------------------
    # Standard V3 Interface
    # ---------------------

    def read(self, *, index: int = 0, page: int = None, **kwargs) -> np.ndarray:
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
            Additional kwargs are forwarded to TiffFile's ``as_array`` method.

        Returns
        -------
        ndarray : np.ndarray
            The decoded ndimage or page.
        """

        if "key" not in kwargs:
            kwargs["key"] = page
        elif page is not None:
            raise ValueError("Can't use `page` and `key` at the same time.")

        if "series" in kwargs:
            raise ValueError("Can't use tiffile's `series` kwarg. Use `index` instead.")

        if index is Ellipsis:
            index = None

        if index is None and page is None:
            # read all series in the file and return them as a batch
            ndimage = np.stack([x for x in self.iter(**kwargs)])
        else:
            ndimage = self._fh.asarray(series=index, **kwargs)

        return ndimage

    def iter(self, **kwargs) -> np.ndarray:
        """Yield ndimages from the TIFF.

        Parameters
        ----------
        kwargs : Any
            Additional kwargs are forwarded to the TiffPageSeries' ``as_array``
            method.

        Yields
        ------
        ndimage : np.ndarray
            A decoded ndimage.
        """

        for sequence in self._fh.series:
            yield sequence.asarray(**kwargs)

    def write(
        self, ndimage: ArrayLike, *, is_batch: bool = False, **kwargs
    ) -> Optional[bytes]:
        """Save a ndimage as TIFF.

        Parameters
        ----------
        ndimage : ArrayLike
            The ndimage to encode and write to the ImageResource.
        is_batch : bool
            If True, the first dimension of the given ndimage is treated as a
            batch dimension and each element will create a new series.
        kwargs : Any
            Additional kwargs are forwarded to TiffWriter's ``write`` method.

        Returns
        -------
        encoded_image : bytes
            If the ImageResource is ``"<bytes>"``, return the encoded bytes.
            Otherwise write returns None.

        Notes
        -----
        Incremental writing is supported. Subsequent calls to ``write`` will
        create new series unless ``contiguous=True`` is used, in which case the
        call to write will append to the current series.

        """

        if not is_batch:
            ndimage = np.asarray(ndimage)[None, :]

        for image in ndimage:
            self._fh.write(image, **kwargs)

        if self._request._uri_type == URI_BYTES:
            self._fh.close()
            file = cast(BytesIO, self._request.get_file())
            return file.getvalue()

    def metadata(
        self, *, index: int = Ellipsis, page: int = None, exclude_applied: bool = True
    ) -> Dict[str, Any]:
        """Format-Specific TIFF metadata.

        The metadata returned depends on the value of both ``index`` and
        ``page``. ``index`` selects a series and ``page`` allows selecting a
        single page from the selected series. If ``index=Ellipsis``, ``page`` is
        understood as a flat index, i.e., the selection ignores individual
        series inside the file. If ``index=Ellipsis`` and ``page=None`` then
        global (file-level) metadata is returned.

        Parameters
        ----------
        index : int
            Select the series of which to extract metadata from. If Ellipsis, treat
            page as a flat index into the file's pages.
        page : int
            If not None, select the page of which to extract metadata from. If
            None, read series-level metadata or, if ``index=...`` global,
            file-level metadata.
        exclude_applied : bool
            For API compatibility. Currently ignored.

        Returns
        -------
        metadata : dict
            A dictionary with information regarding the tiff flavor (file-level)
            or tiff tags (page-level).
        """

        if index is not Ellipsis and page is not None:
            target = self._fh.series[index].pages[page]
        elif index is not Ellipsis and page is None:
            # This is based on my understanding that series-level metadata is
            # stored in the first TIFF page.
            target = self._fh.series[index].pages[0]
        elif index is Ellipsis and page is not None:
            target = self._fh.pages[page]
        else:
            target = None

        metadata = {}
        if target is None:
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
            metadata.update({tag.name: tag.value for tag in target.tags})
            metadata.update(
                {
                    "planar_configuration": target.planarconfig,
                    "compression": target.compression,
                    "predictor": target.predictor,
                    "orientation": None,  # TODO
                    "description1": target.description1,
                    "description": target.description,
                    "software": target.software,
                    # update once python 3.7 reached EoL
                    **_get_resolution(target),
                    **_get_datatime(target),
                }
            )

        return metadata

    def properties(self, *, index: int = 0, page: int = None) -> ImageProperties:
        """Standardized metadata.

        The metadata returned depends on the value of both ``index`` and
        ``page``. ``index`` selects a series and ``page`` allows selecting a
        single page from the selected series. If ``index=None``, ``page`` is
        understood as a flat index, i.e., the selection ignores individual
        series inside the file. If both ``index`` and ``page`` are ``None``,
        then the result is a batch of all series.

        Parameters
        ----------
        index : int
            If ``int``, select the ndimage (series) located at that index inside
            the file. If ``None`` and ``page`` is ``int`` extract the metadata
            of the page located at that (flat) index inside the file. If
            ``None`` and ``page=None``, return the metadata for the batch of all
            ndimages in the file.
        page : int
            If ``None`` return the metadata of the full ndimage. If ``int``,
            return the metadata of the page at the selected index only.

        Returns
        -------
        image_properties : ImageProperties
            The standardized metadata of the selected ndimage or series.

        """

        if index is Ellipsis:
            series = None
            pages = self._fh.pages
        else:
            series = self._fh.series[index]
            pages = series.pages

        if series is not None:
            target_series = self._fh.series[index]
            props = ImageProperties(
                shape=target_series.shape,
                dtype=target_series.dtype,
                is_batch=False,
                spacing=_get_resolution(pages[0])["resolution"],
            )
        elif page is not None:
            props = ImageProperties(
                shape=pages[page].shape,
                dtype=pages[page].dtype,
                is_batch=False,
                spacing=_get_resolution(pages[page])["resolution"],
            )
        else:
            n_series = len(self._fh.series)
            props = ImageProperties(
                shape=(n_series, *self._fh.series[0].shape),
                dtype=self._fh.series[0].dtype,
                is_batch=True,
                spacing=_get_resolution(pages[0])["resolution"],
            )

        return props

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()

        super().close()

    # ------------------------------
    # Add-on Interface inside imopen
    # ------------------------------

    def iter_pages(self, **kwargs):
        """Yield pages from a TIFF file.

        This generator walks over the flat index of the pages inside an
        ImageResource and yields them in order.

        Parameters
        ----------
        kwargs : Any
            Additional kwargs are passed to TiffPage's ``as_array`` method.

        Yields
        ------
        page : np.ndarray
            A page stored inside the TIFF file.

        """

        for sequence in self._fh.series:
            for page in sequence.pages:
                yield page.asarray(**kwargs)
