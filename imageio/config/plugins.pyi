from typing import Any, Dict
from ..core.v3_plugin_api import PluginV3

class PluginConfig:
    def __init__(
        self,
        name: str,
        class_name: str,
        module_name: str,
        *,
        is_legacy: bool = False,
        package_name: str = None,
        install_name: str = None,
        legacy_args: dict = None,
    ) -> None: ...
    @property
    def format(self) -> Any: ...
    @property
    def plugin_class(self) -> PluginV3: ...

known_plugins: Dict[str, PluginConfig]
