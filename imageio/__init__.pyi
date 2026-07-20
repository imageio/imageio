import pathlib
from _typeshed import Incomplete
from typing import Final, Protocol, type_check_only

from . import config, plugins, v2, v3
from .core import (
    RETURN_BYTES as RETURN_BYTES,
    FormatManager,
)
from .core.v3_plugin_api import PluginV3
from .v2 import (
    get_reader,
    get_reader as read,
    get_writer,
    get_writer as save,
    help,
    imwrite,
    imwrite as imsave,
    mimread,
    mimwrite,
    mimwrite as mimsave,
    mvolread,
    mvolwrite,
    mvolwrite as mvolsave,
    volread,
    volwrite,
    volwrite as volsave,
)
from .v3 import imiter, imopen

import numpy as np

__all__ = [
    "v2",
    "v3",
    "config",
    "plugins",
    "imopen",
    "imread",
    "imwrite",
    "imiter",
    "mimread",
    "volread",
    "mvolread",
    "imwrite",
    "mimwrite",
    "volwrite",
    "mvolwrite",
    "read",
    "save",
    "imsave",
    "mimsave",
    "volsave",
    "mvolsave",
    "help",
    "get_reader",
    "get_writer",
    "formats",
    "show_formats",
]

@type_check_only
class _SupportsReadAndClose(Protocol):
    def read(self, size: int = ..., /) -> bytes: ...
    def close(self) -> None: ...

__version__: Final[str] = ...

formats: Final[FormatManager] = ...

def show_formats() -> None: ...
def imread(
    uri: str | bytes | memoryview | pathlib.Path | _SupportsReadAndClose,
    format: str | None = None,
    *,
    plugin: str | type[PluginV3] | None = None,
    extension: str | None = None,
    **plugin_kwargs: Incomplete,
) -> np.ndarray: ...
