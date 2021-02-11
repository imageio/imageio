# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the the Pillow library.
"""

import numpy as np
from PIL import Image, UnidentifiedImageError, ImageSequence

from ..core.imopen import Plugin


class PillowPlugin(Plugin):
    def __init__(self, uri):
        """ Instantiate a new Legacy Plugin

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        """
        self._uri = uri
        self._image = None

    def close(self):
        if self._image:
            self._image.close()

    def read(self, *, index=None, mode=None, formats=None):
        """
        Parses the given URI and creates a ndarray from it.

        Parameters
        ----------
        index : {integer}
            If the URI contains a list of ndimages (multiple frames) return the
            index-th image/frame. If None, read all ndimages (frames) in the URI
            and attempt to stack them along a new 0-th axis (equivalent to
            np.stack(imgs, axis=0))
        mode : {str, None}
            Convert the image to the given mode before returning it. If None,
            the mode will be left unchanged. Possible modes can be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.

        Returns
        -------
        ndimage : ndarray
            A numpy array containing the loaded image data

        Notes
        -----
        If you open a GIF - or any other format using color pallets - you may
        wish to manually set the `mode` parameter. Otherwise, the numbers in
        the returned image will refer to the entries in the color pallet, which
        is discarded during conversion to ndarray.

        """
        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        if index is not None:
            # will raise IO error if index >= number of frames in image
            self._image.seek(index)

            if mode is not None:
                image = np.asarray(self._image.convert(mode))
            else:
                image = np.asarray(self._image)

            return image
        else:
            iterator = self.iter(mode=mode, formats=formats)
            return np.stack([im for im in iterator], axis=0)

    def iter(self, *, mode=None, formats=None):
        """
        Iterate over all ndimages/frames in the URI

        Parameters
        ----------
        mode : {str, None}
            Convert the image to the given mode before returning it. If None,
            the mode will be left unchanged. Possible modes can be found at:
            https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.
        """

        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        if mode is not None:
            for im in ImageSequence.Iterator(self._image):
                yield np.asarray(im.convert(mode))
        else:
            for im in ImageSequence.Iterator(self._image):
                yield np.asarray(im)

    def write(self, image, *, format=None, **kwargs):
        """
        Write an ndimage to the URI specified in path.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage or list of ndimages to write.
        format : {str, None}
            Optional format override.  If omitted, the format to use is
            determined from the filename extension. If a file object was used
            instead of a filename, this parameter must always be used.
        kwargs : ...
            Extra arguments to pass to the writer. If a writer doesn't
            recognise an option, it is silently ignored. The available options
            are described in the :doc:`image format documentation
            (https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
            for each writer.

        """

        pil_image = Image.fromarray(image)
        pil_image.save(self._uri, format=format, **kwargs)

    def get_meta(self, *, index=None, formats=None):
        """ Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, return the metadata
            for the last read ndimage/frame.
        formats : {iterable, None}
            A list or tuple of format strings to attempt to load the file in.
            This can be used to restrict the set of formats checked. Pass
            ``None`` to try all supported formats. You can print the set of
            available formats by running ``python -m PIL`` or using the
            ``PIL.features.pilinfo`` function.
        """
        if not self._image:
            self._image = Image.open(self._uri, formats=None)

        if index is not None:
            self._image.seek(index)

        return self._image.info

    @classmethod
    def can_open(cls, uri):
        """ Verify that plugin can read the given URI

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        Returns
        -------
        readable : bool
            True if the URI can be read by the plugin. False otherwise.

        """
        try:
            with Image.open(uri):
                # Check if it is generally possible to read the image.
                # This will not read any data and merely try to find a
                # compatible pillow plugin as per the pillow docs.
                pass
        except UnidentifiedImageError:
            return False

        return True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
