from io import BytesIO
from typing import Union
from pathlib import Path

try:
    from numpy.typing import ArrayLike
except ImportError:
    # numpy<1.20 fall back to using ndarray
    from numpy import ndarray as ArrayLike

ImageResource = Union[str, BytesIO, Path]


__all__ = [
    "ArrayLike",
    "ImageResource",
]
