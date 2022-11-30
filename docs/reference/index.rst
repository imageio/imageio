API Reference
=============

ImageIO's API follows the usual idea of choosing sensible defaults for the
average user, but giving you fine grained control where you need it. As
such the API is split into two parts: The Core API, which covers standard
use-cases, and a plugin/backend specific API, which allows you to take full
advantage of a backend and its unique features.

Core APIs
^^^^^^^^^

The core API is ImageIOs public frontend. It provides convenient (and powerful)
access to the growing number of individual plugins on top of which ImageIO is
built. Currently the following APIs exist:

.. toctree::
    :maxdepth: 1

    Core API v3 (narrative docs) <core_v3>
    Core API v2 (narrative docs) <userapi>

.. rubric:: Core API v3
.. note::
    To use this API import it using::

        import imageio.v3 as iio
.. note::
    Check the narrative documentation to build intuition for how to use this API.
    You can find them here: :doc:`narrative v3 API docs <core_v3>`.

.. autosummary::

    imageio.v3.imread
    imageio.v3.imiter
    imageio.v3.improps
    imageio.v3.immeta
    imageio.v3.imwrite
    imageio.v3.imopen

.. rubric:: Core API v2
.. warning::
    This API exists for backwards compatibility. It is a wrapper around calls to
    the v3 API and new code should use the v3 API directly.

.. note::
    To use this API import it using::

        import imageio.v2 as iio

.. note::
    Check the narrative documentation to build intuition for how to use this API.
    You can find them here: :doc:`narrative v2 API docs <userapi>`.

.. autosummary::

    imageio.v2.imread
    imageio.v2.mimread
    imageio.v2.volread
    imageio.v2.mvolread
    imageio.v2.imwrite
    imageio.v2.mimwrite
    imageio.v2.volwrite
    imageio.v2.mvolwrite
    imageio.v2.get_reader
    imageio.v2.get_writer


.. _supported_backends:

Plugins & Backend Libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes, you need to do more than just "load an image, done". Sometimes you
need to use a very specific feature of a very specific backend. ImageIO allows
you to do so by allowing its plugins to extend the core API. Typically this is
done in the form of additional keyword arguments (``kwarg``) or plugin-specific
methods. Below you can find a list of available plugins and which arguments they
support.

.. autosummary::
    :toctree: ../_autosummary/
    :template: plugin.rst

    imageio.plugins.bsdf
    imageio.plugins.dicom
    imageio.plugins.feisem
    imageio.plugins.ffmpeg
    imageio.plugins.fits
    imageio.plugins.freeimage
    imageio.plugins.gdal
    imageio.plugins.lytro
    imageio.plugins.npz
    imageio.plugins.opencv
    imageio.plugins.pillow
    imageio.plugins.pillow_legacy
    imageio.plugins.pyav
    imageio.plugins.simpleitk
    imageio.plugins.spe
    imageio.plugins.swf
    imageio.plugins.tifffile
    imageio.plugins.tifffile_v3
