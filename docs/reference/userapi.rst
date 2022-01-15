-----------
Core API v2
-----------

.. py:currentmodule:: imageio.v2

.. warning::
    This API is deprecated and will be superseeded by :doc:`the v3 API <core_v3>`
    starting with ImageIO v3. Check the migration instructions below for
    detailed information on how to migrate.

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

    imageio.imread
    imageio.mimread
    imageio.volread
    imageio.mvolread


Functions for writing
^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: ../_autosummary/

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

.. _migration_from_v2:

Migrating to ImageIO v3
^^^^^^^^^^^^^^^^^^^^^^^

The primary novelty of the v3 API compared to the v2 API is that images are now
treated as ndimages, a generalization of (flat) 2D images to N dimensions. This
change allows us to design a much simpler API; however, comes with a few
backwards incompatible changes.

Avoiding API Migration for Legacy Scripts
-----------------------------------------

If you have an old script where you do not wish to migrate the API, you can
explicitly import the old v2 API and avoid migration. While this will keep the
old (v2) API, it will rely on the new (v3) plugins and backends, which may
contain other backwards incompatible changes. As such, you should prefer a full
migration to v3 and should avoid using the v2 API in new code. To import the v2
API, depending on your script/code, use::

    import imageio.v2 as iio
    import imageio.v2 as imageio
  

Reading Images 
--------------

`iio.imread` can now return a ndimage instead of being limited to flat images.
As such, `iio.volread` has merged into `iio.imread` and is now gone. Similarily,
`iio.mimread` and `iio.mvolread` have merged into a new function called
`iio.imiter`, which returns a generator that yields ndimages from a file in the
order in which they appear. Further, the default behavior of `iio.imread` has
changed, and it now returns the first ndimage (instead of the first flat image)
if the image contains multiple images.

To reproduce similar behavior to the v2 API behavior use one of the following
snippets::

    # img = iio.v2.imread(image_resource)
    try:
        img = iio.v3.imread(image_resource, index=None)[0]
    except ValueError:
        img = iio.v3.imread(image_resource, index=0)

    # img = iio.v2.volread(image_resource)
    img = iio.v3.imread(image_resource)
    
    # img = iio.v2.mimread(image_resource)
    # img = iio.v2.mvolread(image_resource)
    img = [im for im in iio.v3.imiter(image_resource)]

Writing Images
--------------

Similar to reading images, the new `iio.imwrite` can handle ndimages.
``iio.mimwrite``, ``iio.volwrite``, and ``iio.mvolwrite`` have all dissapeared.
The same goes for their aliases ``iio.mimsave``, ``iio.volsave``,
``iio.mvolsave``, and ``iio.imsave``. They are now all covered by
``iio.imwrite``.

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

Plugins now longer have nested ``Reader`` and ``Writer`` classes and they are no
longer global singletons. Instead, a new plugin object is instantiated in mode ``r``
(reading) or  ``w`` (writing) for each `ImageResource` being opened.
As such, the functions ``iio.get_reader``, ``iio.get_writer``, ``iio.read``, and
``iio.save`` have become obsolete and the plugin object is used directly
instead. Using these is considered advanced usage, happens inside a context
manager, and uses `iio.imopen`::

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

Further, ImageIO now provides a curated set of standardized metadata which is
called ImageProperties in addition to above metadata. The difference between the
two is as follows: The metadata dict contains metadata using format-specific
keys to the extent the reading plugin supports them. The ImageProperties
dataclass contains metadata using standardized attribute names. Each plugin
provides the same set of properties, and if the plugin or format doesn't provide a field
it is set to a (sensible) default value. To access
ImageProperties use::

    props = iio.improps(image_resource)
