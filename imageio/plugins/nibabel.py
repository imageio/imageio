# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

"""Read/Write neuroimaging images using nibabel.

Backend: `nibabel <https://nipy.org/nibabel/>`_

.. note::
    To use this plugin you have to install its backend::

        pip install imageio[nibabel]

nibabel provides access to the file formats used in neuroimaging. Reading
supports every image format the backend recognizes, including NIfTI-1/2
(``.nii``, ``.nii.gz``, and the ``.hdr``/``.img`` pair), Analyze, MGH/MGZ and
MINC. Writing is limited to the formats that can be created from an ndimage and
an affine, i.e., NIfTI-1 (``.nii``, ``.nii.gz``) and MGH (``.mgh``, ``.mgz``).
Surface and connectivity formats (GIFTI, CIFTI-2) store their data in a
different shape and are not supported.

Parameters
----------
None

Notes
-----
NIfTI stores volumetric data with the spatial axes first and an optional time
axis last, and this plugin returns the data in exactly that order. That is, for
a 3D file ``shape`` is ``(i, j, k)`` and for a 4D file ``(i, j, k, t)``, which
is the axis order of the returned ndimage. ``spacing`` reports the voxel size
along those axes as taken from the image's affine.

"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import nibabel as nib
import numpy as np

from ..core.request import URI_BYTES, InitializationError, IOMode, Request
from ..core.v3_plugin_api import ImageProperties, PluginV3
from ..typing import ArrayLike

#: Extensions that nibabel can write, mapped to the nibabel image class that
#: represents them. Everything else that nibabel can read is read-only here.
_writable_extensions = {
    ".nii": nib.Nifti1Image,
    ".nii.gz": nib.Nifti1Image,
    ".mgh": nib.MGHImage,
    ".mgz": nib.MGHImage,
}

#: NIfTI header fields that describe the stored image. The header itself is a
#: fixed struct with a lot of legacy bookkeeping, so only the fields a user can
#: make sense of are exposed as metadata.
_metadata_fields = (
    "datatype",
    "bitpix",
    "dim_info",
    "intent_code",
    "intent_name",
    "pixdim",
    "scl_slope",
    "scl_inter",
    "slice_code",
    "xyzt_units",
    "cal_max",
    "cal_min",
    "descrip",
    "qform_code",
    "sform_code",
)


def _plain_python(value: Any) -> Any:
    """Convert the numpy types a nibabel header returns into plain python."""

    if isinstance(value, np.ndarray):
        value = value.tolist()
    elif isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, bytes):
        value = value.decode()

    return value


class NibabelPlugin(PluginV3):
    """A class representing the nibabel plugin.

    Methods
    -------
    .. autosummary::
        :toctree: _plugins/nibabel

        NibabelPlugin.read
        NibabelPlugin.write

    """

    def __init__(self, request: Request) -> None:
        """Instantiate a new nibabel plugin object

        Parameters
        ----------
        request: Request
            A request object representing the resource to be operated on.

        """

        super().__init__(request)
        self._image = None
        self._extension = None

        # nibabel identifies the format from the filename, so the backend needs
        # a file on the local file system. For a path-based request this is the
        # path itself; for byte strings and other URIs imageio materializes a
        # temporary file and cleans it up in `finish`.
        self._filename = request.get_local_filename()

        if request.mode.io_mode == IOMode.read:
            try:
                # `mmap=False` keeps the data in memory: a memory map would stay
                # linked to a file that imageio may delete on close.
                image = nib.load(self._filename, mmap=False)
            except Exception as err:
                # nibabel raises format-specific errors (ImageFileError for
                # unknown formats, HeaderDataError for broken headers, OSError
                # for unreadable files, ...), all of which mean "not this file".
                raise InitializationError(
                    f"nibabel can not read {request.raw_uri}."
                ) from err

            if not hasattr(image, "dataobj"):
                # surface formats (e.g. GIFTI) load, but serve arrays of a
                # different shape and carry no image metadata
                raise InitializationError(
                    f"nibabel can not read {request.raw_uri}: it is not an image format."
                )

            self._image = image
        else:
            # fail early for files nibabel can not create so that imageio can
            # move on to a plugin that can
            self._extension = self._writable_extension()

    def _writable_extension(self) -> str:
        """The writable extension of the file that will be created.

        imageio reports only the trailing suffix of a filename, so a compressed
        NIfTI file (``.nii.gz``) arrives here as ``.gz``; nibabel infers the
        format from the full filename instead, which makes the local filename
        - the file nibabel writes to - the authoritative source.

        """

        for extension in _writable_extensions:
            if self._filename.endswith(extension):
                return extension

        raise InitializationError(
            f"nibabel can not write {self._request.extension} files."
        )

    def read(self, *, index: int = None) -> np.ndarray:
        """Read the image data stored in the file.

        A neuroimaging file holds a single (possibly volumetric or temporally
        resolved) image, so ``index`` accepts only ``0``/``None`` (read that
        image) and ``...`` (read it and prepend a batch axis of length 1). The
        time axis of a 4D image is part of the ndimage and is not iterated.

        Parameters
        ----------
        index : {int, Ellipsis, None}
            Which ndimage to read. See above.

        Returns
        -------
        ndimage : np.ndarray
            A numpy array containing the loaded image data.

        """

        # materialize the data now: the backend reads it lazily, and the file it
        # reads from may be a temporary one that is removed once the plugin closes
        ndimage = np.asanyarray(self._image.dataobj)

        if index is Ellipsis:
            return ndimage[None, ...]
        elif index not in (None, 0):
            raise ValueError(
                f"File contains a single image, but index={index} was requested."
            )

        return ndimage

    def iter(self, **kwargs) -> Iterator[np.ndarray]:
        """Iterate over the ndimages in the file.

        A neuroimaging file contains a single ndimage, so this yields exactly
        one ndimage.

        Returns
        -------
        ndimage : Iterator[np.ndarray]
            Iterator over the image data in the file.

        """

        yield self.read(**kwargs)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        affine: ArrayLike = None,
        header: Any = None,
    ) -> Optional[bytes]:
        """Write an ndimage to the file.

        Parameters
        ----------
        ndimage : ArrayLike or List[ArrayLike]
            The ndimage to write. A list of ndimages with equal shapes is
            stacked along a new trailing axis, which yields a 4D file.
        affine : ArrayLike
            The 4x4 affine that maps voxel indices to world coordinates. If
            None, an identity matrix (1mm isotropic voxels) is used.
        header : nibabel header
            A header to use for the new image. If None, the backend creates a
            default header for the requested format.

        Returns
        -------
        encoded_image : bytes or None
            If the chosen ImageResource is the special target ``"<bytes>"``,
            return the encoded image data as bytes. Otherwise, return None.

        Notes
        -----
        MGH (``.mgh``/``.mgz``) stores only a subset of the numpy dtypes
        (``uint8``, ``int16``, ``int32`` and ``float32``); writing data of
        another dtype raises a ``MGHError`` from the backend.

        """

        if isinstance(ndimage, (list, tuple)):
            ndimage = np.stack(ndimage, axis=-1)

        ndimage = np.asarray(ndimage)

        if affine is None:
            affine = np.eye(4, dtype=float)

        affine = np.asarray(affine, dtype=float)

        if affine.shape != (4, 4):
            raise ValueError(
                f"`affine` must be a 4x4 matrix, but has shape {affine.shape}."
            )

        image_class = _writable_extensions[self._extension]
        image = image_class(ndimage, affine, header)

        # nibabel requires a filename to determine the output format (and to
        # gzip it, if requested); the file imageio handed over is moved to the
        # requested target when the request is finished.
        image.to_filename(self._filename)

        if self._request._uri_type == URI_BYTES:
            # writing to `<bytes>` returns the encoded file directly
            with open(self._filename, "rb") as file:
                return file.read()

        return None

    def metadata(
        self, index: int = None, exclude_applied: bool = True
    ) -> Dict[str, Any]:
        """Read ndimage metadata.

        Parameters
        ----------
        index : {int, Ellipsis, None}
            Which ndimage to read metadata from. See :meth:`.read`.
        exclude_applied : bool
            If True, exclude metadata fields that are applied to the image while
            reading. This plugin does not apply any metadata when reading, so
            this flag currently has no effect.

        Returns
        -------
        metadata : dict
            A dictionary of format-specific metadata.

        """

        if index not in (None, 0, Ellipsis):
            raise ValueError(
                f"File contains a single image, but index={index} was requested."
            )

        image = self._image
        metadata = {"affine": image.affine}
        header = image.header

        for field in _metadata_fields:
            try:
                value = header[field]
            except (KeyError, ValueError):
                # this format's header has no such field (e.g. MGH)
                continue

            metadata[field] = _plain_python(value)

        return metadata

    def properties(self, index: int = None) -> ImageProperties:
        """Standardized ndimage metadata

        Parameters
        ----------
        index : {int, Ellipsis, None}
            Which ndimage to read properties from. See :meth:`.read`.

        Returns
        -------
        properties : ImageProperties
            A dataclass filled with standardized image metadata.

        Notes
        -----
        Reading a single image yields ``shape == image.shape``; reading the
        batch (``index=...``) prepends the batch axis, i.e.
        ``shape == (1, *image.shape)``.

        """

        if index is Ellipsis:
            return ImageProperties(
                shape=(1, *self._image.shape),
                dtype=self._image.get_data_dtype(),
                n_images=1,
                is_batch=True,
                spacing=self._voxel_sizes(),
            )

        if index not in (None, 0):
            raise ValueError(
                f"File contains a single image, but index={index} was requested."
            )

        return ImageProperties(
            shape=self._image.shape,
            dtype=self._image.get_data_dtype(),
            spacing=self._voxel_sizes(),
        )

    def _voxel_sizes(self) -> Optional[Tuple[float, ...]]:
        """Spacing between voxels along each axis, taken from the affine."""

        affine = getattr(self._image, "affine", None)

        if affine is None:
            return None

        return tuple(float(size) for size in nib.affines.voxel_sizes(affine))
