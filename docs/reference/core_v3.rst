-----------
Core API v3
-----------

.. py:currentmodule:: imageio.core.v3_api

.. note::
    For migration instructions from the v2 API check :ref:`our migration guide
    <migration_from_v2>`.

This API provides a functional interface to all of ImageIOs backends. It is
split into two parts: :ref:`Everyday Usage <v3_basic_usage>` and :ref:`Advanced
Usage <v3_advanced_usage>`. The first part (everyday usage) focusses on sensible
defaults and automation to cover everyday tasks such as plain reading or writing
of images. The second part (advanced usage) focusses on providing fully-featured
and performant access to all the a particular backend.

API Overview
------------

.. autosummary::
    :toctree: _core_v3/

    imageio.core.v3_api.imread
    imageio.core.v3_api.imwrite
    imageio.core.v3_api.imiter

.. _v3_basic_usage:

Everyday Usage
--------------

Most of the time, the image-related IO we wish to perform can be described as "I
want to load X as a numpy array.", or "I want to save my array as a XYZ file".
This should not be complicated, and it is, in fact, as simple as calling the
corresponding function::

    import imageio as iio

    # reading:
    img = iio.v3.imread("imageio:chelsea.png")
    
    # writing:
    iio.v3.imwrite("out_image.jpg", img)

Both functions accept any :doc:`ImageResource <../getting_started/requests>` as
their first argument, which means we can read/write almost anything image
related; from simple JPGs through ImageJ hyperstacks to MP4 video or various
niche RAW formats.

If we do need to customize or tweak this process we can pass additional keyword
arguments (`kwargs`) to overwrite any defaults ImageIO uses when reading or writing.
The two `kwargs` that are always available are:

- ``plugin``: The name of the plugin to use for reading/writing.
- ``index`` (reading only): The index of the ndimage to read, if the format
  supports storing more than one (GIF, multi-page TIFF, video, etc.).

Additional `kwargs` are specific to the plugin being used and we can find a list
of available ones in the documentation of the specific plugin (where they
are called parameters). A list of all available plugins can be found :ref:`here
<supported_backends>`.

.. _v3_advanced_usage:

Advanced Usage
--------------

Iterating Video and Multi-Page Formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some formats (GIF, MP4, TIFF, among others) allow storage of more than one
ndimage in the same file, and often we wish to do processing on all ndimages in
such a file instead of just a single one. While :func:`iio.v3.imread(...,
index=None) <imageio.core.v3_api.imread>` allows us to read all ndimages and
stack them into a ndarray, this comes with two problems:

- Some formats (e.g., SPE or TIFF) allow multiple ndimages with different shapes
  in the same file, which prevents stacking.
- Some files (especially video) are
  too big to fit into memory when loaded all at once.

To address this problem, the v3 API introduces :func:`iio.v3.imiter
<imageio.core.v3_api.imiter>`, a generator yielding ndimages in the order in
which they appear in the file::

    import imageio as iio

    for frame in iio.v3.imiter("imageio:cockatoo.mp4"):
        pass # do something with the current frame

Just like imread, imiter accepts additional `kwargs` to overwrite any defaults used by ImageIO.

Low-Level Access
^^^^^^^^^^^^^^^^

Sometimes we may wish for low-level access to a plugin or file, for example, because

- we wish to have fine-grained control over when it is opened/closed.
- we need to perform multiple IO operations and don't want to open the file multiple times.
- a plugin/backend offers unique features not otherwise exposed by the v3 API.

For these cases, the v3 API offers :func:`iio.v3.imopen
<imageio.core.imopen.imopen>`. It provides a context managed that initializes
the plugin and openes the file for reading (``"r"``) or writing (``"w"``),
similar to the built-in ``open``::

    import imageio as iio

    with iio.v3.imopen("imageio:chelsea.png", "r") as iio_plugin:
        img = iio_plugin.read()
        metadata = iio_plugin.get_meta()
        # iio_plugin.plugin_specific_function()

Similar to above, you can pass the ``plugin`` `kwarg` to imopen to control the
plugin that is being used. The returned plugin instance (`iio_plugin`) exposes
the v3 plugin API (TODO: link to documentation), and can be used for low-level
access.
