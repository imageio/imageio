# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 

What is a plugin
----------------

In imageio, a plugin provides one or more Format objects, and corresponding
Reader and Writer classes.

Each Format object represents an implementation to read/save a particular 
file format. The Reader and Writer classes do the actual reading/saving.


Registering
-----------

Strictly speaking a format can be used stand alone. However, to allow 
imageio to automatically select it for a specific file, the format must
be registered using imageio.formats.add_format(). 

Note that a plugin is not required to be part of the imageio package; as
long as a format is registered, imageio can use it. This makes imageio very 
easy to extend.


What methods to implement
--------------------------

Imageio is designed such that plugins mostly only need to implement 
private methods. These private methods are called from public methods.
In effect, the public methods can be given a descent docstring which
does not have to be repeated at the plugins.

For the Format class, the following needs to be implemented/specified:

  * The format needs a short name, a description and a list of file extensions
    that are common for the file-format in question.
  * Use a docstring to provide more detailed information about the format/plugin.
  * Set the _readerClass and _writerClass attributes. 
  * Implement _can_read(request), return a bool. See also the Request class.
  * Implement _can_save(request), dito.

For the Reader class:
    
  * Implement _read_data(*indices, **kwargs)
  * Implement _read_info(*indices, **kwargs), empty indices means global info.
  * Implement _mshape(), should implement the shape of the data. 1 for single
    image, 5 for 5 images (4,5) for a series of 4 images of 5 stacks, etc.
    Under construction... we might also want to specify that we dont know
    the number if images.
  * _close() - close files, release resources.

For the Writer class:
    
  * Implement _save_data(data, *indices, **kwargs)
  * Implement _save_info(info, *indices, **kwargs), empty indices means global info.
  * _close() - close files, release resources.

"""

import imageio.plugins.plugin_freeimage
