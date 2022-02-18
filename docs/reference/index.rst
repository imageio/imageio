API Reference
=============

ImageIO's API follows the usual idea of choosing sensible defaults for the
average user, but giving you fine grained control where you need it. As
such the API is split into two parts: The Core API, which covers standard
use-cases, and a plugin/backend specific API, which allows you to take full
advantage of a backend and its unique features.

Core API
^^^^^^^^

The core API is ImageIOs public frontend. It provides convenient (and powerful)
access to the growing number of individual plugins on top of which ImageIO is
built.

.. toctree::
    :maxdepth: 1

    Core API v2 <userapi>
    Core API v3 <core_v3>

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
    imageio.plugins.pillow
    imageio.plugins.pillow_legacy
    imageio.plugins.simpleitk
    imageio.plugins.spe
    imageio.plugins.swf
    imageio.plugins.tifffile
