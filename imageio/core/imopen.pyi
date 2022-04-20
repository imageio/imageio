from typing import Literal, Type, TypeVar, overload

from ..plugins.pillow import PillowPlugin
from ..plugins.pyav import PyAVPlugin
from ..typing import ImageResource
from .legacy_plugin_wrapper import LegacyPlugin
from .v3_plugin_api import PluginV3

CustomPlugin = TypeVar("CustomPlugin", bound=PluginV3)

@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    format_hint: str = None,
) -> PluginV3: ...
@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    plugin: str = None,
    format_hint: str = None,
    legacy_mode: Literal[True],
    **kwargs,
) -> LegacyPlugin: ...
@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    format_hint: str = None,
    legacy_mode: Literal[False] = False,
) -> PluginV3: ...
@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    plugin: Literal["pyav"],
    container: str = None,
) -> PyAVPlugin: ...
@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    plugin: Literal["pillow"],
) -> PillowPlugin: ...
@overload
def imopen(
    uri: ImageResource,
    io_mode: Literal["r", "w"],
    *,
    plugin: Type[CustomPlugin],
    format_hint: str = None,
    **kwargs,
) -> CustomPlugin: ...
