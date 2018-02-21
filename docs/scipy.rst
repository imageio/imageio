Transitioning from Scipy's imread
=================================

Scipy is `deprecating <https://scipy.github.io/devdocs/release.1.0.0.html#backwards-incompatible-changes>`_
their image I/O functionality.

This document is intended to help people coming from
`Scipy <https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imread.html>`_
to adapt to Imageio's :func:`imread <imageio.imread>` function.
We recommend reading the :doc:`user api <userapi>` and checkout some
:doc:`examples <examples>` to get a feel of imageio.

Imageio makes use of variety of plugins to support reading images (and volumes/movies)
from many different formats. Fortunately, Pillow is the main plugin for common images,
which is the same library as used by  Scipy's ``imread``. Note that Imageio
automatically selects a plugin based on the image to read (unless a format is
explicitly specified), but uses Pillow where possible. 

In short terms: For images previously read by Scipy's imread, imageio should
generally use Pillow as well, and imageio provides the same functionality as Scipy
in these cases. But keep in mind:

    * Instead of ``mode``, use the ``pilmode`` keyword argument.
    * Instead of ``flatten``, use the ``as_gray`` keyword argument.
    * The documentation for the above arguments is not on :func:`imread <imageio.imread>`,
      but on the docs of the individual formats, e.g. :doc:`PNG <format_png-pil>`.
    * Imageio's functions all return numpy arrays, albeit as a subclass (so that
      meta data can be attached). This subclass is called ``Image``.
