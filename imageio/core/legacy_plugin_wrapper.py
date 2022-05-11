import numpy as np
from pathlib import Path

from .request import IOMode, InitializationError
from .v3_plugin_api import PluginV3, ImageProperties


def _legacy_default_index(format):
    if format._name == "FFMPEG":
        index = Ellipsis
    elif format._name == "GIF-PIL":
        index = Ellipsis
    else:
        index = 0

    return index


class LegacyPlugin(PluginV3):
    """A plugin to  make old (v2.9) plugins compatible with v3.0

    .. depreciated:: 2.9
        `legacy_get_reader` will be removed in a future version of imageio.
        `legacy_get_writer` will be removed in a future version of imageio.

    This plugin is a wrapper around the old FormatManager class and exposes
    all the old plugins via the new API. On top of this it has
    ``legacy_get_reader`` and ``legacy_get_writer`` methods to allow using
    it with the v2.9 API.

    Methods
    -------
    read(index=None, **kwargs)
        Read the image at position ``index``.
    write(image, **kwargs)
        Write image to the URI.
    iter(**kwargs)
        Iteratively yield images from the given URI.
    get_meta(index=None)
        Return the metadata for the image at position ``index``.
    legacy_get_reader(**kwargs)
        Returns the v2.9 image reader. (depreciated)
    legacy_get_writer(**kwargs)
        Returns the v2.9 image writer. (depreciated)

    Examples
    --------

    >>> import imageio.v3 as iio
    >>> with iio.imopen("/path/to/image.tiff", "r", legacy_mode=True) as file:
    >>>     reader = file.legacy_get_reader()  # depreciated
    >>>     for im in file.iter():
    >>>         print(im.shape)

    """

    def __init__(self, request, legacy_plugin):
        """Instantiate a new Legacy Plugin

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.
        legacy_plugin : Format
            The (legacy) format to use to interface with the URI.

        """
        self._request = request
        self._format = legacy_plugin

        source = (
            "<bytes>"
            if isinstance(self._request.raw_uri, bytes)
            else self._request.raw_uri
        )
        if self._request.mode.io_mode == IOMode.read:
            if not self._format.can_read(request):
                raise InitializationError(
                    f"`{self._format.name}`" f" can not read `{source}`."
                )
        else:
            if not self._format.can_write(request):
                raise InitializationError(
                    f"`{self._format.name}`" f" can not write to `{source}`."
                )

    def legacy_get_reader(self, **kwargs):
        """legacy_get_reader(**kwargs)

        a utility method to provide support vor the V2.9 API

        Parameters
        ----------
        kwargs : ...
            Further keyword arguments are passed to the reader. See :func:`.help`
            to see what arguments are available for a particular format.
        """

        # Note: this will break thread-safety
        self._request._kwargs = kwargs

        # safeguard for DICOM plugin reading from folders
        try:
            assert Path(self._request.filename).is_dir()
        except OSError:
            pass  # not a valid path on this OS
        except AssertionError:
            pass  # not a folder
        else:
            return self._format.get_reader(self._request)

        self._request.get_file().seek(0)
        return self._format.get_reader(self._request)

    def read(self, *, index=None, **kwargs):
        """
        Parses the given URI and creates a ndarray from it.

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the index-th
            image. If None, stack all images into an ndimage along the
            0-th dimension (equivalent to np.stack(imgs, axis=0)).
        kwargs : ...
            Further keyword arguments are passed to the reader. See
            :func:`.help` to see what arguments are available for a particular
            format.

        Returns
        -------
        ndimage : np.ndarray
            A numpy array containing the decoded image data.

        """

        if index is None:
            index = _legacy_default_index(self._format)

        if index is Ellipsis:
            img = np.stack([im for im in self.iter(**kwargs)])
            return img

        reader = self.legacy_get_reader(**kwargs)
        return reader.get_data(index)

    def legacy_get_writer(self, **kwargs):
        """legacy_get_writer(**kwargs)

        Returns a :class:`.Writer` object which can be used to write data
        and meta data to the specified file.

        Parameters
        ----------
        kwargs : ...
            Further keyword arguments are passed to the writer. See :func:`.help`
            to see what arguments are available for a particular format.
        """

        # Note: this will break thread-safety
        self._request._kwargs = kwargs
        return self._format.get_writer(self._request)

    def write(self, ndimage, **kwargs):
        """
        Write an ndimage to the URI specified in path.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage or list of ndimages to write.
        kwargs : ...
            Further keyword arguments are passed to the writer. See
            :func:`.help` to see what arguments are available for a
            particular format.
        """
        with self.legacy_get_writer(**kwargs) as writer:
            if self._request.mode.image_mode in "iv":
                writer.append_data(ndimage)
            else:
                if len(ndimage) == 0:
                    raise RuntimeError("Zero images were written.")
                for written, ndimage in enumerate(ndimage):
                    # Test image
                    imt = type(ndimage)
                    ndimage = np.asanyarray(ndimage)
                    if not np.issubdtype(ndimage.dtype, np.number):
                        raise ValueError(
                            "Image is not numeric, but {}.".format(imt.__name__)
                        )
                    elif self._request.mode.image_mode == "I":
                        if ndimage.ndim == 2:
                            pass
                        elif ndimage.ndim == 3 and ndimage.shape[2] in [1, 3, 4]:
                            pass
                        else:
                            raise ValueError(
                                "Image must be 2D " "(grayscale, RGB, or RGBA)."
                            )
                    elif self._request.mode.image_mode == "V":
                        if ndimage.ndim == 3:
                            pass
                        elif ndimage.ndim == 4 and ndimage.shape[3] < 32:
                            pass
                        else:
                            raise ValueError(
                                "Image must be 3D," " or 4D if each voxel is a tuple."
                            )

                    # Add image
                    writer.append_data(ndimage)

        return writer.request.get_result()

    def iter(self, **kwargs):
        """Iterate over a list of ndimages given by the URI

        Parameters
        ----------
        kwargs : ...
            Further keyword arguments are passed to the reader. See
            :func:`.help` to see what arguments are available for a particular
            format.
        """

        reader = self.legacy_get_reader(**kwargs)
        for image in reader:
            yield image

    def properties(self, index=None):
        """Standardized ndimage metadata.

        Parameters
        ----------
        index : int
            The index of the ndimage for which to return properties. If the
            index is out of bounds a ``ValueError`` is raised. If ``None``,
            return the properties for the ndimage stack. If this is impossible,
            e.g., due to shape missmatch, an exception will be raised.

        Returns
        -------
        properties : ImageProperties
            A dataclass filled with standardized image metadata.

        """

        if index is None:
            index = _legacy_default_index(self._format)

        # for backwards compatibility ... actually reads pixel data :(
        image = self.read(index=index)

        return ImageProperties(
            shape=image.shape,
            dtype=image.dtype,
            is_batch=True if index is None else False,
        )

    def get_meta(self, *, index=None):
        """Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, behavior depends on
            the used api

            Legacy-style API: return metadata of the first element (index=0)
            New-style API: Behavior depends on the used Plugin.

        Returns
        -------
        metadata : dict
            A dictionary of metadata.

        """

        return self.metadata(index=index, exclude_applied=False)

    def metadata(self, index=None, exclude_applied: bool = True):
        """Format-Specific ndimage metadata.

        Parameters
        ----------
        index : int
            The index of the ndimage to read. If the index is out of bounds a
            ``ValueError`` is raised. If ``None``, global metadata is returned.
        exclude_applied : bool
            If True (default), do not report metadata fields that the plugin
            would apply/consume while reading the image.

        Returns
        -------
        metadata : dict
            A dictionary filled with format-specific metadata fields and their
            values.

        """

        if exclude_applied:
            raise ValueError(
                "Legacy plugins don't support excluding applied metadata fields."
            )

        if index is None:
            index = _legacy_default_index(self._format)

        return self.legacy_get_reader().get_meta_data(index=index)

    def __del__(self) -> None:
        pass
        # turns out we can't close the file here for LegacyPlugin
        # because it would break backwards compatibility
        # with legacy_get_writer and legacy_get_reader
        # self._request.finish()
