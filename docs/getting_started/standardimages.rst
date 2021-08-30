Imageio Standard Images
=======================

Imageio provides a number of standard images. These include classic
2D images, as well as animated and volumetric images. To the best
of our knowledge, all the listed images are in public domain.

The image names can be loaded by using a special URI,
e.g. ``imread('imageio:astronaut.png')``.
The images are automatically downloaded (and cached in your appdata
directory).

{% for name in ordered_keys %}
* `{{name}} <{{base_url+name}}>`_: {{images[name]}}
{% endfor %}