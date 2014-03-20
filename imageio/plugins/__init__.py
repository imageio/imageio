# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 

.. note::
    imageio is under construction, some details with regard to the 
    Reader and Writer classes and how they should be implemented
    may still change. If you want to implement a plugin, maybe you
    can also help work out the details of the API for the Reader
    and Writer classes.


What is a plugin
----------------

In imageio, a plugin provides one or more imageio.Format objects, and 
corresponding imageio.Reader and imageio.Writer classes.
Each imageio.Format object represents an implementation to read/save a 
particular file format. Its Reader and Writer classes do the actual
reading/saving.

The reader and writer objects have a ``request`` attribute that can be
used to obtain information about the read or save request, such as
user-provided keyword arguments, as well get access to the raw image
data.


Registering
-----------

Strictly speaking a format can be used stand alone. However, to allow 
imageio to automatically select it for a specific file, the format must
be registered using ``imageio.formats.add_format()``. 

Note that a plugin is not required to be part of the imageio package; as
long as a format is registered, imageio can use it. This makes imageio very 
easy to extend.


What methods to implement
--------------------------

Imageio is designed such that plugins only need to implement a few
private methods. The public API is implemented by the base classes.
In effect, the public methods can be given a descent docstring which
does not have to be repeated at the plugins.

For the imageio.Format class, the following needs to be implemented/specified:

  * The format needs a short name, a description, and a list of file
    extensions that are common for the file-format in question.
  * Use a docstring to provide more detailed information about the
    format/plugin.
  * Implement ``_can_read(request)``, return a bool. See also the Request class.
  * Implement ``_can_save(request)``, dito.

For the imageio.Format.Reader class:
  
  * Implement ``_open(**kwargs)`` to initialize the reader, with the
    user-provided keyword arguments.
  * Implement ``_close()`` to clean up
  * Implement ``_get_length()`` to provide a suitable length based on what
    the user expects. Can be ``inf`` for streaming data.
  * Implement ``_get_data(index)`` to return an array and a meta-data dict.
  * Implement ``_get_meta_data(index)`` to return a meta-data dict. If index
    is None, it should return the 'global' meta-data.
  * Optionally implement ``_get_next_data()`` to provide allow streaming.

For the imageio.format.Writer class:
    
  * Implement ``_open(**kwargs)`` to initialize the writer, with the
    user-provided keyword arguments.
  * Implement ``_close()`` to clean up
  * Implement ``_append_data(im, meta)`` to add data (and meta-data).
  * Implement ``_set_meta_data(meta)`` to set the global meta-data.

"""

import imageio.plugins.animatedgif
import imageio.plugins.plugin_freeimage
import imageio.plugins.example
import imageio.plugins.dicom
import imageio.plugins.ffmpeg
