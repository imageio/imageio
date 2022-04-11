import numpy as np
from typing import Optional, Dict, Any, Union, List

from .request import Request
from .v3_plugin_api import PluginV3, ImageProperties
from .format import Format
from ..typing import ArrayLike

class LegacyPlugin(PluginV3):
    def __init__(self, request: Request, legacy_plugin: Format) -> None: ...
    def legacy_get_reader(self, **kwargs) -> Format.Reader: ...
    def read(self, *, index: Optional[int] = 0, **kwargs) -> np.ndarray: ...
    def legacy_get_writer(self, **kwargs) -> Format.Writer: ...
    def write(
        self, ndimage: Union[ArrayLike, List[ArrayLike]], **kwargs
    ) -> Optional[bytes]: ...
    def iter(self, **kwargs) -> np.ndarray: ...
    def properties(self, index: Optional[int] = 0) -> ImageProperties: ...
    def get_meta(self, *, index: Optional[int] = 0) -> Dict[str, Any]: ...
    def metadata(
        self, index: Optional[int] = 0, exclude_applied: bool = True
    ) -> Dict[str, Any]: ...
    def __del__(self) -> None: ...
