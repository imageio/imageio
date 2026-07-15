# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

from collections.abc import Sequence
from typing import Dict, Literal, Union, List, overload

import numpy as np

from .core.imopen import imopen
from .core import RETURN_BYTES, Array
from .typing import ImageResource, ArrayLike
from .core.format import Format

MEMTEST_DEFAULT_MIM = "256MB"
MEMTEST_DEFAULT_MVOL = "1GB"

def to_nbytes(arg: float = None, default=None) -> float: ...
def help(name=None) -> None: ...
def decypher_format_arg(format_name: Union[str, None]) -> Dict[str, str]: ...
def get_reader(
    uri: ImageResource, format: str | None = ..., mode: str = "?", **kwargs
) -> Format.Reader: ...
def get_writer(
    uri: ImageResource, format: str | None = ..., mode: str = "?", **kwargs
) -> Format.Writer: ...
def imread(uri: ImageResource, format: str | None = ..., **kwargs) -> Array: ...
@overload
def imwrite(
    uri: Literal["<bytes>"], im: ArrayLike, format: str | None = ..., **kwargs
) -> bytes: ...
@overload
def imwrite(
    uri: ImageResource, im: ArrayLike, format: str | None = ..., **kwargs
) -> None: ...
def imwrite(
    uri: ImageResource | Literal["<bytes>"], im: ArrayLike, format: str | None = ..., **kwargs
) -> bytes | None: ...
def mimread(
    uri: ImageResource, format: str | None = ..., memtest=MEMTEST_DEFAULT_MIM, **kwargs
) -> List[Array]: ...
@overload
def mimwrite(
    uri: Literal["<bytes>"], ims: Sequence[ArrayLike], format: str | None = ..., **kwargs
) -> bytes: ...
@overload
def mimwrite(
    uri: ImageResource, ims: Sequence[ArrayLike], format: str | None = ..., **kwargs
) -> None: ...
def mimwrite(
    uri: ImageResource | Literal["bytes"], ims: Sequence[ArrayLike], format: str | None = ..., **kwargs
) -> bytes | None: ...
def volread(uri: ImageResource, format: str | None = ..., **kwargs) -> Array: ...
@overload
def volwrite(
    uri: Literal["<bytes>"], im: ArrayLike, format: str | None = ..., **kwargs
) -> bytes: ...
@overload
def volwrite(
    uri: ImageResource, im: ArrayLike, format: str | None = ..., **kwargs
) -> None: ...
def volwrite(
    uri: ImageResource | Literal["<bytes>"], im: ArrayLike, format: str | None = ..., **kwargs
) -> bytes | None: ...
def mvolread(
    uri: ImageResource,
    format: str | None = ...,
    memtest: float = MEMTEST_DEFAULT_MVOL,
    **kwargs,
) -> List[Array]: ...
@overload
def mvolwrite(
    uri: Literal["<bytes>"], ims: Sequence[ArrayLike], format: str | None= None, **kwargs
) -> bytes: ...
@overload
def mvolwrite(
    uri: ImageResource, ims: Sequence[ArrayLike], format: str | None = None, **kwargs
) -> None: ...
def mvolwrite(
    uri: ImageResource | Literal["<bytes>"], ims: Sequence[ArrayLike], format: str | None = ..., **kwargs
) -> bytes | None: ...

# aliases
read = get_reader
save = get_writer
imsave = imwrite
mimsave = mimwrite
volsave = volwrite
mvolsave = mvolwrite
