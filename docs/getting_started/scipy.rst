Transitioning from Scipy's imread
=================================

Scipy has `depreciated <https://scipy.github.io/devdocs/release.1.0.0.html#backwards-incompatible-changes>`_
their image I/O functionality.

This document is intended to help people coming from
`Scipy <https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imread.html>`_
to adapt to ImageIO's :func:`imread <imageio.imread>` function.
We recommend reading the :doc:`user api <../reference/userapi>` and checking out some
:doc:`examples <../examples>` to get a feel of ImageIO.

ImageIO makes use of a variety of backends to support reading images (and
volumes/movies) from many different formats. One of these backends is Pillow,
which is the same library as used by Scipy's ``imread``. This means that all
image formats that were supported by scipy are supported by ImageIO. At the same
time, Pillow is not the only backend of ImageIO, and those other backends give
you give you access to additional formats. To manage this, ImageIO automatically
selects the right backend to use based on the source to read (which you can of
course control manually, should you wish to do so).

In short terms: In most places where you used Scipy's imread, ImageIO's imread
is a drop-in replacement and ImageIO provides the same functionality as Scipy in
these cases. In some cases, you will need to update the keyword arguments used.

    * Instead of ``mode``, use the ``pilmode`` keyword argument.
    * Instead of ``flatten``, use the ``as_gray`` keyword argument.
    * The documentation for the above arguments is not on :func:`imread
      <ImageIO.imread>`, but on the docs of the individual plugins, e.g.
      :mod:`Pillow <imageio.plugins.pillow_legacy>`.
    * ImageIO's functions all return numpy arrays, albeit as a subclass (so that
      meta data can be attached).
