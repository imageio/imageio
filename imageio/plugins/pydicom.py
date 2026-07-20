"""Read/Write single-file DICOM instances using pydicom.

.. note::
    To use this plugin you need to have `pydicom <https://pydicom.github.io/pydicom/>`_
    installed::

        pip install pydicom


Backend Library: `pydicom <https://pydicom.github.io/pydicom/>`_

This plugin reads and writes DICOM files using pydicom. It operates in
individual files, meaning while it supports multi-frame files natively, it does
**not** assemble data across files in a directory.


Methods
-------
.. note::
    Check the respective function for supported kwargs and detailed
    documentation.

.. autosummary::
    :toctree:

    PydicomPlugin.read
    PydicomPlugin.iter
    PydicomPlugin.write
    PydicomPlugin.properties
    PydicomPlugin.metadata

Additional methods available inside the :func:`imopen <imageio.v3.imopen>`
context:

.. autosummary::
    :toctree:

    PydicomPlugin.write_frame
    PydicomPlugin.lut_dense
    PydicomPlugin.lut_linear
    PydicomPlugin.instance_metadata
    PydicomPlugin.shared_frame_metadata
    PydicomPlugin.compression

Advanced API
------------

In addition to the default ImageIO v3 API this plugin exposes custom functions
and attributes for writing DICOM. These are available inside the
:func:`imopen <imageio.v3.imopen>` context and allow fine-grained control over
tags, functional groups, palettes, and compression. The callables are documented
above; below is a usage example::

    import imageio.v3 as iio

    frames = [...]  # list of (rows, cols) arrays, e.g. uint16
    with iio.imopen("out.dcm", "w", plugin="pydicom") as f:
        # global metadata
        f.instance_metadata["PatientName"] = "Anonymous"
        f.instance_metadata["Modality"] = "OT"

        # bit depth
        f.instance_metadata["BitsStored"] = 12

        # pixel compression
        f.compression = "rle"  # or "jpeg-ls", "jpeg2000-lossless", ...

        # shared FG (written once, applied to each frame)
        f.shared_frame_metadata["PixelMeasuresSequence"] = [
            {"PixelSpacing": [1.0, 1.0]}
        ]

        # write each frame
        for i, frame in enumerate(frames):
            f.write_frame(
                frame,
                # set frame-level metadata
                metadata={"FrameContentSequence": [{"FrameAcquisitionNumber": i}]},
            )

    meta = iio.immeta("out.dcm", plugin="pydicom")
    assert meta["PatientName"] == "Anonymous"

Frames are buffered until flush (``close()`` / context exit).

Compression
-----------

Compression is imopen-only. ``imwrite`` / ``write()`` always produce an
uncompressed Dataset; set ``f.compression`` before close to run pydicom
``Dataset.compress()`` once at flush. Changing the value after some
``write_frame`` calls is fine — only the value at flush matters.

Accepted values are short names (resolved to transfer syntax UIDs) or a raw
UID string:

- ``"rle"`` — RLE Lossless
- ``"jpeg-ls"`` — JPEG-LS Lossless
- ``"jpeg-ls-near"`` — JPEG-LS Near-Lossless
- ``"jpeg2000"`` — JPEG 2000
- ``"jpeg2000-lossless"`` — JPEG 2000 Lossless

Availability depends on pydicom’s installed encoders (RLE is built-in; others
may need extra packages). Unknown names raise immediately; unsupported UIDs
fail at flush.

Example::

    import imageio.v3 as iio
    import numpy as np

    img = np.arange(64, dtype=np.uint8).reshape(8, 8)
    with iio.imopen("compressed.dcm", "w", plugin="pydicom") as f:
        f.compression = "rle"
        f.write(img)

Palette LUTs
------------

The plugin offers helpers to build color palettes when writing palettized
DICOM images. Supported palettes are either **dense** or **linear**:

- A **dense** palette maps each pixel index to a color from a lookup table.
- A **linear** palette maps each pixel index via piecewise-linear
  interpolation between the provided ``colors`` at the provided ``indices``.

Dense color maps use the ordinary LookupTableData tags, linear maps use
SegmentedLookupTableData tags. Please ensure your reader supports these. Optional
alpha is supported as a 4th LUT channel. Pixel frames must be **index** arrays
into the LUT (not already-colored RGB).

When using a LUT, do **not** set ``BitsStored`` in ``instance_metadata``.

Example using a dense palette::

    import imageio.v3 as iio
    import numpy as np

    frame = ...  # (rows, cols) index array, with values 0..3
    colormap = np.array(
        [[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]],
        dtype=np.uint8,
    )
    with iio.imopen("palette_dense.dcm", "w", plugin="pydicom") as f:
        f.lut_dense(colormap)
        f.write(frame)

Example using a linear palette::

    import imageio.v3 as iio

    frame = ...  # (rows, cols) index array, uint8
    with iio.imopen("palette_linear.dcm", "w", plugin="pydicom") as f:
        f.lut_linear(
            colors=[(0, 0, 0), (65535, 65535, 65535)],
            indices=[0, 255],
        )
        f.write(frame)

Calling either helper **replaces** any previous palette state and clears the
other encoding's data tags (explicit and segmented are mutually exclusive).
While we offer helpers for dense and linear, you can still manually build and assign
other tables directly to the respective metadata tags.

Pixel reconstruction
--------------------

By default ``read`` / ``iter`` / ``imread`` / ``imiter`` reconstruct the image.
This means any LUT (lookup table), grayscale correction, or ROI (region of
interest) windowing is applied before the image is returned.

Pass ``raw=True`` to skip that pipeline and get stored values
(``pixel_array(..., raw=True)``). ``improps`` / ``properties`` take the same
``raw`` flag so reported shape and dtype match ``read``.

Notes
-----
Be aware that ``.write()`` on ``"<bytes>"`` needs to flush immediately so
``imwrite`` can return encoded bytes. This may cause surprising behavior when used
inside an explicit ``imopen`` context.

"""

from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import numpy as np

try:
    import pydicom as pdcm
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The pydicom plugin requires pydicom. Install it via `pip install imageio[pydicom]`."
    ) from exc

from ..core.request import URI_BYTES, InitializationError, IOMode, Request
from ..core.v3_plugin_api import ImageProperties, PluginV3
from ..typing import ArrayLike


def _as_python(value: Any) -> Any:
    if isinstance(value, pdcm.Dataset):
        return _dataset_to_dict(value, omit_keys=())
    if isinstance(value, pdcm.sequence.Sequence):
        return [_as_python(item) for item in value]
    if isinstance(value, bytes):
        return value
    if isinstance(value, (list, tuple)):
        return [_as_python(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _dataset_to_dict(ds: pdcm.Dataset, *, omit_keys: Sequence[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    omit = set(omit_keys)
    for elem in ds:
        if elem.keyword is None or elem.keyword == "PixelData":
            continue
        if elem.keyword in omit:
            continue
        out[elem.keyword] = _as_python(elem.value)
    return out


def _dict_to_dataset(data: Dict[str, Any]) -> pdcm.Dataset:
    ds = pdcm.Dataset()
    for key, value in data.items():
        _set_dataset_value(ds, key, value)
    return ds


def _set_dataset_value(ds: pdcm.Dataset, key: str, value: Any) -> None:
    if isinstance(value, dict):
        setattr(ds, key, _dict_to_dataset(value))
    elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        setattr(ds, key, pdcm.sequence.Sequence([_dict_to_dataset(v) for v in value]))
    else:
        setattr(ds, key, value)


class _TagMap:
    """Dict-like keyword → value view that writes through to a Dataset."""

    def __init__(self, get_ds: Callable[[], pdcm.Dataset]) -> None:
        self._get_ds = get_ds

    def __getitem__(self, key: str) -> Any:
        return _as_python(getattr(self._get_ds(), key))

    def __setitem__(self, key: str, value: Any) -> None:
        _set_dataset_value(self._get_ds(), key, value)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and hasattr(self._get_ds(), key)

    def get(self, key: str, default: Any = None) -> Any:
        return self[key] if key in self else default

    def update(self, other: Dict[str, Any]) -> None:
        for key, value in other.items():
            self[key] = value


class PydicomPlugin(PluginV3):
    """Read and write DICOM images via pydicom.

    Parameters
    ----------
    request : iio.Request
        Image resource request.
    kwargs : Any
        Additional kwargs are forwarded to ``pydicom.dcmread``.
    """

    def __init__(self, request: Request, **kwargs) -> None:
        super().__init__(request)

        # Read-only
        self._dcmread_kwargs: Dict[str, Any] = kwargs
        self._dcmread_kwargs.setdefault("stop_before_pixels", True)

        # Write-only
        self._compression: Optional[str] = None
        self._save_kwargs: Dict[str, Any] = {}
        self._frames: List[np.ndarray] = []
        self._frame_metadata: List[Optional[Dict[str, Any]]] = []
        self._flushed = False

        if request.mode.io_mode == IOMode.read:
            try:
                self._dataset = pdcm.dcmread(request.get_file(), **self._dcmread_kwargs)
            except pdcm.errors.InvalidDicomError as exc:
                raise InitializationError(
                    "pydicom cannot read this file as DICOM."
                ) from exc
        else:
            self._dataset = pdcm.Dataset()
            self._dataset.SOPClassUID = pdcm.uid.SecondaryCaptureImageStorage
            self._dataset.SOPInstanceUID = pdcm.uid.generate_uid()
            self._dataset.StudyInstanceUID = pdcm.uid.generate_uid()
            self._dataset.SeriesInstanceUID = pdcm.uid.generate_uid()
            self._dataset.Modality = "OT"

    def _ensure_pixel_dataset(self) -> None:
        # Read __init__ always sets _dataset; write handles never call this.
        if not self._dcmread_kwargs["stop_before_pixels"]:
            return
        fh = self.request.get_file()
        fh.seek(0)
        self._dcmread_kwargs["stop_before_pixels"] = False
        self._dataset = pdcm.dcmread(fh, **self._dcmread_kwargs)

    def _postprocess(self, arr: np.ndarray, *, raw: bool) -> np.ndarray:
        if raw:
            return arr

        if self._dataset.PhotometricInterpretation == "PALETTE COLOR":
            return pdcm.pixels.apply_color_lut(arr, self._dataset)
        arr = pdcm.pixels.apply_rescale(arr, self._dataset)
        return pdcm.pixels.apply_voi_lut(arr, self._dataset)

    def read(
        self,
        *,
        index: Optional[int] = None,
        raw: bool = False,
        **kwargs,
    ) -> np.ndarray:
        """Read pixel data from the DICOM instance.

        Parameters
        ----------
        index : int or Ellipsis or None
            ``None`` (default) returns the full array. ``int`` selects one
            frame. ``...`` ensures a leading batch axis (shape
            ``(frames, rows, cols[, channels])``).
        raw : bool
            If ``False`` (default), return a fully reconstructed image:
            pydicom decode (including YBR→RGB), then palette LUT **or**
            modality rescale / modality LUT followed by VOI LUT / windowing.
            Otherwise, return stored pixel values only.
        kwargs : Any
            Additional kwargs are forwarded to pydicom ``pixel_array``.

        Returns
        -------
        ndimage : np.ndarray
            Decoded pixels (always channel-last).
        """
        self._ensure_pixel_dataset()
        frame_index = None if index in (Ellipsis, None) else index
        arr = np.asarray(
            pdcm.pixels.pixel_array(self._dataset, index=frame_index, raw=raw, **kwargs)
        )
        arr = self._postprocess(arr, raw=raw)

        # ``...`` ensures a leading batch axis; multi-frame already has one.
        if index is Ellipsis and int(getattr(self._dataset, "NumberOfFrames", 1)) == 1:
            arr = arr[None, ...]

        return arr

    def iter(self, *, raw: bool = False, **kwargs) -> Iterator[np.ndarray]:
        """Yield decoded frames one at a time (frame-wise decode).

        Parameters
        ----------
        raw : bool
            Same meaning as ``read(..., raw=...)``. Default ``False`` applies
            full reconstruction per frame.
        kwargs : Any
            Forwarded to pydicom ``iter_pixels``.

        Yields
        ------
        frame : np.ndarray
            One frame with shape ``(rows, cols[, channels])``.
        """
        self._ensure_pixel_dataset()
        for frame in pdcm.pixels.iter_pixels(self._dataset, raw=raw, **kwargs):
            yield self._postprocess(np.asarray(frame), raw=raw)

    def properties(
        self, *, index: Optional[int] = None, raw: bool = False
    ) -> ImageProperties:
        """Standardized ndimage metadata from Dataset tags (no PixelData decode).

        Parameters
        ----------
        index : int or Ellipsis or None
            Same conventions as ``read``.
        raw : bool
            If ``False`` (default), shape and dtype match reconstructed
            ``read`` / ``iter`` output (palette → RGB channels; rescale /
            VOI may change dtype). Otherwise, report stored layout: integer
            ``Pixel Data`` (has ``PixelRepresentation``) or float modules
            (no ``PixelRepresentation``, ``BitsAllocated`` 32 / 64).

        Returns
        -------
        properties : ImageProperties
        """
        rows = int(self._dataset.Rows)
        cols = int(self._dataset.Columns)
        n_frames = int(getattr(self._dataset, "NumberOfFrames", 1))
        is_batch = index is Ellipsis or (index is None and n_frames > 1)

        # figure out how many channels are in the file
        if not raw and (
            hasattr(self._dataset, "AlphaPaletteColorLookupTableData")
            or hasattr(self._dataset, "SegmentedAlphaPaletteColorLookupTableData")
        ):
            channels = 4
        elif not raw and self._dataset.PhotometricInterpretation == "PALETTE COLOR":
            channels = 3
        else:
            channels = int(self._dataset.SamplesPerPixel)

        if is_batch:
            shape: Tuple[int, ...] = (n_frames, rows, cols)
        else:
            shape = (rows, cols)
        if channels > 1:
            shape = shape + (channels,)

        # figure out the dtype
        bits_allocated = int(self._dataset.BitsAllocated)
        is_signed = (
            int(self._dataset.PixelRepresentation) == 1
            if hasattr(self._dataset, "PixelRepresentation")
            else None
        )
        if not raw and self._dataset.PhotometricInterpretation == "PALETTE COLOR":
            bits = int(self._dataset.RedPaletteColorLookupTableDescriptor[2])
            dtype = np.dtype(np.uint8 if bits <= 8 else np.uint16)
        elif not raw and getattr(self._dataset, "VOILUTSequence", None) is not None:
            bits = int(self._dataset.VOILUTSequence[0].LUTDescriptor[2])
            dtype = np.dtype(np.uint8 if bits <= 8 else np.uint16)
        elif (
            not raw
            and hasattr(self._dataset, "WindowCenter")
            and hasattr(self._dataset, "WindowWidth")
        ):
            dtype = np.dtype(np.float64)
        elif (
            not raw and getattr(self._dataset, "ModalityLUTSequence", None) is not None
        ):
            bits = int(self._dataset.ModalityLUTSequence[0].LUTDescriptor[2])
            dtype = np.dtype(np.uint8 if bits <= 8 else np.uint16)
        elif (
            not raw
            and hasattr(self._dataset, "RescaleSlope")
            and hasattr(self._dataset, "RescaleIntercept")
        ):
            dtype = np.dtype(np.float64)
        elif is_signed is None and bits_allocated == 32:
            dtype = np.dtype(np.float32)
        elif is_signed is None and bits_allocated == 64:
            dtype = np.dtype(np.float64)
        elif is_signed is not None and bits_allocated == 1:
            dtype = np.dtype(np.uint8)
        elif is_signed is not None and bits_allocated == 8:
            dtype = np.dtype(np.int8 if is_signed else np.uint8)
        elif is_signed is not None and bits_allocated == 16:
            dtype = np.dtype(np.int16 if is_signed else np.uint16)
        elif is_signed is not None and bits_allocated == 32:
            dtype = np.dtype(np.int32 if is_signed else np.uint32)
        else:
            raise ValueError(
                "Unsupported stored pixel type: BitsAllocated="
                f"{bits_allocated}, PixelRepresentation="
                f"{getattr(self._dataset, 'PixelRepresentation', None)}."
            )

        # figure out spacing
        # per-frame FG > shared FG > instance tags
        row_sp = None
        col_sp = None
        slice_sp = None

        # 1. Instance-level (global) tags
        pixel_spacing = getattr(self._dataset, "PixelSpacing", None)
        if pixel_spacing is not None:
            row_sp = float(pixel_spacing[0])
            col_sp = float(pixel_spacing[1])
        spacing_between_slices = getattr(self._dataset, "SpacingBetweenSlices", None)
        if spacing_between_slices is not None:
            slice_sp = float(spacing_between_slices)

        # 2. Shared functional group pixel measures (overwrite if set)
        shared_fg = getattr(self._dataset, "SharedFunctionalGroupsSequence", None)
        if shared_fg is not None:
            measures_seq = getattr(shared_fg[0], "PixelMeasuresSequence", None)
            if measures_seq is not None:
                measures = measures_seq[0]
                pixel_spacing = getattr(measures, "PixelSpacing", None)
                if pixel_spacing is not None:
                    row_sp = float(pixel_spacing[0])
                    col_sp = float(pixel_spacing[1])
                spacing_between_slices = getattr(measures, "SpacingBetweenSlices", None)
                if spacing_between_slices is not None:
                    slice_sp = float(spacing_between_slices)

        # 3. Per-frame functional group pixel measures (overwrite if index given)
        if isinstance(index, int):
            per_frame_fg = getattr(
                self._dataset, "PerFrameFunctionalGroupsSequence", None
            )
            if per_frame_fg is not None:
                measures_seq = getattr(
                    per_frame_fg[index], "PixelMeasuresSequence", None
                )
                if measures_seq is not None:
                    measures = measures_seq[0]
                    pixel_spacing = getattr(measures, "PixelSpacing", None)
                    if pixel_spacing is not None:
                        row_sp = float(pixel_spacing[0])
                        col_sp = float(pixel_spacing[1])
                    spacing_between_slices = getattr(
                        measures, "SpacingBetweenSlices", None
                    )
                    if spacing_between_slices is not None:
                        slice_sp = float(spacing_between_slices)

        # Map spacing components onto the reported shape axes.
        if row_sp is None or col_sp is None:
            spacing = None
        else:
            spacing_list: List[Any] = []
            if is_batch:
                spacing_list.append(slice_sp if slice_sp is not None else 1.0)
            spacing_list.extend([row_sp, col_sp])
            if channels > 1:
                spacing_list.append(1.0)
            spacing = tuple(spacing_list)

        return ImageProperties(
            shape=shape,
            dtype=dtype,
            n_images=n_frames if is_batch else None,
            is_batch=is_batch,
            spacing=spacing,
        )

    def metadata(
        self,
        *,
        index: Any = Ellipsis,
        exclude_applied: bool = True,
        raw: bool = False,
    ) -> Dict[str, Any]:
        """Read (non-data) DICOM tags.

        Parameters
        ----------
        index : Ellipsis or int
            Metadata is built by layered ``dict.update``:

            1. If ``index`` is ``...`` or ``None``, add instance-level tags
               (FG sequences omitted as top-level keys;
               ``TransferSyntaxUID`` included from file_meta).
            2. If a shared functional group is present, update with its macros.
            3. If ``index`` is an ``int``, update with that frame's per-frame
               FG (per-frame wins on conflict).

            Classic files with no FG data therefore yield ``{}`` for an
            integer ``index``.
        exclude_applied : bool
            If True (default) and ``raw`` is False, drop tags consumed by the
            default ``read`` / ``iter`` reconstruction (rescale / windowing).
            Otherwise, leave those tags in the returned dict.
        raw : bool
            Pair with ``read(..., raw=...)``. If ``False`` (default),
            ``exclude_applied`` may drop reconstruction tags. Otherwise,
            those tags are kept even when ``exclude_applied`` is True.

        Returns
        -------
        metadata : dict
            Keyword → value mapping (pydicom keyword names).
        """

        omit_applied: Tuple[str, ...] = (
            (
                "RescaleSlope",
                "RescaleIntercept",
                "RescaleType",
                "WindowCenter",
                "WindowWidth",
                "WindowCenterWidthExplanation",
                "VOILUTFunction",
            )
            if exclude_applied and not raw
            else ()
        )

        meta: Dict[str, Any] = {}

        # 1. Instance-level tags
        if index in (Ellipsis, None):
            meta.update(
                _dataset_to_dict(
                    self._dataset,
                    omit_keys=(
                        "SharedFunctionalGroupsSequence",
                        "PerFrameFunctionalGroupsSequence",
                        *omit_applied,
                    ),
                )
            )
            if (
                hasattr(self._dataset, "file_meta")
                and self._dataset.file_meta is not None
            ):
                ts = getattr(self._dataset.file_meta, "TransferSyntaxUID", None)
                if ts is not None:
                    meta.setdefault("TransferSyntaxUID", str(ts))

        # 2. Shared functional group macros
        shared_seq = getattr(self._dataset, "SharedFunctionalGroupsSequence", None)
        if shared_seq is not None:
            meta.update(_dataset_to_dict(shared_seq[0], omit_keys=omit_applied))

        # 3. Per-frame functional group macros for a concrete frame index
        if isinstance(index, int):
            per_seq = getattr(self._dataset, "PerFrameFunctionalGroupsSequence", None)
            if per_seq is not None:
                meta.update(_dataset_to_dict(per_seq[index], omit_keys=omit_applied))

        return meta

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        metadata: Optional[Dict[str, Any]] = None,
        is_planar: bool = False,
        **kwargs,
    ) -> Optional[bytes]:
        """Write an image stack to DICOM.

        Parameters
        ----------
        ndimage : ArrayLike
            The ndimage to write.
        metadata : dict
            Global metadata (instance-level) to write to the file.
        is_planar : bool
            If True, the provided ndimage is assumed to use planar color layout
            ([Frame, Channel], Height, Width). Otherwise, it is assumed to
            be interleaved ([Frame], Height, Width, [Channel]).
            Stored as DICOM ``PlanarConfiguration``.
        kwargs : Any
            Additional kwargs are forwarded to ``pydicom.dcmwrite``.

        Returns
        -------
        bytes or None
            Encoded bytes when the URI is ``"<bytes>"``, else ``None``.
        """
        if metadata:
            for key, value in metadata.items():
                _set_dataset_value(self._dataset, key, value)
        self._dataset.PlanarConfiguration = int(is_planar)
        self._save_kwargs.update(kwargs)

        # Prepend a batch axis for single-frame inputs: (H, W), planar (C, H, W),
        # or interleaved RGB (H, W, 3). Otherwise axis 0 is already the batch.
        arr = np.asarray(ndimage)
        if (
            arr.ndim == 2
            or (arr.ndim == 3 and is_planar)
            or (arr.ndim == 3 and arr.shape[-1] == 3)
        ):
            arr = arr[None, ...]

        for frame in arr:
            self.write_frame(frame)

        if self.request._uri_type == URI_BYTES:
            self._flush()
            return self.request.get_file().getvalue()
        return None

    @property
    def instance_metadata(self) -> _TagMap:
        """Instance-level (global) metadata of the file."""
        return _TagMap(lambda: self._dataset)

    @instance_metadata.setter
    def instance_metadata(self, value: Dict[str, Any]) -> None:
        for key, val in dict(value).items():
            _set_dataset_value(self._dataset, key, val)

    @property
    def shared_frame_metadata(self) -> _TagMap:
        """Metadata in the shared functional group.

        The tags stored here are writen once but applied to each frame
        in the dicom file.
        """

        def get_item() -> pdcm.Dataset:
            if not hasattr(self._dataset, "SharedFunctionalGroupsSequence") or not len(
                self._dataset.SharedFunctionalGroupsSequence
            ):
                self._dataset.SharedFunctionalGroupsSequence = pdcm.sequence.Sequence(
                    [pdcm.Dataset()]
                )
            return self._dataset.SharedFunctionalGroupsSequence[0]

        return _TagMap(get_item)

    @shared_frame_metadata.setter
    def shared_frame_metadata(self, value: Dict[str, Any]) -> None:
        self._dataset.SharedFunctionalGroupsSequence = pdcm.sequence.Sequence(
            [_dict_to_dataset(dict(value))]
        )

    @property
    def compression(self) -> Optional[str]:
        """The pixel compression to use when writing.

        Available options:
        - None: (system default)
        - "rle": RLE lossless compression
        - "jpeg-ls": JPEG-LS lossless compression
        - "jpeg-ls-near": JPEG-LS near lossless compression
        - "jpeg2000": JPEG 2000 lossless compression
        - "jpeg2000-lossless": JPEG 2000 lossless compression
        - Any transfer syntax UID string

        Returns
        -------
        compression : str or None
            Resolved transfer syntax UID, or ``None``.
        """
        return self._compression

    @compression.setter
    def compression(self, value: Optional[Union[str, Any]]) -> None:
        if value is None:
            self._compression = None
            return
        text = str(value)
        names = {
            "rle": pdcm.uid.RLELossless,
            "jpeg-ls": pdcm.uid.JPEGLSLossless,
            "jpeg-ls-near": pdcm.uid.JPEGLSNearLossless,
            "jpeg2000": pdcm.uid.JPEG2000,
            "jpeg2000-lossless": pdcm.uid.JPEG2000Lossless,
        }
        if text in names:
            self._compression = str(names[text])
            return
        if text and text[0].isdigit() and "." in text:
            self._compression = text
            return
        raise ValueError(
            f"Unknown compression {value!r}. Use one of: {', '.join(names)} "
            "(or a transfer syntax UID string)."
        )

    def write_frame(
        self, frame: ArrayLike, *, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add the given ndimage to the frames in this image.

        Parameters
        ----------
        frame : ArrayLike
            Single frame array.
        metadata : dict
            Local metadata associated with this ndimage.
        """
        self._frames.append(np.asarray(frame))
        self._frame_metadata.append(dict(metadata) if metadata else None)

    def lut_dense(self, colormap: ArrayLike, first_mapped: int = 0) -> None:
        """Set the given colormap as the image's LUT.

        Parameters
        ----------
        colormap : ArrayLike
            RGB(A) colormap as a 2D array of shape ``(N, 3)`` or ``(N, 4)``
            with dtype ``uint8`` or ``uint16`` (up to ``2**16`` entries).
        first_mapped : int
            Offset subtracted from stored pixel values before indexing the LUT.
        """
        cmap = np.asarray(colormap, order="F")
        bits = 8 * cmap.dtype.itemsize
        n_entries = 0 if cmap.shape[0] == 65536 else cmap.shape[0]

        for name in (
            "RedPaletteColorLookupTableDescriptor",
            "GreenPaletteColorLookupTableDescriptor",
            "BluePaletteColorLookupTableDescriptor",
            "AlphaPaletteColorLookupTableDescriptor",
            "RedPaletteColorLookupTableData",
            "GreenPaletteColorLookupTableData",
            "BluePaletteColorLookupTableData",
            "AlphaPaletteColorLookupTableData",
            "SegmentedRedPaletteColorLookupTableData",
            "SegmentedGreenPaletteColorLookupTableData",
            "SegmentedBluePaletteColorLookupTableData",
            "SegmentedAlphaPaletteColorLookupTableData",
        ):
            if name in self._dataset:
                delattr(self._dataset, name)

        descriptor = [n_entries, first_mapped, bits]
        channels = ("Red", "Green", "Blue", "Alpha")[: cmap.shape[1]]
        for i, channel in enumerate(channels):
            setattr(
                self._dataset,
                f"{channel}PaletteColorLookupTableDescriptor",
                descriptor,
            )
            setattr(
                self._dataset,
                f"{channel}PaletteColorLookupTableData",
                cmap[:, i].tobytes(),
            )
        self._dataset.PhotometricInterpretation = "PALETTE COLOR"

    def lut_linear(
        self,
        colors: ArrayLike,
        indices: ArrayLike,
        first_mapped: int = 0,
    ) -> None:
        """Set a piecewise linear gradient as the image's LUT.

        Builds a gradient LUT using DICOM's segmented palette tags.
        This allows more efficient storage of a gradient palette. The
        palette is defined by a sequence of knot points at different
        pixel intensities.

        Parameters
        ----------
        colors : ArrayLike
            Knot colors as a 2D array of shape (K, 3) or (K, 4).
        indices : ArrayLike
            0-based indicies of pixel intensities where each knot is
            located. Assumed to be strictly increasing.
        first_mapped : int
            Offset subtracted from stored pixel values before indexing
            the LUT.
        """
        cmap = np.asarray(colors, order="F")
        indices = np.asarray(indices)
        n = indices[-1].item() + 1
        n_entries = 0 if n == 65536 else n
        bits = 16

        for name in (
            "RedPaletteColorLookupTableDescriptor",
            "GreenPaletteColorLookupTableDescriptor",
            "BluePaletteColorLookupTableDescriptor",
            "AlphaPaletteColorLookupTableDescriptor",
            "RedPaletteColorLookupTableData",
            "GreenPaletteColorLookupTableData",
            "BluePaletteColorLookupTableData",
            "AlphaPaletteColorLookupTableData",
            "SegmentedRedPaletteColorLookupTableData",
            "SegmentedGreenPaletteColorLookupTableData",
            "SegmentedBluePaletteColorLookupTableData",
            "SegmentedAlphaPaletteColorLookupTableData",
        ):
            if name in self._dataset:
                delattr(self._dataset, name)

        descriptor = [n_entries, first_mapped, bits]
        channels = ("Red", "Green", "Blue", "Alpha")[: cmap.shape[1]]
        for i, channel in enumerate(channels):
            setattr(
                self._dataset,
                f"{channel}PaletteColorLookupTableDescriptor",
                descriptor,
            )
            # Discrete knot 0, then linear segments between consecutive knots.
            channel_vals = cmap[:, i]
            words = np.empty(3 * len(indices), dtype="<u2")
            words[0:3] = (0, 1, channel_vals[0])
            for k in range(len(indices) - 1):
                words[3 * (k + 1) : 3 * (k + 2)] = (
                    1,
                    indices[k + 1] - indices[k],
                    channel_vals[k + 1],
                )
            setattr(
                self._dataset,
                f"Segmented{channel}PaletteColorLookupTableData",
                words.tobytes(),
            )
        self._dataset.PhotometricInterpretation = "PALETTE COLOR"

    def _flush(self) -> None:
        if self._flushed:
            return
        if self.request.mode.io_mode != IOMode.write:
            return
        if not self._frames:
            self._flushed = True
            return

        is_planar = int(getattr(self._dataset, "PlanarConfiguration", 0)) == 1
        has_palette = hasattr(
            self._dataset, "RedPaletteColorLookupTableData"
        ) or hasattr(self._dataset, "SegmentedRedPaletteColorLookupTableData")
        arr = (
            self._frames[0]
            if len(self._frames) == 1
            else np.stack(self._frames, axis=0)
        )
        bits_stored = (
            self._dataset.BitsStored
            if hasattr(self._dataset, "BitsStored")
            else 8 * arr.dtype.itemsize
        )

        # PhotometricInterpretation for encode (required by set_pixel_data).
        if has_palette:
            photometric = "PALETTE COLOR"
        elif hasattr(self._dataset, "PhotometricInterpretation"):
            photometric = str(self._dataset.PhotometricInterpretation)
        elif self._frames[0].ndim == 2:
            photometric = "MONOCHROME2"
        else:
            photometric = "RGB"

        # write the pixel data
        if is_planar:
            # writing planar with pydicom requires manual packing
            samples, rows, cols = arr.shape[-3:]
            if len(self._frames) == 1:
                if "NumberOfFrames" in self._dataset:
                    delattr(self._dataset, "NumberOfFrames")
            else:
                self._dataset.NumberOfFrames = len(self._frames)
            self._dataset.SamplesPerPixel = samples
            self._dataset.PhotometricInterpretation = photometric
            self._dataset.PlanarConfiguration = 1
            self._dataset.Rows = rows
            self._dataset.Columns = cols
            self._dataset.BitsAllocated = 8 * arr.dtype.itemsize
            self._dataset.BitsStored = bits_stored
            self._dataset.HighBit = bits_stored - 1
            self._dataset.PixelRepresentation = 0 if arr.dtype.kind == "u" else 1
            raw = np.ascontiguousarray(arr).tobytes()
            if len(raw) % 2 == 1:
                raw += b"\x00"
            self._dataset.PixelData = raw
            self._dataset["PixelData"].VR = (
                pdcm.valuerep.VR.OB
                if self._dataset.BitsAllocated <= 8
                else pdcm.valuerep.VR.OW
            )
            if not hasattr(self._dataset, "file_meta"):
                self._dataset.file_meta = pdcm.dataset.FileMetaDataset()
            tsyntax = getattr(self._dataset.file_meta, "TransferSyntaxUID", None)
            if tsyntax is None or tsyntax.is_compressed:
                self._dataset.file_meta.TransferSyntaxUID = (
                    pdcm.uid.ExplicitVRLittleEndian
                )
        else:
            self._dataset.set_pixel_data(
                arr, photometric, bits_stored, generate_instance_uid=False
            )

        # write per-frame (local) metadata
        if any(m is not None for m in self._frame_metadata):
            items = [_dict_to_dataset(meta or {}) for meta in self._frame_metadata]
            self._dataset.PerFrameFunctionalGroupsSequence = pdcm.sequence.Sequence(
                items
            )

        # apply pixel compression
        try:
            if self._compression is not None:
                self._dataset.compress(str(self._compression))
            save_kwargs = dict(self._save_kwargs)
            save_kwargs.setdefault("enforce_file_format", True)
            self._dataset.save_as(self.request.get_file(), **save_kwargs)
        finally:
            self._flushed = True

    def close(self) -> None:
        """Flush a write buffer (if needed) and release the request."""
        if self.request.mode.io_mode == IOMode.write:
            self._flush()
        self.request.finish()
