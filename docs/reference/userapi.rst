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

.. note::
    All read-functions return images as numpy arrays, and have a ``meta``
    attribute; the meta-data dictionary can be accessed with ``im.meta``.
    To make this work, imageio actually makes use of a subclass of
    ``np.ndarray``. If needed, the image can be converted to a plain numpy
    array using ``np.asarray(im)``.

.. autofunction:: imageio.help

.. autofunction :: imageio.show_formats


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


.. autofunction:: imageio.get_reader

.. autofunction:: imageio.get_writer

----

.. autoclass:: imageio.core.format.Reader
    :inherited-members:
    :members: 
    
.. autoclass:: imageio.core.format.Writer
    :inherited-members:
    :members: 
