import numpy as np

from .format import FormatManager, MODENAMES
from .request import IOMode, Request, InitializationError


class imopen:
    """Open a URI and return a plugin instance that can read/write the URIs content.

    ``imopen`` takes a URI and searches for a plugin capable of opening it. Once
    a suitable plugin is found, a plugin instance is created that implements the
    imageio API to interact with the image data. The search can be skipped using
    the optional ``plugin="plugin_name"`` argument.

    Notes
    -----

    For library maintainers: If you call imopen from inside the library, you
    will first need to first create an instance, i.e. ``imopen()(uri, ...)``
    (Notice the double parentheses).

    Examples
    --------

    >>> import imageio.v3 as iio
    >>> with iio.imopen("/path/to/image.png", "r") as file:
    >>>     im = file.read()

    >>> with iio.imopen("/path/to/output.jpg", "w") as file:
    >>>     file.write(im)

    """

    _known_plugins = dict()
    _legacy_format_manager = FormatManager()

    def __call__(
        self,
        uri,
        io_mode: str,
        *,
        plugin: str = None,
        search_legacy_only: bool = True,
        **kwargs,
    ):
        """Instantiate a plugin capable of interacting with the given URI

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image
            from, e.g. a filename, pathlib.Path, http address or file object,
            see the docs for more info.
        io_mode : {str}
            The mode to open the file with. Possible values are::

                ``r`` - open the file for reading
                ``w`` - open the file for writing

            Depreciated since v2.9:
            A second character can be added to give the reader a hint on what
            the user expects. This will be ignored by new plugins and will
            only have an effect on legacy plugins. Possible values are::

                ``i`` for an image,
                ``I`` for multiple images,
                ``v`` for a volume,
                ``V`` for multiple volumes,
                ``?`` for don't care (default)

        plugin : {str, None}
            The plugin to be used. If None (default), performs a search for a
            matching plugin.
        search_legacy_only : {bool}
            If true (default), and ``plugin=None`` then only legacy plugins
            (v2.9 and prior) are searched. New plugins (v3.0+) are skipped.
        **kwargs : {any}
            Additional keyword arguments will be passed to the plugin instance.
        """

        request = Request(uri, io_mode)
        plugin_instance = None

        if plugin is not None:
            try:
                candidate_plugin = self._known_plugins[plugin]
            except KeyError:
                request.finish()
                raise ValueError(f"'{plugin}' is not a registered plugin name.")

            try:
                plugin_instance = candidate_plugin(request, **kwargs)
            except InitializationError:
                request.finish()
                raise IOError(f"'{plugin}' can not handle the given uri.")

        else:
            for candidate_plugin in self._known_plugins.values():
                if search_legacy_only:
                    continue
                try:
                    plugin_instance = candidate_plugin(request, **kwargs)
                except InitializationError:
                    continue
                else:
                    break
            else:
                kwargs["plugin_manager"] = self._legacy_format_manager
                kwargs["io_mode"] = io_mode
                kwargs["uri"] = uri

                try:
                    plugin_instance = LegacyPlugin(request, **kwargs)
                except (ValueError, IndexError, KeyError) as e:
                    plugin_instance = None
                    if search_legacy_only:
                        # ensure backwards compatibility and do not change
                        # type of error raised to IOError
                        request.finish()
                        raise e

        if plugin_instance is None:
            request.finish()
            raise IOError(
                f"Could not find a matching plugin to open {uri} with iomode '{io_mode}'"
            )

        return plugin_instance

    @classmethod
    def register_plugin(cls, plugin_name, plugin_class):
        """Register a new plugin to be used when opening URIs.

        Parameters
        ----------
        plugin_name : str
            The name of the plugin to be registered. If the name already exists
            the given plugin will overwrite the old one.
        plugin_class : callable
            A callable that returns an instance of a plugin that conforms
            to the imageio API.
        """

        cls._known_plugins[plugin_name] = plugin_class


class LegacyPlugin:
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
    >>> with iio.imopen("/path/to/image.tiff", "r", search_legacy_only=True) as file:
    >>>     reader = file.legacy_get_reader()  # depreciated
    >>>     for im in file.iter():
    >>>         print(im.shape)

    """

    def __init__(self, request, plugin_manager, uri, io_mode, format=None):
        """Instantiate a new Legacy Plugin

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.
        io_mode : {str}
            Exists to ensure compatibility with imopen. For legacy plugins
            this has no effect.
        plugin_manager : {format.FormatManager instance}
            An instance of the legacy format manager used to find an appropriate
            plugin to load the image. It has to be the reference to the one
            global instance.
        format : {object, None}
            The (legacy) format to use to interface with the URI. If None
            imageio selects the appropriate plugin for you based on the URI.

        """
        self._request = request
        self._plugin_manager = plugin_manager

        plugin = plugin_manager[format]
        if plugin is None and self._request.mode.io_mode == IOMode.read:
            plugin = self._plugin_manager.search_read_format(request)
        elif plugin is None and self._request.mode.io_mode == IOMode.write:
            plugin = self._plugin_manager.search_write_format(request)

        if plugin is None:
            modename = MODENAMES(self._request.mode[1])
            raise ValueError(
                "Could not find a format to read the specified file"
                " in %s mode" % modename
            )

        self._plugin = plugin

        # for backwards compatibility with get_reader/get_writer
        self._uri = uri
        self._io_mode = io_mode

    def legacy_get_reader(self, **kwargs):
        """legacy_get_reader(**kwargs)

        a utility method to provide support vor the V2.9 API

        Parameters
        ----------
        kwargs : ...
            Further keyword arguments are passed to the reader. See :func:`.help`
            to see what arguments are available for a particular format.
        """

        # create a throw-away request
        req = Request(self._uri, self._io_mode, **kwargs)

        return self._plugin.get_reader(req)

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
        """

        if index is None:
            return [im for im in self.iter(**kwargs)]

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

        # create a throw-away request
        req = Request(self._uri, self._io_mode, **kwargs)

        return self._plugin.get_writer(req)

    def write(self, image, **kwargs):
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
            if self._request.mode.image_mode in "iv?":
                writer.append_data(image)
            else:
                if len(image) == 0:
                    raise RuntimeError("Zero images were written.")
                for written, image in enumerate(image):
                    # Test image
                    imt = type(image)
                    image = np.asanyarray(image)
                    if not np.issubdtype(image.dtype, np.number):
                        raise ValueError(
                            "Image is not numeric, but {}.".format(imt.__name__)
                        )
                    elif self._request.mode.image_mode == "I":
                        if image.ndim == 2:
                            pass
                        elif image.ndim == 3 and image.shape[2] in [1, 3, 4]:
                            pass
                        else:
                            raise ValueError(
                                "Image must be 2D " "(grayscale, RGB, or RGBA)."
                            )
                    else:  # self._request.mode.image_mode == "V"
                        if image.ndim == 3:
                            pass
                        elif image.ndim == 4 and image.shape[3] < 32:
                            pass  # How large can a tuple be?
                        else:
                            raise ValueError(
                                "Image must be 3D," " or 4D if each voxel is a tuple."
                            )

                    # Add image
                    writer.append_data(image)

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
        """

        return self.legacy_get_reader().get_meta_data(index=index)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._request.finish()
