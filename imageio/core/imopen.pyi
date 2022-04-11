from typing import Any, Literal, overload, Union
from .v3_plugin_api import PluginV3
from ..plugins.pillow import PillowPlugin
from .legacy_plugin_wrapper import LegacyPlugin

@overload
def imopen(
    uri,
    io_mode: str,
    *,
    plugin: Literal["pillow"],
    format_hint: str = None,
    legacy_mode: Literal[False],
    **kwargs
) -> PillowPlugin: ...
@overload
def imopen(
    uri,
    io_mode: str,
    *,
    plugin: Union[str, Any] = None,
    format_hint: str = None,
    legacy_mode: Literal[True],
    **kwargs
) -> LegacyPlugin: ...
@overload
def imopen(
    uri,
    io_mode: str,
    *,
    plugin: Union[str, Any] = None,
    format_hint: str = None,
    legacy_mode: bool = False,
    **kwargs
) -> PluginV3: ...
