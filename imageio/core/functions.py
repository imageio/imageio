# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

"""
These functions represent imageio's main interface for the user. They
provide a common API to read and write image data for a large
variety of formats. All read and write functions accept keyword
arguments, which are passed on to the format that does the actual work.
To see what keyword arguments are supported by a specific format, use
the :func:`.help` function.

Functions for reading:

  * :func:`.imread` - read an image from the specified uri
  * :func:`.mimread` - read a series of images from the specified uri
  * :func:`.volread` - read a volume from the specified uri
  * :func:`.mvolread` - read a series of volumes from the specified uri

Functions for saving:

  * :func:`.imwrite` - write an image to the specified uri
  * :func:`.mimwrite` - write a series of images to the specified uri
  * :func:`.volwrite` - write a volume to the specified uri
  * :func:`.mvolwrite` - write a series of volumes to the specified uri

More control:

For a larger degree of control, imageio provides functions
:func:`.get_reader` and :func:`.get_writer`. They respectively return an
:class:`.Reader` and an :class:`.Writer` object, which can
be used to read/write data and meta data in a more controlled manner.
This also allows specific scientific formats to be exposed in a way
that best suits that file-format.

----

All read-functions return images as numpy arrays, and have a ``meta``
attribute; the meta-data dictionary can be accessed with ``im.meta``.
To make this work, imageio actually makes use of a subclass of
``np.ndarray``. If needed, the image can be converted to a plain numpy
array using ``np.asarray(im)``.

----

Supported resource URI's:

All functions described here accept a URI to describe the resource to
read from or write to. These can be a wide range of things. (Imageio
takes care of handling the URI so that plugins can access the data in
an easy way.)

For reading and writing:

* a normal filename, e.g. ``'c:\\foo\\bar.png'``
* a file in a zipfile, e.g. ``'c:\\foo\\bar.zip\\eggs.png'``
* a file object with a ``read()`` / ``write()`` method.

For reading:

* an http/ftp address, e.g. ``'http://example.com/foo.png'``
* the raw bytes of an image file
* ``get_reader("<video0>")`` to grab images from a (web) camera.
* ``imread("<screen>")`` to grab a screenshot (on Windows or OS X).
* ``imread("<clipboard>")`` to grab an image from the clipboard (on Windows).

For writing one can also use ``'<bytes>'`` or ``imageio.RETURN_BYTES`` to
make a write function return the bytes instead of writing to a file.

Note that reading from HTTP and zipfiles works for many formats including
png and jpeg, but may not work for all formats (some plugins "seek" the
file object, which HTTP/zip streams do not support). In such a case one
can download/extract the file first. For HTTP one can use something
like ``imageio.imread(imageio.core.urlopen(url).read(), '.gif')``.

"""

from numbers import Number
import re

import numpy as np

from .. import formats
from .imopen import imopen


MEMTEST_DEFAULT_MIM = "256MB"
MEMTEST_DEFAULT_MVOL = "1GB"


mem_re = re.compile(r"^(\d+\.?\d*)\s*([kKMGTPEZY]?i?)B?$")
sizes = {"": 1, None: 1}
for i, si in enumerate([""] + list("kMGTPEZY")):
    sizes[si] = 1000 ** i
    if si:
        sizes[si.upper() + "i"] = 1024 ** i


def to_nbytes(arg, default=None):
    if not arg:
        return None

    if arg is True:
        return default

    if isinstance(arg, Number):
        return arg

    match = mem_re.match(arg)
    if match is None:
        raise ValueError(
            "Memory size could not be parsed "
            "(is your capitalisation correct?): {}".format(arg)
        )

    num, unit = match.groups()

    try:
        return float(num) * sizes[unit]
    except KeyError:
        raise ValueError(
            "Memory size unit not recognised "
            "(is your capitalisation correct?): {}".format(unit)
        )


def help(name=None):
    """help(name=None)

    Print the documentation of the format specified by name, or a list
    of supported formats if name is omitted.

    Parameters
    ----------
    name : str
        Can be the name of a format, a filename extension, or a full
        filename. See also the :doc:`formats page <formats>`.
    """
    if not name:
        print(formats)
    else:
        print(formats[name])


# Base functions that return a reader/writer


def get_reader(uri, format=None, mode="?", **kwargs):
    """get_reader(uri, format=None, mode='?', **kwargs)

    Returns a :class:`.Reader` object which can be used to read data
    and meta data from the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    mode : {'i', 'I', 'v', 'V', '?'}
        Used to give the reader a hint on what the user expects (default "?"):
        "i" for an image, "I" for multiple images, "v" for a volume,
        "V" for multiple volumes, "?" for don't care.
    kwargs : ...
        Further keyword arguments are passed to the reader. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    image_file = imopen()(uri, "r", format=format)
    return image_file.legacy_get_reader(iio_mode=mode, **kwargs)


def get_writer(uri, format=None, mode="?", **kwargs):
    """get_writer(uri, format=None, mode='?', **kwargs)

    Returns a :class:`.Writer` object which can be used to write data
    and meta data to the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, file}
        The resource to write the image to, e.g. a filename, pathlib.Path
        or file object, see the docs for more info.
    format : str
        The format to use to write the file. By default imageio selects
        the appropriate for you based on the filename.
    mode : {'i', 'I', 'v', 'V', '?'}
        Used to give the writer a hint on what the user expects (default '?'):
        "i" for an image, "I" for multiple images, "v" for a volume,
        "V" for multiple volumes, "?" for don't care.
    kwargs : ...
        Further keyword arguments are passed to the writer. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    image_file = imopen()(uri, "w", format=format)
    return image_file.legacy_get_writer(iio_mode=mode, **kwargs)


# Images


def imread(uri, format=None, **kwargs):
    """imread(uri, format=None, **kwargs)

    Reads an image from the specified file. Returns a numpy array, which
    comes with a dict of meta data at its 'meta' attribute.

    Note that the image data is returned as-is, and may not always have
    a dtype of uint8 (and thus may differ from what e.g. PIL returns).

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the reader. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    if "mode" in kwargs:
        raise TypeError(
            'Invalid keyword argument "mode", ' 'perhaps you mean "pilmode"?'
        )

    with imopen()(uri, "r", format=format) as file:
        return file.read(index=0, iio_mode="i", **kwargs)


def imwrite(uri, im, format=None, **kwargs):
    """imwrite(uri, im, format=None, **kwargs)

    Write an image to the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, file}
        The resource to write the image to, e.g. a filename, pathlib.Path
        or file object, see the docs for more info.
    im : numpy.ndarray
        The image data. Must be NxM, NxMx3 or NxMx4.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the writer. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    # Test image
    imt = type(im)
    im = np.asanyarray(im)
    if not np.issubdtype(im.dtype, np.number):
        raise ValueError("Image is not numeric, but {}.".format(imt.__name__))
    elif im.ndim == 2:
        pass
    elif im.ndim == 3 and im.shape[2] in [1, 3, 4]:
        pass
    else:
        raise ValueError("Image must be 2D (grayscale, RGB, or RGBA).")

    with imopen()(uri, "w", format=format) as file:
        return file.write(im, iio_mode="i", **kwargs)


# Multiple images


def mimread(uri, format=None, memtest=MEMTEST_DEFAULT_MIM, **kwargs):
    """mimread(uri, format=None, memtest="256MB", **kwargs)

    Reads multiple images from the specified file. Returns a list of
    numpy arrays, each with a dict of meta data at its 'meta' attribute.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the images from, e.g. a filename,pathlib.Path,
        http address or file object, see the docs for more info.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    memtest : {bool, int, float, str}
        If truthy, this function will raise an error if the resulting
        list of images consumes greater than the amount of memory specified.
        This is to protect the system from using so much memory that it needs
        to resort to swapping, and thereby stall the computer. E.g.
        ``mimread('hunger_games.avi')``.

        If the argument is a number, that will be used as the threshold number
        of bytes.

        If the argument is a string, it will be interpreted as a number of bytes with
        SI/IEC prefixed units (e.g. '1kB', '250MiB', '80.3YB').

        - Units are case sensitive
        - k, M etc. represent a 1000-fold change, where Ki, Mi etc. represent 1024-fold
        - The "B" is optional, but if present, must be capitalised

        If the argument is True, the default will be used, for compatibility reasons.

        Default: '256MB'
    kwargs : ...
        Further keyword arguments are passed to the reader. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    # used for mimread and mvolread
    nbyte_limit = to_nbytes(memtest, MEMTEST_DEFAULT_MIM)

    images = list()
    nbytes = 0

    with imopen()(uri, "r", format=format) as file:
        for image in file.iter(iio_mode="I", **kwargs):
            images.append(image)
            nbytes += image.nbytes
            if nbytes > nbyte_limit:
                raise RuntimeError(
                    "imageio.mimread() has read over {}B of "
                    "image data.\nStopped to avoid memory problems."
                    " Use imageio.get_reader(), increase threshold, or memtest=False".format(
                        int(nbyte_limit)
                    )
                )

    return images


def mimwrite(uri, ims, format=None, **kwargs):
    """mimwrite(uri, ims, format=None, **kwargs)

    Write multiple images to the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, file}
        The resource to write the images to, e.g. a filename, pathlib.Path
        or file object, see the docs for more info.
    ims : sequence of numpy arrays
        The image data. Each array must be NxM, NxMx3 or NxMx4.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the writer. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    with imopen()(uri, "w", format=format) as file:
        return file.write(ims, iio_mode="I", **kwargs)


# Volumes


def volread(uri, format=None, **kwargs):
    """volread(uri, format=None, **kwargs)

    Reads a volume from the specified file. Returns a numpy array, which
    comes with a dict of meta data at its 'meta' attribute.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the volume from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the reader. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    with imopen()(uri, "r", format=format) as file:
        return file.read(index=0, iio_mode="v", **kwargs)


def volwrite(uri, im, format=None, **kwargs):
    """volwrite(uri, vol, format=None, **kwargs)

    Write a volume to the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, file}
        The resource to write the image to, e.g. a filename, pathlib.Path
        or file object, see the docs for more info.
    vol : numpy.ndarray
        The image data. Must be NxMxL (or NxMxLxK if each voxel is a tuple).
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the writer. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    # Test image
    imt = type(im)
    im = np.asanyarray(im)
    if not np.issubdtype(im.dtype, np.number):
        raise ValueError("Image is not numeric, but {}.".format(imt.__name__))
    elif im.ndim == 3:
        pass
    elif im.ndim == 4 and im.shape[3] < 32:  # How large can a tuple be?
        pass
    else:
        raise ValueError("Image must be 3D, or 4D if each voxel is a tuple.")

    with imopen()(uri, "w", format=format) as file:
        return file.write(im, iio_mode="v", **kwargs)


# Multiple volumes


def mvolread(uri, format=None, memtest=MEMTEST_DEFAULT_MVOL, **kwargs):
    """mvolread(uri, format=None, memtest='1GB', **kwargs)

    Reads multiple volumes from the specified file. Returns a list of
    numpy arrays, each with a dict of meta data at its 'meta' attribute.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the volumes from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    memtest : {bool, int, float, str}
        If truthy, this function will raise an error if the resulting
        list of images consumes greater than the amount of memory specified.
        This is to protect the system from using so much memory that it needs
        to resort to swapping, and thereby stall the computer. E.g.
        ``mimread('hunger_games.avi')``.

        If the argument is a number, that will be used as the threshold number
        of bytes.

        If the argument is a string, it will be interpreted as a number of bytes with
        SI/IEC prefixed units (e.g. '1kB', '250MiB', '80.3YB').

        - Units are case sensitive
        - k, M etc. represent a 1000-fold change, where Ki, Mi etc. represent 1024-fold
        - The "B" is optional, but if present, must be capitalised

        If the argument is True, the default will be used, for compatibility reasons.

        Default: '1GB'
    kwargs : ...
        Further keyword arguments are passed to the reader. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    # used for mimread and mvolread
    nbyte_limit = to_nbytes(memtest, MEMTEST_DEFAULT_MVOL)

    images = list()
    nbytes = 0
    with imopen()(uri, "r", format=format) as file:
        for image in file.iter(iio_mode="V", **kwargs):
            images.append(image)
            nbytes += image.nbytes
            if nbytes > nbyte_limit:
                raise RuntimeError(
                    "imageio.mimread() has read over {}B of "
                    "image data.\nStopped to avoid memory problems."
                    " Use imageio.get_reader(), increase threshold, or memtest=False".format(
                        int(nbyte_limit)
                    )
                )

    return images


def mvolwrite(uri, ims, format=None, **kwargs):
    """mvolwrite(uri, vols, format=None, **kwargs)

    Write multiple volumes to the specified file.

    Parameters
    ----------
    uri : {str, pathlib.Path, file}
        The resource to write the volumes to, e.g. a filename, pathlib.Path
        or file object, see the docs for more info.
    ims : sequence of numpy arrays
        The image data. Each array must be NxMxL (or NxMxLxK if each
        voxel is a tuple).
    format : str
        The format to use to read the file. By default imageio selects
        the appropriate for you based on the filename and its contents.
    kwargs : ...
        Further keyword arguments are passed to the writer. See :func:`.help`
        to see what arguments are available for a particular format.
    """

    with imopen()(uri, "w", format=format) as file:
        return file.write(ims, iio_mode="V", **kwargs)
