Transitioning from Scipy's imread
=================================

This document is intended to help people coming from
`Scipy <https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imread.html>`_
to adapt to Imageio's :func:`imread <imageio.imread>` function.
We recommend reading the :doc:`user api <userapi>` and checkout some
:doc:`examples <examples>` to get a feel of imageio.

Imageio makes use of variety of plugins to support reading images (and volumes/movies)
from many different formats. Fortunately, Pillow is the main plugin for common images,
which is the same library that Scipy's ``imread`` used. When the Pillow
plugin is used, imageio provides the same functionality as Scipy. But
keep in mind:

    * Instead of ``mode``, use the ``pilmode`` keyword argument.
    * Instead of ``flatten``, use the ``as_gray`` keyword argument.
    * The documentation for the above arguments is not on :func:`imread <imageio.imread>`,
      but on the docs of the individual formats, e.g. :doc:`PNG <format_png-pil>`.
