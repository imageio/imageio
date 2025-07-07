from typing import Union, IO
from pathlib import Path

try:
    from numpy.typing import ArrayLike
except ImportError:
    # numpy<1.20 fall back to using ndarray
    from numpy import ndarray as ArrayLike

ImageResource = Union[str, bytes, Path, IO[bytes]]


__all__ = [
    "ArrayLike",
    "ImageResource",
]
