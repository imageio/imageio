# -*- coding: utf-8 -*-
# Copyright (c) 2016, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

from __future__ import absolute_import, print_function, division

import numpy as np

from .. import formats
from ..core import Format, image_as_uint

# Get info about pillow formats without having to import PIL
from .pillow_info import pillow_formats, pillow_docs

# todo: Pillow ImageGrab module supports grabbing the screen on Win and OSX.
# todo: also ImageSequence module -> GIF


class PillowFormat(Format):
    """
    Base format class for Pillow formats.
    """
    
    _pillow_imported = False
    _Image = None
    
    @property
    def plugin_id(self):
        """ The PIL plugin id.
        """
        return self._plugin_id  # Set when format is created
    
    def _init_pillow(self):
        if not self._pillow_imported:
            self._pillow_imported = True  # more like tried to import
            import PIL
            if not hasattr(PIL, 'PILLOW_VERSION'):
                raise ImportError('Imageio Pillow plugin needs Pillow, not PIL!')
            from PIL import Image
            self._Image = Image
        elif self._Image is None:
            raise RuntimeError('Imageio Pillow plugin cannot work without Pillow.')
        
        Image = self._Image
        if self.plugin_id in ('PNG', 'JPEG', 'BMP', 'GIF', 'PPM'):
            Image.preinit()
        else:
            Image.init()
        return Image
    
    def _can_read(self, request):
        Image = self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if self.plugin_id in Image.OPEN:
                factory, accept = Image.OPEN[self.plugin_id]
                if not accept or accept(request.firstbytes):
                    return True
    
    def _can_write(self, request):
        Image = self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if request.filename.lower().endswith(self.extensions):
                if self.plugin_id in Image.SAVE:
                    return True
    
    
    class Reader(Format.Reader):
    
        def _open(self, **kwargs):
            Image = self.format._init_pillow()
            try:
                factory, accept = Image.OPEN[self.format.plugin_id]
            except KeyError:
                raise RuntimeError('Format %s cannot read images.' %
                                   self.format.name)
            self._im = factory(self.request.get_file(), '')
            if hasattr(Image, '_decompression_bomb_check'):
                Image._decompression_bomb_check(self._im.size)
            self._length = 1  # todo: overload in GIF format
        
        def _close(self):
            self._im.close()
        
        def _get_length(self):
            return self._length
        
        def _get_data(self, index):
            if index >= self._length:
                raise IndexError('Image index %i > %i' % (index, self._length))
            im = np.asarray(self._im)
            return im, self._im.info
        
        def _get_meta_data(self, index):
            return self._im.info
    
    
    class Writer(Format.Writer):
        
        def _open(self, **kwargs):   
            Image = self.format._init_pillow()
            try:
                self._save_func = Image.SAVE[self.format.plugin_id]
            except KeyError:
                raise RuntimeError('Format %s cannot write images.' %
                                   self.format.name)
            self._fp = self.request.get_file()
            self._meta = {}
            self._meta.update(kwargs)
            self._written = False
        
        def _close(self):
            pass
        
        def _append_data(self, im, meta):
            if self._written:
                raise RuntimeError('Format %s only supports single images.' %
                                   self.format.name)
            self._written = True
            self._meta.update(meta)
            im = self.format._Image.fromarray(im)
            im.encoderinfo = self._meta
            self._save_func(im, self._fp, '')
            im.close()
        
        def set_meta_data(self, meta):
            self._meta.update(meta)


def register_pillow_formats():
    
    for id, summary, ext in pillow_formats:
        format = PillowFormat(id + '-PIL', summary, ext, 'i')
        format._plugin_id = id
        format.__doc__ = pillow_docs[id]
        formats.add_format(format)


register_pillow_formats()
