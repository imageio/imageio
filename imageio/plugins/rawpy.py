""" Read/Write images using rawpy.

rawpy is an easy-to-use Python wrapper for the LibRaw library. 
It also contains some extra functionality for finding and repairing hot/dead pixels.
"""

import rawpy
import numpy as np

from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union, cast
from ..core.request import URI_BYTES, InitializationError, IOMode, Request
from ..core.v3_plugin_api import PluginV3
from ..typing import ArrayLike


class RawPyPlugin(PluginV3):
    """A class representing the rawpy plugin.

    Methods
    -------

    .. autosummary::
    :toctree: _plugins/rawpy

    RawPyPlugin.read
    """
    def __init__(self, request: Request) -> None:
        """Instantiates a new rawpy plugin object

        Parameters
        ----------
        request: {Request}
            A request object representing the resource to be operated on.
        """

        super().__init__(request)

        self._image_file = None

        if request.mode.io_mode == IOMode.read:
            try:
                self._image_file = rawpy.imread(request.get_file())
            except rawpy.NotSupportedError:
                if request._uri_type == URI_BYTES:
                    raise InitializationError(
                        "RawPy can not read the provided bytes."
                    ) from None
                else:
                    raise InitializationError(
                        f"RawPy can not read {request.raw_uri}."
                    ) from None
        elif request.mode.io_mode == IOMode.write:
            raise InitializationError(
                "RawPy does not support writing."
            ) from None

    def close(self) -> None:

        if self._image_file:
            self._image_file.close()

        self._request.finish()

    def read(self, *, index: int = 0, **kwargs) -> np.ndarray:
        """Read Raw Image.

        Returns
        -------
        nd_image: ndarray
            The image data
        """

        nd_image: np.ndarray
        
        try:
            nd_image = self._image_file.postprocess(**kwargs)
        except Exception as ex:
            raise ex

        return nd_image
    
    def write(
        self, 
        ndimage: Union[ArrayLike, List[ArrayLike]]
    ) -> bytes | None:
        """RawPy does not support writing.
        """
        raise NotImplementedError()

    def iter(self) -> Iterator[np.ndarray]:
        """Load the image.

        Returns
        -------
        nd_image: ndarray
            The image data
        """

        try:
            yield self.read()
        except Exception as ex:
            raise ex
