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

    <extension> (<format name>): <plugin> <plugin> ...

where ``<plugin>`` is the name of a plugin that can handle the format. If you
wish to use a specific plugin to load a format, you would use the name as
specified. For example, if you have a PNG file that you wish to open with pillow
and the ``<plugin>`` is called ``PNG-PIL`` you would call::

    iio.imread("image.png", format="PNG-PIL")

.. rubric:: Format List

.. note::
    To complete this list we are looking for the following information:

        - The full name of each extension
        - A link to the spec, wikipedia page, or format homepage
        - extensions/formats supported by ImageIO but not listed here

    If you come across any of the above, please `share this information
    <https://github.com/imageio/imageio/issues>`_ so that we can add it below.

{% for format in formats %}
{% if format.external_link %}
- **{{ format.extension }}** (`{{ format.name }} <{{format.external_link}}>`_): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{% elif format.name %}
- **{{ format.extension }}** ({{ format.name }}): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{% else %}
- **{{ format.extension }}**: {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{%endif%}
{% endfor %}
