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
                with rawpy.RawPy.open_buffer(request.get_file()):
                    self._image_file = request.get_file()
            except rawpy.NotSupportedError as ex:
                raise InitializationError(
                    f"RawPy can not read {request.raw_uri}."
                ) from None
            finally:
                rawpy.RawPy.close()
            
    def read(self, *, index: int = 0, **kwargs) -> np.ndarray:
        """Read Raw Image.

        Returns
        -------
        nd_image: ndarray
            The image data
        """

        nd_image: np.ndarray
        
        try:
            with rawpy.imread(self._image_file) as raw_image:
                nd_image = raw_image.postprocess(**kwargs)
        except Exception as ex:
            print(ex)

        return nd_image
    
    def write(
        self, 
        ndimage: Union[ArrayLike, List[ArrayLike]]
    ) -> bytes | None:
        """RawPy implementation not found.
        """
        raise NotImplementedError()

    def iter(self) -> Iterator[np.ndarray]:
        """Load the image.

        Returns
        -------
        nd_image: ndarray
            The image data
        """
        nd_image: np.ndarray
        
        try:
            with rawpy.imread(self._image_file) as raw_image:
                nd_image = raw_image.raw_image
        except Exception as ex:
            print(ex)

        return iter(nd_image)
