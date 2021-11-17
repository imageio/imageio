Supported Formats
=================

.. note::
    If you just want to know if a specific extension/format is supported
    you can search this page using ``Ctrl+F`` and then type the name of
    the extension or format.

ImageIO reads and writes images by deligating your request to one of many
backends. Example backends are pillow, ffmpeg, tifffile among others. Each
backend supports its own set of formats, which is how ImageIO manages to support
so many of them.

To help you navigate this format jungle, ImageIO provides various curated lists of formats
depending on your use-case

.. toctree::
    :maxdepth: 1

    formats_by_plugin
    video_formats


All Formats
-----------

Below you can find an alphabetically sorted list of *all*
extensions/file-formats that ImageIO is aware of. If an extension is listed
here, it is supported. If an extension is not listed here, it may still be
supported if one of the backends supports the extension/format. If you encoutner
the latter, please `create a new issue
<https://github.com/imageio/imageio/issues>`_ so that we can keep below list up
to date and add support for any missing formats.

Each entry in the list below follows the following format::

    extension (format_name): plugin1 plugin2 ...

where the plugins refer to imageio plugins that can handle the format. If you
wish to use a specific plugin to load a format, you would use the name as
specified here. For example, if you have a PNG file that you wish to open with pillow
you would call::

    iio.imread("image.png", format="PNG-PIL")

.. rubric:: Format List

.. note::
    To complete this list we are looking for each format's full name and a link
    to the spec. If you come across this information, please consider sharing it
    by `creating a new issue <https://github.com/imageio/imageio/issues>`_.

{% for format in formats %}
{% if format.external_link %}
- **{{ format.extension }}** (`{{ format.name }} <{{format.external_link}}>`_): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name].module_name}}>` {% endfor %}
{% elif format.name %}
- **{{ format.extension }}** ({{ format.name }}): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name].module_name}}>` {% endfor %}
{% else %}
- **{{ format.extension }}**: {% for name in format.priority %} :mod:`{{name}} <{{plugins[name].module_name}}>` {% endfor %}
{%endif%}
{% endfor %}
