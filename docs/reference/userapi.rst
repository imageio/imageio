-----------
Core API v2
-----------

.. py:currentmodule:: imageio.v2

.. warning::

    This API exists for backwards compatibility. It is a wrapper around calls to
    the v3 API and new code should use the v3 API directly. Check the migration
    instructions below for detailed information on how to migrate.

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
    :toctree: ../_autosummary/

    imageio.v2.imread
    imageio.v2.mimread
    imageio.v2.volread
    imageio.v2.mvolread


Functions for writing
^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: ../_autosummary/

    imageio.v2.imwrite
    imageio.v2.mimwrite
    imageio.v2.volwrite
    imageio.v2.mvolwrite

More control
^^^^^^^^^^^^

For a larger degree of control, imageio provides functions
:func:`.get_reader` and :func:`.get_writer`. They respectively return an
:class:`.Reader` and an :class:`.Writer` object, which can
be used to read/write data and meta data in a more controlled manner.
This also allows specific scientific formats to be exposed in a way
that best suits that file-format.


.. autofunction:: imageio.v2.get_reader

.. autofunction:: imageio.v2.get_writer

----

.. autoclass:: imageio.core::Format.Reader
    :inherited-members:
    :members: 
    
.. autoclass:: imageio.core::Format.Writer
    :inherited-members:
    :members: 

.. _migration_from_v2:

Migrating to the v3 API
^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    Make sure to have a look at the :doc:`narrative docs for the v3 API <core_v3>`
    to build some intuition on how to use the new API.

The primary novelty of the v3 API compared to the v2 API is that images are now
treated as ndimages, a generalization of (flat) 2D images to N dimensions. This
change allows us to design a much simpler API; however, comes with a few
backwards incompatible changes.

.. rubric:: Avoiding Migration for Legacy Scripts

If you have an old script that you do not wish to migrate, you can avoid most of 
the migration by explicitly importing the v2 API::

    import imageio.v2 as imageio

This will give you access to most of the old API. However, calls will still rely
on the new (v3) plugins and backends, which may cause behavioral changes. As
such, you should prefer a full migration to v3 and should avoid using the v2 API
in new code. This is meant as a quick way for you to postpone a full migration
until it is convenient for you to do so.
  

Reading Images 
--------------

`iio.imread` can now return a ndimage instead of being limited to flat images.
As such, `iio.volread` has merged into `iio.imread` and is now gone. Similarily,
`iio.mimread` and `iio.mvolread` have merged into a new function called
`iio.imiter`, which returns a generator that yields ndimages from a file in the
order in which they appear. Further, the default behavior of `iio.imread` has
changed and it has become more context aware. Now it will either return the
first stored ndimage (like before) or, depending on the format, all images if
this is the more common use-case.

To reproduce similar behavior to the v2 API in cases where the incompatibility
matters use one of the following snippets::

    # img = iio.v2.imread(image_resource)
    img = iio.v3.imread(image_resource, index=...)[0]

    # img = iio.v2.volread(image_resource)
    img = iio.v3.imread(image_resource)
    
    # img = iio.v2.mimread(image_resource)
    # img = iio.v2.mvolread(image_resource)
    img = [im for im in iio.v3.imiter(image_resource)]

Writing Images
--------------

Similar to reading images, the new `iio.imwrite` can handle ndimages and lists
of images, like ``iio.mimwrite`` and consorts. ``iio.mimwrite``,
``iio.volwrite``, and ``iio.mvolwrite`` have all dissapeared. The same goes for
their aliases ``iio.mimsave``, ``iio.volsave``, ``iio.mvolsave``, and
``iio.imsave``. They are now all covered by ``iio.imwrite``.

To reproduce similar behavior to the v2 API behavior use one of the following
snippets::

    # img = iio.v2.imwrite(image_resource, ndimage)
    # img = iio.v2.volwrite(image_resource, ndimage)
    img = iio.v3.imwrite(image_resource, ndimage)

    # img = iio.v2.mimwrite(image_resource, list_of_ndimages)
    # img = iio.v2.mvolwrite(image_resource, list_of_ndimages)
    img = iio.v3.imwrite(image_resource, list_of_ndimages)

Reader and Writer
-----------------

Previously, the `reader` and `writer` objects provided an advanced way to
read/write data with more control. These are no longer needed. Likewise, the
functions ``iio.get_reader``, ``iio.get_writer``, ``iio.read``, and ``iio.save``
have become obsolete. Instead, the plugin object is used directly, which is
instantiated in mode ``r`` (reading) or  ``w`` (writing). To create such a
plugin object, call ``iio.imopen`` and use it as a context manager::

    # reader = iio.get_reader(image_resource)
    # reader = iio.read(image_resource)
    with iio.imopen(image_resource, "r") as reader:
        # file is only open/accessible here
        # img = reader.read(index=0)
        # meta = reader.metadata(index=0)
        # ...
        pass


    # writer = iio.get_writer(image_resource)
    # writer = iio.save(image_resource)
    with iio.imopen(image_resource, "w") as writer:
        # file is only open/accessible here
        # writer.write(ndimage)
        # ...
        pass

Metadata
--------

The v3 API makes handling of metadata much more consistent and explicit.
Previously in v2, metadata was provided as a ``dict`` that was attached to the
image by returning a custom subclass of ``np.ndarray``. Now metadata is
served independently from pixel data::

    # metadata = iio.imread(image_resource).meta
    metadata = iio.immeta(image_resource)

Further, ImageIO now provides a curated set of standardized metadata, which is
called :class:`ImageProperties <imageio.core.v3_plugin_api.ImageProperties>`, in
addition to above metadata. The difference between the two is as follows: The
metadata dict contains metadata using format-specific keys to the extent the
reading plugin supports them. The ImageProperties dataclass contains generally
available metadata using standardized attribute names. Each plugin provides the
same set of properties, and if the plugin or format doesn't provide a field it
is set to a default value; usually ``None``. To access ImageProperties use::

    props = iio.improps(image_resource)


Caveats and Notes
-----------------

This section is a collection of notes and feedback that we got from other
developers that were migrating to ImageIO V3, which might be useful to know
while you are migrating your own code.

- The old pillow plugin used to ``np.squeeze`` the image before writing it. This
  has been removed in V3 to match pillows native behavior. A trailing axis with
  dimension 1, e.g., ``(256, 256, 1)`` will now raise an exception. (see `#842
  <https://github.com/imageio/imageio/issues/842>`_)
- The old pillow plugin featured a kwarg called ``as_gray`` which would convert
  images to grayscale before returning them. This is redundant and has been
  deprecated in favor of using ``mode="L"``, which matches pillow's native
  kwarg.
- The old pillow plugin used to make an internal copy when reading 16-bit
  grayscale images from PNG. Pillow itself only offers limited support for
  16-bit arrays and typicalls uses 32-bit arrays to handle 16-bit images. In v2
  we changed the datatype internally and returned a 16-bit array. In v3 we avoid
  this copy, due to its performance implications (see `#931
  <https://github.com/imageio/imageio/issues/931>`_).

