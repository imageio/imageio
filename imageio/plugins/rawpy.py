""" Read/Write images using rawpy.

rawpy is an easy-to-use Python wrapper for the LibRaw library. 
It also contains some extra functionality for finding and repairing hot/dead pixels.
"""

import rawpy
import numpy as np

from ..core.request import URI_BYTES, InitializationError, IOMode, Request
from ..core.v3_plugin_api import PluginV3


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

        self._image: rawpy = None
        self._image_file = request.get_file()

    def read(self, *, index: int = 0, **kwargs) -> np.ndarray:
        """Read Raw Image.

        Returns
        -------
        image: ndimage
            The image data
        """

        nd_image = None

        
        try:
            with rawpy.imread(self._image_file) as raw_image:
                self._image = raw_image.postprocess(**kwargs)
            nd_image = self._image
        except (AttributeError, TypeError) as ex:
            print(ex)
        except (rawpy.NotSupportedError, rawpy.LibRawError, rawpy.LibRawFatalError, rawpy.LibRawNonFatalError) as ex:
            print(ex)
        except Exception as ex:
            print(ex)

        return nd_image
    
    
