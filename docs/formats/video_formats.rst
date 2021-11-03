Video Formats
-------------

Below you can find an alphabetically sorted list of the video
extensions/formats that ImageIO is aware of. If an extension is listed
here, it is supported. If an extension is not listed here, it may still be
supported if one of the backends supports the extension/format. If you encounter
the latter, please `create a new issue
<https://github.com/imageio/imageio/issues>`_ so that we can keep below list up
to date and add support for any missing formats.

Each entry in the list below follows the following format::

    <extension> (<format name>): <plugin> <plugin> ...

where ``<plugin>`` is the name of a plugin that can handle the format. If you
wish to use a specific plugin to load a format, you would use the name as
specified. For example, if you have a MOV file that you wish to open with FFMPEG
and the ``<plugin>`` is called ``FFMPEG`` you would call::

    iio.imread("image.mov", format="FFMPEG")

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