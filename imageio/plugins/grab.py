"""
PIL-based formats to take screenshots and grab from the clipboard.
"""

from __future__ import absolute_import, print_function, division

import sys
import threading

import numpy as np

from .. import formats
from ..core import Format


class BaseGrabFormat(Format):
    """ Base format for grab formats.
    """
    
    _pillow_imported = False
    _ImageGrab = None
    
    def __init__(self, *args, **kwargs):
        super(BaseGrabFormat, self).__init__(*args, **kwargs)
        self._lock = threading.RLock()
    
    def _can_write(self, request):
        return False
    
    def _init_pillow(self):
        with self._lock:
            if not self._pillow_imported:
                self._pillow_imported = True  # more like tried to import
                import PIL
                if not hasattr(PIL, 'PILLOW_VERSION'):
                    raise ImportError('Imageio Pillow requires '
                                      'Pillow, not PIL!')
                from PIL import ImageGrab
                self._ImageGrab = ImageGrab
            elif self._ImageGrab is None:
                raise RuntimeError('Imageio grab plugin requires Pillow lib.')
            ImageGrab = self._ImageGrab
        return ImageGrab
    
    class Reader(Format.Reader):
        
        def _open(self):
            pass
        
        def _close(self):
            pass
        
        def _get_data(self, index):
            return self.format._get_data(index)


class ScreenGrabFormat(BaseGrabFormat):
    """ The ScreenGrabFormat provided a means to grab screenshots using
    the uri of "<screen>".
    
    This functionality is provided via Pillow. Note that "<screen>" is
    only supported on Windows and OS X.
    
    Parameters for reading
    ----------------------
    No parameters.
    """
    
    def _can_read(self, request):
        if request.mode[1] not in 'i?':
            return False

        if not (sys.platform.startswith('win') or
                sys.platform.startswith('darwin')):
            return False  # not supported on Linux by Pillow
        
        if request.filename != '<screen>':
            return False
        
        self._init_pillow()
        return True
    
    def _get_data(self, index):
        ImageGrab = self._init_pillow()
        
        pil_im = ImageGrab.grab()
        assert pil_im is not None
        im = np.asarray(pil_im)
        return im, {}


class ClipboardGrabFormat(BaseGrabFormat):
    """ The ClipboardGrabFormat provided a means to grab image data from
    the clipboard, using the uri "<clipboard>"
    
    This functionality is provided via Pillow. Note that "<clipboard>" is
    only supported on Windows.
    
    Parameters for reading
    ----------------------
    No parameters.
    """
    
    def _can_read(self, request):
        if request.mode[1] not in 'i?':
            return False

        if not sys.platform.startswith('win'):
            return False  # not supported on Linux or OS X by Pillow
        
        if request.filename != '<clipboard>':
            return False
        
        self._init_pillow()
        return True
    
    def _get_data(self, index):
        ImageGrab = self._init_pillow()
        
        pil_im = ImageGrab.grabclipboard()
        if pil_im is None:
            raise RuntimeError('There seems to be no image data on the '
                                'clipboard now.')
        im = np.asarray(pil_im)
        return im, {}


# Register. You register an *instance* of a Format class.
format = ScreenGrabFormat('screengrab',
                          'Grab screenshots (Windows and OS X only)', [], 'i')
formats.add_format(format)

format = ClipboardGrabFormat('clipboardgrab',
                             'Grab from clipboard (Windows only)', [], 'i')
formats.add_format(format)
