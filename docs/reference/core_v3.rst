-----------
Core API v3
-----------

.. py:currentmodule:: imageio.v3

.. note::
    For migration instructions from the v2 API check :ref:`our migration guide
    <migration_from_v2>`.

This API provides a functional interface to all of ImageIOs backends. It is
split into two parts: :ref:`Everyday Usage <v3_basic_usage>` and :ref:`Advanced
Usage <v3_advanced_usage>`. The first part (everyday usage) focusses on sensible
defaults and automation to cover everyday tasks such as plain reading or writing
of images. The second part (advanced usage) focusses on providing fully-featured
and performant access to all the features of a particular backend.

API Overview
------------

.. autosummary::
    :toctree: ../_autosummary/

    imageio.v3.imread
    imageio.v3.imwrite
    imageio.v3.imiter
    imageio.v3.improps
    imageio.v3.immeta
    imageio.v3.imopen

.. _v3_basic_usage:

Everyday Usage
--------------

Reading and Writing
^^^^^^^^^^^^^^^^^^^

Frequently, the image-related IO you wish to perform can be summarized as "I
want to load X as a numpy array.", or "I want to save my array as a XYZ file".
This should not be complicated, and it is, in fact, as simple as calling the
corresponding function::

    import imageio.v3 as iio

    # reading:
    img = iio.imread("imageio:chelsea.png")
    
    # writing:
    iio.imwrite("out_image.jpg", img)

    # (Check the examples section for many more examples.)

Both functions accept any :doc:`ImageResource <../user_guide/requests>` as
their first argument, which means you can read/write almost anything image
related; from simple JPGs through ImageJ hyperstacks to MP4 video or RAW formats.
Check the :doc:`Supported Formats <../formats/index>` docs for a list of all formats
(that we are aware of).

If you do need to customize or tweak this process you can pass additional keyword
arguments (`kwargs`) to overwrite any defaults ImageIO uses when reading or
writing. The following `kwargs` are always available:

- ``plugin``: The name of the plugin to use for reading/writing.
- ``extension``: Treat the provided ImageResource as if it had the given
  extension.
- ``index`` (reading only): The index of the ndimage to read. Useful if the format
  supports storing more than one (GIF, multi-page TIFF, video, etc.).

Additional `kwargs` are specific to the plugin being used and you can find a
list of available ones in the documentation of the specific plugin (where they
are listed as parameters). A list of all available plugins can be found :ref:`here
<supported_backends>` and you can read more about the above kwargs in
the documentation of the respective function (imread/imwrite/etc.).

Handling Metadata
^^^^^^^^^^^^^^^^^

ImageIO serves two types of metadata: ImageProperties and format-specific metadata.

:class:`ImageProperties <imageio.core.v3_plugin_api.ImageProperties>` are a
collection of standardized metadata fields and are supported by all plugins and
for all supported formats. If a file doesn't carry the relevant field or if a
format doesn't support it, its value is set to a sensible default. You can
access the properties of an image by calling :func:`improps
<imageio.v3.improps>`::

    import imageio.v3 as iio

    props = iio.improps("imageio:newtonscradle.gif")
    props.shape
    props.dtype
    # ...

As with the other functions of the API, you can pass generally available kwargs
(`plugin`, `index`, ...) to `improps` to modify the behavior. Plugins may
specify additional plugin-specific keyword arguments, and those are documented
in the plugin-specific docs. Further, accessing this metadata is efficient in 
the sense that it doesn't load (decode) pixel data.

Format-specific metadata is handled by :func:`immeta <imageio.v3.immeta>`::

    import imageio.v3 as iio

    meta = iio.immeta("imageio:newtonscradle.gif")

It returns a dictionary of non-standardized metadata fields. It, too, supports
general kwargs (`plugin`, `index`, ...) which may be extended by a specific
plugin. Further, it accepts a kwarg called ``exclude_applied``. If set to True,
this will remove any items from the dictionary that would be consumed by a read
call to the plugin. For example, if the metadata sets a rotation flag (the raw
pixel data should be rotated before displaying it) and the plugin's read call
will rotate the image because if it, then setting ``exclude_applied=True`` will
remove the rotation field from the returned metadata. This can be useful to keep
an image and it's metadata in sync.

Further, this type of metadata is much more specific than ImageProperties
because different plugins (and formats) may return and support different fields.
This means that you can get much more specific metadata for a format, e.g., a
frame's side data in a video format, but you need to be mindful of the plugin
and format used because these fields may not exist all the time, e.g., jpeg and
most other image formats have no side data. In general we try to match a fields
name to the name it has in a format; however, we may adjust this if the name is
not a valid python string. The best way to know which fields exist for your
specific ImageResource is to call ``immeta`` on it and inspect the result.

.. _v3_advanced_usage:

Advanced Usage
--------------

Iterating Video and Multi-Page Formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some formats (GIF, MP4, TIFF, among others) allow storage of more than one
ndimage in the same file, and you may wish to process all ndimages in such a
file instead of just a single one. While :func:`iio.imread(...)
<imageio.core.v3_api.imread>` allows you to read all ndimages and stack them
into a ndarray (using `index=...`; check the docs), this comes with two
problems:

- Some formats (e.g., SPE or TIFF) allow multiple ndimages with different shapes
  in the same file, which prevents stacking.
- Some files (especially video) are too big to fit into memory when loaded all
  at once.

To address these problems, the v3 API introduces :func:`iio.imiter
<imageio.core.v3_api.imiter>`; a generator yielding ndimages in the order in
which they appear in the file::

    import imageio.v3 as iio

    for frame in iio.imiter("imageio:cockatoo.mp4"):
        pass # do something with each frame

Just like imread, imiter accepts additional `kwargs` to overwrite any defaults
used by ImageIO. Like before, the :func:`function-specific documentation
<imageio.core.v3_api.imiter>` details the `kwargs` that are always present, and
additional kwargs are plugin specific and documented by the respective plugin.

Low-Level Access
^^^^^^^^^^^^^^^^

At times you may need low-level access to a plugin or file, for example,
because:

- you wish to have fine-grained control over when the file is opened/closed.
- you need to perform multiple IO operations and don't want to open the file
  multiple times.
- a plugin/backend offers unique features not otherwise exposed by the
  high-level API.

For these cases the v3 API offers :func:`iio.v3.imopen
<imageio.core.imopen.imopen>`. It provides a context manager that initializes
the plugin and opens the file for reading (``"r"``) or writing (``"w"``),
similar to the Python built-in function ``open``::

    import imageio.v3 as iio

    with iio.imopen("imageio:chelsea.png", "r") as image_file:
        props = image_file.properties()
        # ... configure HPC pipeline and unicorns
        img = image_file.read()
        # image_file.plugin_specific_function()

Similar to above, you can pass the ``plugin`` `kwarg` to imopen to control the
plugin that is being used. The returned plugin instance (`image_file`) exposes
the :class:`v3 plugin API <imageio.core.v3_plugin_api.PluginV3>`, and can be
used for low-level access.
