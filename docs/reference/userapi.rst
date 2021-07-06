-------------
Core API v2.9
-------------

.. py:currentmodule:: imageio.core.functions

These functions represent imageio's main interface for the user. They
provide a common API to read and write image data for a large
variety of formats. All read and write functions accept keyword
arguments, which are passed on to the backend that does the actual work.
To see what keyword arguments are supported by a specific format, use
the :func:`.help` function.

Functions for reading
^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _core_29/

    imageio.imread
    imageio.mimread
    imageio.volread
    imageio.mvolread


Functions for writing
^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _core_29/

    imageio.imwrite
    imageio.mimwrite
    imageio.volwrite
    imageio.mvolwrite

More control
^^^^^^^^^^^^

For a larger degree of control, imageio provides functions
:func:`.get_reader` and :func:`.get_writer`. They respectively return an
:class:`.Reader` and an :class:`.Writer` object, which can
be used to read/write data and meta data in a more controlled manner.
This also allows specific scientific formats to be exposed in a way
that best suits that file-format.

----

All read-functions return images as numpy arrays, and have a ``meta``
attribute; the meta-data dictionary can be accessed with ``im.meta``.
To make this work, imageio actually makes use of a subclass of
``np.ndarray``. If needed, the image can be converted to a plain numpy
array using ``np.asarray(im)``.

----

Supported resource URI's:

All functions described here accept a URI to describe the resource to
read from or write to. These can be a wide range of things. (Imageio
takes care of handling the URI so that plugins can access the data in
an easy way.)

For reading and writing:

* a normal filename, e.g. ``'c:\\foo\\bar.png'``
* a file in a zipfile, e.g. ``'c:\\foo\\bar.zip\\eggs.png'``
* a file object with a ``read()`` / ``write()`` method.

For reading:

* an http/ftp address, e.g. ``'http://example.com/foo.png'``
* the raw bytes of an image file
* ``get_reader("<video0>")`` to grab images from a (web) camera.
* ``imread("<screen>")`` to grab a screenshot (on Windows or OS X).
* ``imread("<clipboard>")`` to grab an image from the clipboard (on Windows).

For writing one can also use ``'<bytes>'`` or ``imageio.RETURN_BYTES`` to
make a write function return the bytes instead of writing to a file.

Note that reading from HTTP and zipfiles works for many formats including
png and jpeg, but may not work for all formats (some plugins "seek" the
file object, which HTTP/zip streams do not support). In such a case one
can download/extract the file first. For HTTP one can use something
like ``imageio.imread(imageio.core.urlopen(url).read(), '.gif')``.


----

.. autofunction:: imageio.help

.. autofunction :: imageio.show_formats


----

.. autofunction:: imageio.get_reader

.. autofunction:: imageio.get_writer

----

.. autoclass:: imageio.core.format.Reader
    :inherited-members:
    :members: 
    
.. autoclass:: imageio.core.format.Writer
    :inherited-members:
    :members: 
