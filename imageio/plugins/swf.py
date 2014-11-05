# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" SWF plugin. Most of the actual work is done in _swf.py.
"""

from __future__ import absolute_import, print_function, division

from io import BytesIO
import zlib

import numpy as np

from imageio import formats
from imageio.core import Format
from imageio.core.request import read_n_bytes

from . import _swf


class SWFFormat(Format):
    """ 
    
    
    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.
    
    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.
    
    """
    
    def _can_read(self, request):
        if request.mode[1] in (self.modes + '?'):
            tmp = request.firstbytes[0:3].decode('ascii', 'ignore')
            if tmp in ('FWS', 'CWS'):
                return True
    
    def _can_save(self, request):
        if request.mode[1] in (self.modes + '?'):
            for ext in self.extensions:
                if request.filename.endswith('.' + ext):
                    return True
    
    # -- reader
    
    class Reader(Format.Reader):
    
        def _open(self):
            
            self._fp = self.request.get_file()
            
            # Check file ...
            tmp = self.request.firstbytes[0:3].decode('ascii', 'ignore')
            if tmp == 'FWS':
                pass  # OK
            elif tmp == 'CWS':
                # Compressed, we need to decompress
                bb = self._fp.read()
                bb = bb[:8] + zlib.decompress(bb[8:])
                # Wrap up in a file object
                self._fp = BytesIO(bb)
            else:
                raise IOError('This does not look like a valid SWF file')
            
            # Skip head
            self._fp_read(8)
            nbits = _swf.bits2int(self._fp_read(1), 5)
            nbits = 5 + nbits * 4
            Lrect = nbits / 8.0
            if Lrect % 1:
                Lrect += 1
            Lrect = int(Lrect)
            self._fp_read(Lrect + 3)
            
            # Init counter
            self._framecounter = 0
        
        def _fp_read(self, n):
            return read_n_bytes(self._fp, n)
        
        def _close(self):
            pass
        
        def _get_length(self):
            return np.inf  # we don't know
        
        def _get_data(self, index):
            
            # Check index
            if index < 0:
                raise IndexError('Index in swf file must be > 0')
            elif index != self._framecounter:
                raise RuntimeError('SWF format does not support seeking')
            
            # Read tags until we see an image
            while True:
                im = self._read_one_tag()
                if im is not None:
                    self._framecounter += 1
                    return im, {}
        
        def _read_one_tag(self):
            
            # Get head
            head = self._fp_read(6)
            if not head:
                raise IndexError('Reached end of swf movie')
            
            # Determine type and length
            T, L1, L2 = _swf.get_type_and_len(head)
            if not L2:
                raise RuntimeError('Invalid tag length, could not proceed')
            
            # Read data
            bb = self._fp_read(L2 - 6)
            
            # Parse tag
            if T == 0:
                raise IndexError('Reached end of swf movie')
            elif T in [20, 36]:
                im = _swf.read_pixels(bb, 0, T, L1)  # can be None
            elif T in [6, 21, 35, 90]:
                im = None
                print('Ignoring JPEG image: cannot read JPEG.')
            else:
                im = None  # Not an image tag
            
            # Done.  Return image. Can be None
            return im
        
        def _get_meta_data(self, index):
            return {}  # This format does not support meta data
    
    # -- writer
    
    class Writer(Format.Writer):
        
        def _open(self, fps=12, loop=True): 
            self._arg_fps = int(fps)
            self._arg_loop = bool(loop)
            
            self._fp = self.request.get_file()
            self._framecounter = 0
        
        def _write_header(self, framesize, fps):
            # Called as soon as we know framesize; when we get first frame
            bb = b''
            bb += 'F'.encode('ascii')  # uncompressed
            bb += 'WS'.encode('ascii')  # signature bytes
            bb += _swf.int2uint8(8)  # version
            bb += '0000'.encode('ascii')  # FileLength (leave open for now)
            bb += _swf.Tag().make_rect_record(0, framesize[0], 0, framesize[1]).tobytes()
            bb += _swf.int2uint8(0) + _swf.int2uint8(fps)  # FrameRate
            self._location_to_save_nframes = len(bb)
            bb += '00'.encode('ascii')  # nframes (leave open for now)
            self._fp.write(bb)
            
            # Write some initial tags
            taglist = _swf.FileAttributesTag(), _swf.SetBackgroundTag(0, 0, 0)
            for tag in taglist:
                self._fp.write(tag.get_tag())
        
        def _close(self):
            # What if no images were saved?
            if not self._framecounter:
                self._write_header((10, 10), self._arg_fps)
            # Write stop tag if we do not loop
            if not self._arg_loop:
                self._fp.write(_swf.DoActionTag('stop').get_tag())
            # finish with end tag
            self._fp.write('\x00\x00'.encode('ascii'))
            # set size
            sze = self._fp.tell()
            self._fp.seek(4)
            self._fp.write(_swf.int2uint32(sze))
            # set nframes
            self._fp.seek(self._location_to_save_nframes)
            self._fp.write(_swf.int2uint16(self._framecounter))
        
        def _append_data(self, im, meta):
            # Get frame size
            wh = im.shape[1], im.shape[0]
            # Write header on first frame
            isfirstframe = False
            if self._framecounter == 0:
                isfirstframe = True
                self._write_header(wh, self._arg_fps)
            # Create tags
            bm = _swf.BitmapTag(im)
            sh = _swf.ShapeTag(bm.id, (0, 0), wh)
            po = _swf.PlaceObjectTag(1, sh.id, move=(not isfirstframe))
            sf = _swf.ShowFrameTag()
            # Write tags
            for tag in [bm, sh, po, sf]:
                self._fp.write(tag.get_tag())
            self._framecounter += 1
        
        def set_meta_data(self, meta):
            pass


# Register. You register an *instance* of a Format class. Here specify:
format = SWFFormat('swf',  # shot name
                   'Shockwave flash',  # one line descr.
                   '.swf',  # list of extensions as a space separated string
                   'I'  # modes, characters in iIvV
                   )
formats.add_format(format)
