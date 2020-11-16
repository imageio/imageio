import collections
import copy
import math
from pathlib import Path
from typing import Dict, IO, Mapping, Optional, Sequence, Union, overload

import numpy as np

from . import functions


class ImageSequence:
    """Sliceable, lazy-loading interface to multi-image files

    Single images can be retrieved by index, while substacks can be created
    by slicing and fancy indexing using lists/arrays of indices or boolean
    indices. Creating substacks does not load data into memory, allowing for
    dealing with containing many images.

    Examples
    --------

    Load 3rd frame:

    >>> with ImageSequence("some_file.tif"): as stack:
    ...     img = stack[3]

    Use fancy indexing to create substacks:

    >>> stack = ImageSequence("some_file.tif").open():
    >>> len(stack)
    30
    >>> substack1 = stack[1::2]  # Slice, will not load any data
    >>> len(substack2)
    15
    >>> np.all(substack2[1] == stack[3])  # Actually load data using int index
    True
    >>> substack2 = stack[[3, 5]]  # Create lazy substack using list of indices
    >>> substack3 = stack[[True, False] * len(stack) // 2]  # or boolean index
    >>> seq.close()
    """
    uri: Union[str, Path, bytes, IO]
    """File or file location or data to read from."""
    mode: str
    """Mode for opening file. Use "i" to retrieve a single image, "I" for
    multple images, "v" for single volume, "V" for multiple volumes and "?"
    for a sensible default.
    """
    reader_args: Mapping
    """Keyword arguments passed to :py:func:`imageio.get_reader` when opening
    file.
    """
    _slicerator_flag = True  # Make it work with slicerator

    def __init__(self, uri: Union[str, Path, bytes, IO],
                 format: Optional[str] = None, mode: str = "?", **kwargs):
        """Parameters
        ----------
        uri
            File or file location or data to read from.
        format
            File format. Use `None` for automatic detection.
        mode
            Mode for opening file. Use "i" to retrieve a single image, "I" for
            multple images, "v" for single volume, "V" for multiple volumes
            and "?" for a sensible default.
        **kwargs
            Keyword arguments passed to :py:func:`imageio.get_reader` when
            opening file.
        """
        self.uri = uri
        self._format = format
        self.mode = mode
        self.reader_args = kwargs
        self._reader = None
        self._indices = None

    def open(self) -> "ImageSequence":
        """Open the file

        Returns
        -------
        self
        """
        self._reader = functions.get_reader(self.uri, self._format, self.mode,
                                            **self.reader_args)
        return self

    def close(self):
        """Close the file"""
        self._reader.close()

    @overload
    def _resolve_index(self, t: int) -> int: ...

    def _resolve_index(self, t: Union[slice, Sequence[int], Sequence[bool]]
                       ) -> np.ndarray:
        """Convert index of potentially sliced stack to original index

        Parameters
        ----------
        t
            Index/indices w.r.t. sliced object

        Returns
        -------
        “Original” index/indeces suitable for retrieving images from file
        """
        # Use Iterable as Sequence does not imply numpy.ndarray
        if isinstance(t, (slice, collections.abc.Iterable)):
            if not math.isfinite(len(self)):
                raise IndexError(
                    "slicing impossible for sequences of unknown length")
        if isinstance(t, slice):
            t = np.arange(*t.indices(len(self)))
        if isinstance(t, collections.abc.Iterable):
            t = np.asarray(t)
            if np.issubdtype(t.dtype, np.bool_):
                if len(t) != len(self):
                    raise IndexError(
                        "boolean index did not match; stack length is "
                        f"{len(self)} but corresponding boolean length is "
                        f"{len(t)}")
                t = np.nonzero(t)[0]
            else:
                t[t < 0] += len(self)
            oob = np.nonzero((t < 0) | (t > len(self) - 1))[0]
            if oob.size:
                raise IndexError(
                    f"index {oob[0]} is out of bounds for stack of length "
                    f"{len(self)}")
        else:
            # Treat scalar t separately as this is much faster
            if t < 0:
                t += len(self)
            if t < 0 or t > len(self) - 1:
                raise IndexError(
                    f"index {t} is out of bounds for stack of length "
                    f"{len(self)}")
        if self._indices is None:
            return t
        return self._indices[t]

    def get_data(self, t: int, **kwargs) -> np.ndarray:
        """Get a single frame

        Parameters
        ----------
        t
            Frame number
        **kwargs
            Additional keyword arguments to pass to imageio's
            ``Reader.get_data()`` method.

        Returns
        -------
        Image data. The array has a ``meta`` attribute containing associated
        metadata.
        """
        return self._reader.get_data(self._resolve_index(t), **kwargs)

    def get_meta_data(self, t: Optional[int] = None) -> Dict:
        """Get metadata for a frame

        If ``t`` is not given, return the global metadata.

        Parameters
        ----------
        t
            Frame number

        Returns
        -------
        Metadata dictionary.
        """
        return self._reader.get_meta_data(
            None if t is None else self._resolve_index(t))

    @overload
    def __getitem__(self, t: int) -> np.ndarray: ...

    def __getitem__(self, t: Union[slice, Sequence[int], Sequence[bool]]
                    ) -> "ImageSequence":
        """Implement indexing and lazy slicing

        Parameters
        ----------
        t
            Frame number(s)

        Returns
        -------
        If t is a single index, return the corresponding frame. Otherwise,
        return a copy of ``self`` describing a substack.
        """
        t = self._resolve_index(t)
        if isinstance(t, np.ndarray):
            ret = copy.copy(self)
            ret._indices = t
            return ret
        # Assume t is a number
        return self._reader.get_data(t)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.close()

    def __len__(self):
        if self.closed:
            return 0
        try:
            return len(self._indices)
        except TypeError:
            # self._indices is None
            try:
                return len(self._reader)
            except TypeError:
                return 0

    @property
    def closed(self) -> bool:
        """True if the file is currently closed."""
        return getattr(self._reader, "closed", True)

    @property
    def format(self) -> Union[None, str]:
        """File format. Use `None` for automatic detection."""
        return self._format if self.closed else self._reader.format.name

    @format.setter
    def format(self, fmt):
        self._format = fmt
