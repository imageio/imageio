# -*- coding: utf-8 -*-
# Copyright (c) 2016, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

from __future__ import absolute_import, print_function, division

import numpy as np

from .. import formats
from ..core import Format, image_as_uint

try:
    import PIL
    if not hasattr(PIL, 'PILLOW_VERSION'):
        raise ImportError('Imageio Pillow plugin needs Pillow, not PIL!')
except ImportError as err:
    raise

from PIL import Image

# Image.ID - list of plugin id's
# Image.OPEN - dict of id: (factory, accept)
# Image.SAVE - dict of id: (write) ?
# Image.EXTENSION - dict of ext: id

# Get docs: https://raw.githubusercontent.com/python-pillow/Pillow/master/docs/handbook/image-file-formats.rst

FULL_FORMATS = set(Image.ID).intersection(Image.SAVE.keys())
READABLE_FORMATS = set(Image.ID).intersection(Image.OPEN.keys()).difference(FULL_FORMATS)


FULL_FORMATS = ('.bmp', '.eps', '.gif', '.icns', '.im',
                '.jpeg', '.jpg', '.jpeg2000',
                '.msp', '.pcx', '.png', '.ppm', '.spider', '.tiff', '.webp',
                '.xbm')

READABLE_FORMATS = ('.cur', '.dcx', '.dds', '.fli', '.flc', '.fpx', '.gbr',
                    '.gd', '.ico', '.icns', '.imt', '.iptc', '.naa', '.mcidas',
                    '.mpo', '.pcd', '.psd', '.cgi', '.tga', '.wal', '.xpm')

WRITABLE_FORMATS = ('.palm', '.pdf', '.pixar')

# Pillow "knows" these, without being able to read or write them
IDENTIFIABLE_FORMATS = ('.bufr', '.fits', '.grib', '.hdf5', '.mpeg', '.wmf')


# todo: Pillow ImageGrab module supports grabbing the screen on Win and OSX. how awesome it that!

# todo: also ImageSequence module

# todo: format has short name by default, unless it already exists,
# in which case it gets a "PIL_" prefix. Make possible to use that prefix
# even for the formats that got the prefix-less name.



class PillowFormat(Format):
    """ The dummy format is an example format that does nothing.
    It will never indicate that it can read or write a file. When
    explicitly asked to read, it will simply read the bytes. When 
    explicitly asked to write, it will raise an error.
    
    This documentation is shown when the user does ``help('thisformat')``.
    
    Parameters for reading
    ----------------------
    Specify arguments in numpy doc style here.
    
    Parameters for saving
    ---------------------
    Specify arguments in numpy doc style here.
    
    """
    
    @property
    def plugin_id(self):
        """ The PIL plugin id.
        """
        return self._plugin_id  # Set when format is created
    
    def _init_pillow(self):
        # Init Pillow
        if self.plugin_id in ('PNG', 'JPEG', 'BMP', 'GIF', 'PPM'):
            Image.preinit()
        else:
            Image.init()
    
    def _can_read(self, request):
        self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if self.plugin_id in Image.OPEN:
                factory, accept = Image.OPEN[self.plugin_id]
                if not accept or accept(request.firstbytes):
                    return True
    
    def _can_write(self, request):
        self._init_pillow()
        if request.mode[1] in (self.modes + '?'):
            if request.filename.lower().endswith(self.extensions):
                if self.plugin_id in Image.SAVE:
                    return True
    
    # -- reader
    
    class Reader(Format.Reader):
    
        def _open(self, **kwargs):
            self.format._init_pillow()
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
    
    # -- writer
    
    class Writer(Format.Writer):
        
        def _open(self, **kwargs):   
            self.format._init_pillow()
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
            im = Image.fromarray(im)
            im.encoderinfo = self._meta
            self._save_func(im, self._fp, '')
            im.close()
        
        def set_meta_data(self, meta):
            self._meta.update(meta)


pngformat = PillowFormat('PNG-PIL', "Portable network graphics", '.png', 'i')
pngformat._plugin_id = 'PNG'
pngformat.__doc__ = 'blabla docs for png'
formats.add_format(pngformat)

# # Register. You register an *instance* of a Format class. Here specify:
# format = DummyFormat('dummy',  # short name
#                      'An example format that does nothing.',  # one line descr.
#                      '.foobar .nonexistentext',  # list of extensions
#                      'iI'  # modes, characters in iIvV
#                      )
# formats.add_format(format)
