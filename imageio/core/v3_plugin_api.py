from . import Request
from numpy.typing import ArrayLike
import numpy as np
from typing import Optional, Dict, Any, Tuple, Union, List


class ImageDescriptor:
    def __init__(self, shape: Tuple[int, ...], dtype: np.dtype) -> None:
        # TODO: replace with dataclass once py3.6 is dropped.
        self.shape: shape
        self.dtype: dtype


class PluginV3:
    """A ImageIO Plugin.

    This is an abstract plugin that documents the v3 plugin API interface. A
    plugin is an adapter/wrapper around a backend that converts a request from
    iio.core (e.g., read an image from file) into a sequence of instructions for
    the backend that fullfill the request.

    Plugin authors may choose to subclass this class when implementing a new
    plugin, but aren't obliged to do so. As long as the plugin class implements
    the interface (methods) described below the ImageIO core will treat it just
    like any other plugin.


    Parameters
    ----------
    request : iio.Request
        A request object that represents the users intent. It provides a
        standard interface to access various the various ImageResources and
        serves them to the plugin as a file object (or file). Check the docs for
        details.
    **kwargs : Any
        Additional configuration arguments for the plugin or backend. Usually
        these match with configuration arguments available on the backend and
        are forwarded to it.


    Raises
    ------
    InitializationError
        During ``__init__`` the plugin tests if it can fulfill the request. If
        it can't, e.g., because the request points to a file in the wrong
        format, then it should raise an ``InitializationError`` and provide a
        reason for failure. This reason may be reported to the user.
    ImportError
        Plugins will be imported dynamically when listed in
        ``iio.config.known_plugins`` to fullfill requests. This way, users only
        have to load plugins/backends they actually use. If this plugin's backend
        is not installed, it should raise an ``ImportError`` either during
        module import or during class construction.

    Notes
    -----
    Upon successful construction the plugin takes ownership of the provided
    request. This means that it is the plugin's responsibility to call
    request.finish() to close the resource when it is no longer needed.

    Plugins _must_ implement a context manager that closes and cleans any
    resources held by the plugin upon exit.

    """

    def __init__(self, request: Request) -> None:
        """Initialize a new Plugin Instance.

        See Plugin's docstring for detailed documentation.

        Notes
        -----
        The implementation here stores the request as a local variable that is
        exposed using a @property below. If you inherit from PluginV3, remember
        to call ``super().__init__(request)``.

        """

        self._request = request

    def read(self, *, index: int = None) -> np.ndarray:
        """Read a ndimage.

        The ``read`` method loads a (single) ndimage, located at ``index`` from
        the requested ImageResource.

        It is at the plugin's descretion to decide (and document) what
        constitutes a single ndimage. A sensible way to make this decision is to
        choose based on the ImageResource's format and on what users will expect
        from such a format. For example, a sensible choice for a TIFF file
        produced by an ImageJ hyperstack is to read it as a volumetric ndimage
        (1 color dimension followed by 3 spatial dimensions). On the other hand,
        a sensible choice for a MP4 file produced by Davinci Resolve is to treat
        each frame as a ndimage (2 spatial dimensions followed by 1 color
        dimension).

        The value ``index=None`` is special. It requests the plugin to load all
        ndimages in the file and stack them along a new first axis. For example,
        if a MP4 file is read with ``index=None`` and the plugin identifies
        single frames as ndimages, then the plugin should read all frames and
        stack them into a new ndimage which now contains a time axis as its
        first axis. If a PNG file (single image format) is read with
        ``index=None`` the plugin does a very similar thing: It loads all
        ndimages in the file (here it's just one) and stacks them along a new
        first axis, effectively prepending an axis with size 1 to the image. If
        a plugin does not wish to support ``index=None`` it should set a more
        sensible default and raise a ``ValueError`` when requested to read using
        ``index=None``.

        Parameters
        ----------
        index : int
            The index of the ndimage to read. If the index is out of bounds a
            ``ValueError`` is raised. If ``None``, the plugin reads all ndimages
            in the file and stacks them along a new, prepended, batch dimension.
            If stacking is impossible, e.g., due to shape missmatch, an
            exception will be raised.
        **kwargs : Any
            The read method may accept any number of plugin-specific keyword
            arguments to further customize the read behavior. Usually these
            match the arguments available on the backend and are forwarded to
            it.

        Returns
        -------
        ndimage : np.ndarray
            A ndimage containing decoded pixel data (sometimes called bitmap).

        Notes
        -----
        Plugins may choose a different (more sensible) default value for ``index``.

        The ImageResource from which the plugin should read is managed by the
        provided request object. Directly accessing the managed ImageResource is
        _not_ permitted. Instead, you can get FileLike access to the
        ImageResource via request.get_file().

        If the backend doesn't support reading from FileLike objects, you can
        request a temporary file to pass to the backend via
        ``request.get_local_filename()``. This is, however, not very performant
        (involves copying the Request's content into a temporary file), so you
        should avoid doing this whenever possible. Consider it a fallback method
        in case all else fails.

        """
        raise NotImplementedError()

    def write(self, ndimage: Union[ArrayLike, List[ArrayLike]]) -> Optional[bytes]:
        """Write a ndimage to a ImageResource.

        The ``write`` method encodes the given ndimage into the format handled
        by the backend and writes it to the ImageResource. It overwrites
        any content that may have been previously stored in the file.

        If the backend supports only a single format then it must check if
        the ImageResource matches that format and raise an exception if not.
        Typically, this should be done during initialization in the form of a
        ``InitializationError``.

        If the backend supports more than one format it must determine the
        requested/desired format. Usually this can be done by inspecting the
        ImageResource (e.g., by checking ``request.extension``), or by providing
        a mechanism to explicitly set the format (perhaps with a - sensible -
        default value). If the plugin can not determine the desired format, it
        _must not_ write to the ImageResource, but raise an exception instead.

        If the backend supports at least one format that can hold multiple
        ndimages it should be capable of handling ndimage batches and lists of
        ndimages. If the ``ndimage`` input is as a list of ndimages, the plugin
        should expect that the ndimages are not stackable, i.e., that they have
        different shapes and/or dimensions. Otherwise, the ``ndimage`` may be a
        batch of multiple ndimages stacked along the first axis of the array.
        The plugin must be able to discover this, either automatically or via
        additional `kwargs`. If there is ambiguity in the process, the plugin
        must clearly document what happens in such cases and, if possible,
        describe how to resolve this ambiguity.

        Parameters
        ----------
        ndimage : ArrayLike
            The ndimage to encode and write to the current ImageResource.
        **kwargs : Any
            The write method may accept any number of plugin-specific keyword
            arguments to customize the writing behavior. Usually these match the
            arguments available on the backend and are forwarded to it.

        Returns
        -------
        encoded_image : bytes or None
            If the chosen ImageResource is the special target ``"<bytes>"`` then
            write should return a byte string containing the encoded image data.
            Otherwise, it returns None.

        Notes
        -----
        The ImageResource to which the plugin should write to is managed by the
        provided request object. Directly accessing the managed ImageResource is
        _not_ permitted. Instead, you can get FileLike access to the
        ImageResource via request.get_file().

        If the backend doesn't support writing to FileLike objects, you can
        request a temporary file to pass to the backend via
        ``request.get_local_filename()``. This is, however, not very performant
        (involves copying the Request's content from a temporary file), so you
        should avoid doing this whenever possible. Consider it a fallback method
        in case all else fails.

        """
        raise NotImplementedError()

    def iter(self) -> np.ndarray:
        """Iterate the ImageResource.

        This method returns a generator that yields ndimages in the order in which
        they appear in the file. This is roughly equivalent to::

            idx = 0
            while True:
                try:
                    yield self.read(index=idx)
                except ValueError:
                    break

        It works very similar to ``read``, and you can consult the documentation
        of that method for additional information on desired behavior.

        Parameters
        ----------
        **kwargs : Any
            The iter method may accept any number of plugin-specific keyword
            arguments to further customize the reading/iteration behavior.
            Usually these match the arguments available on the backend and are
            forwarded to it.

        Yields
        ------
        ndimage : np.ndarray
            A ndimage containing decoded pixel data (sometimes called bitmap).

        See Also
        --------
        PluginV3.read

        """
        raise NotImplementedError()

    def descriptor(self, index: int = None) -> ImageDescriptor:
        """Standardized ndimage metadata.

        Parameters
        ----------
        index : int
            The index of the ndimage for which to return the descriptor. If the
            index is out of bounds a ``ValueError`` is raised. If ``None``,
            return the descriptor for the ndimage stack. If this is impossible,
            e.g., due to shape missmatch, an exception will be raised.

        Returns
        -------
        descriptor : ImageDescriptor
            A dataclass filled with standardized image metadata.

        """
        raise NotImplementedError()

    def metadata(
        self, index: int = None, exclude_applied: bool = True
    ) -> Dict[str, Any]:
        """Format-Specific ndimage metadata.

        The method reads metadata stored in the ImageResource and returns it as
        a python dict. The plugin is free to choose which name to give a piece
        of metadata; however, if possible, it should match the name given by the
        format. On top, there is no requirement regarding which fields should be
        present, with exception of ``exclude_applied``.

        If the plugin does return metadata items, it must check the value of
        ``exclude_applied`` before returning them. If ``exclude applied`` is
        True, then any metadata item that would be applied to an ndimage
        returned by ``read`` (or ``iter``) must not be returned. This is done to
        avoid confusion; for example, if an ImageResource defines the ExIF
        rotation tag, and the plugin applies the rotation to the data before
        returning it, then ``exclude_applied`` prevents confusion on whether the
        tag was already applied or not.

        The _kwarg_ ``index`` behaves similar to its counterpart in ``read``
        with one exception: If the ``index`` is None, then global metadata is
        returned instead of returning a combination of all metadata items. If
        there is no global metadata, the Plugin should return an empty dict or
        raise an exception. Just like before, the plugin may choose a more
        sensible default value for ``index``.

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
        raise NotImplementedError()

    def close(self) -> None:
        """Close the ImageResource.

        This method allows a plugin to behave similar to the python build-in ``open``::

            image_file = my_plugin(Request, "r")
            ...
            image_file.close()

        It is used by context manager and deconstructor below to avoid leaking
        ImageResources. If the plugin has no other cleanup to do it doesn#t have
        to overwrite this method itself and can rely on the implementation
        below.

        Notes
        -----

        """

        self.request.finish()

    @property
    def request(self) -> Request:
        return self._request

    def __enter__(self) -> "PluginV3":
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
