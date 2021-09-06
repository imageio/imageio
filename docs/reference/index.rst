API Reference
=============

ImageIO's API follows the usual idea of choosing sensible defaults for the average use, but giving
you fine grained control 

Core API (Basic Usage)
^^^^^^^^^^^^^^^^^^^^^^

The API documented in this section is shared by all plugins

.. toctree::
    :maxdepth: 1

    Core API v2.9 <userapi>


Plugins & Backend Libraries (Advanced Usage)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes, you need to do more than just "load an image, done". Sometimes you
need to use a very specific feature of a very specific backend. ImageIOs allows
you to do so by allowing its plugins to extend the core API. Typically this is
done in the form of additional keyword arguments (``kwarg``). Below you can find
a list of available plugins and which arguments they support.

.. autosummary::
    :toctree: _backends/
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