# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" This module defines the classes that make up the plugin system:
The Format and FormatCollection classes.

The actual plugins are in the plugins subpackage. 
"""


class Plugin:
    """ The plugin class is an abstract class. With a plugin we refer
    to either a Format or a FormatCollection.
    """
    
    def can_read_im(self, filename, first_bytes):
        pass
        
    def can_read_ims(self, filename, first_bytes):
        pass
    
    def can_read_vol(self, filename, first_bytes):
        pass
    
    def can_save_im(self, filename):
        pass
    
    def can_save_ims(self, filename):
        pass
    
    def can_save_vol(self, filename):
        pass
    


class FormatCollection(Plugin):
    """ The format collection represents a set of formats that are in some
    way related. For instance, all formats of freeimage are supported through
    a single format collection.
    
    A format collection can contain multiple Format instance and even 
    have multiple format collections (you can add these with add_plugin).
    
    To create a FormatCollection, implement the can_read and can_save
    methods; they should return a format that can read the image or None.
    
    """
    
    def __init__(self):
        self._format_collections = []
        self._formats = []
    
    def add_plugin(self, plugin):
        if isinstance(plugin, Format):
            self._formats.append(plugin)
        elif isinstance(plugin, FormatCollection):
            self._format_collections.append(plugin)
        else:
            raise ValueError('add_plugin needs argument to be a Format of FormatCollection.')
    
    
    def supported_formats(self):
        formats = []
        for fc in self._format_collections:
            formats.extend(fc.supported_formats())
        formats.extend(self._formats)
        return formats
    
    def can_read_im(self, filename, first_bytes):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_read_im()
            if res:
                return res
    
    def can_read_ims(self, filename, first_bytes):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_read_ims()
            if res:
                return res
    
    def can_read_vol(self, filename, first_bytes):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_read_vol()
            if res:
                return res
    
    def can_save_im(self, filename):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_save_im()
            if res:
                return res
    
    def can_save_ims(self, filename):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_save_ims()
            if res:
                return res
    
    def can_save_vol(self, filename):
        plugins = self._format_collections + self._formats
        for plug in plugins:
            res = plug.can_save_vol()
            if res:
                return res



class Format(Plugin):
    """ A format represents an implementation to read/save a particular 
    file format.
    
    To create a format, implement the imread, imsave, etc. methods. To let 
    imageio know what files a Format instance can handle, it should either
    let a FormatCollection handle that, or one needs to implement 
    the can_read and can_save methods.
    
    todo: maybe it is sometimes enough to only specify the extensions.
    
    A new format must be registered by either adding it via 
    imageio.plugins.root_plugin.add_plugin(), or by having it wrapped
    with a FormatCollection.
    
    """
    # todo: maybe it is sometimes enough to only specify the extensions.
    # todo: better docs on the two ways one can create a plugin.
    
    def __init__(self, name, description):
        self._name = name.upper()
        self._description = description
    
    def __repr__(self):
        return '<Format %s - %s>' % (self.name, self.description)
    
    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    
    def supported_extensions(self):
        """ Return a list of file extensions supported by this plugin.
        """
        pass # todo: We can use this also in can_read / can_write
    
    
    def imread(self, filename, **kwargs):
        raise NotImplemented()
    
    def imsread(self, filename, **kwargs):
        raise NotImplemented()
    
    def volread(self, filename, **kwargs):
        raise NotImplemented()
    
    
    def imsave(self, filename, im, **kwargs):
        raise NotImplemented()
    
    def imssave(self, filename, ims, **kwargs):
        raise NotImplemented()
    
    def volsave(self, filename, vol, **kwargs):
        raise NotImplemented()
    
