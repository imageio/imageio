import collections
import copy
import math

import numpy as np

from . import functions


class ImageSequence:
    def __init__(self, uri, format=None, mode="?", **kwargs):
        self.uri = uri
        self.format = format
        self.mode = mode
        self.reader_args = kwargs
        self._reader = None
        self._indices = None

    def open(self):
        self._reader = functions.get_reader(self.uri, self.format, self.mode,
                                            **self.reader_args)
        return self

    def close(self):
        self._reader.close()
        self._reader = None

    def get_data(self, t, **kwargs):
        if t > len(self) - 1 or t < -len(self):
            raise IndexError("Index out of range.")
        if self._indices is None:
            return self._reader.get_data(t, **kwargs)
        else:
            return self._reader.get_data(self._indices[t], **kwargs)

    def get_meta_data(self, t):
        if t > len(self) - 1 or t < -len(self):
            raise IndexError("Index out of range.")
        if self._indices is None:
            return self._reader.get_meta_data(t)
        else:
            return self._reader.get_meta_data(self._indices[t])

    def __getitem__(self, t):
        if isinstance(t, (slice, collections.abc.Sequence)):
            if not math.isfinite(len(self)):
                raise IndexError(
                    "Slicing impossible for sequences of unknown length.")
            if isinstance(t, slice):
                rel_idx = np.arange(*t.indices(len(self)))
            elif isinstance(t, collections.abc.Sequence):
                rel_idx = np.asarray(t)
                if np.issubdtype(rel_idx.dtype, np.bool_):
                    rel_idx, = np.nonzero(rel_idx)
                if (np.any((rel_idx > len(self) - 1)) or
                        np.any((rel_idx < -len(self)))):
                    raise IndexError("Index out of range.")
            ret = copy.copy(self)
            if self._indices is None:
                ret._indices = rel_idx
            else:
                ret._indices = self._indices[rel_idx]
            return ret

        # Assume t is a number
        return self.get_data(t)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace):
        self.close()

    def __len__(self):
        try:
            return len(self._indices)
        except TypeError:
            # self._indices is None
            try:
                return len(self._reader)
            except TypeError:
                return 0

    @property
    def closed(self):
        try:
            return self._reader.closed
        except AttributeError:
            # self._reader is None
            return True
