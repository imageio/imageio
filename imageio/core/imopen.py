import numpy as np

from .format import FormatManager, MODENAMES
from .request import Request


class imopen(object):
    """Open a URI and return a plugin instance that can read/write its content.

    ``imopen`` takes a URI and searches for a plugin capable of opening it.
    Once a suitable plugin is found, a plugin instance is created that exposes
    read/write/iter methods to interact with the image data. The search can be
    skipped by providing a valid plugin name as optional input argument.

    Note for library maintainers: If you call imopen from inside the library,
    you will first need to first create an instance, i.e.
    ``imopen()(uri, ...)``. Note the double parentheses.

    """

    _known_plugins = dict()
    _legacy_format_manager = FormatManager()

    def __call__(self, uri, *, plugin=None, legacy_api=True, **kwargs):
        """Instantiate a plugin capable of interacting with the given URI

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.
        plugin : {str, None}
            The plugin to be used. If None, performs a search for a matching plugin.
        legacy_api : {bool}
            The API to be used. If true use the v2.9 API, otherwise use the new
            v3.0 API.
        **kwargs :
            Additional keyword arguments will be passed to the plugin instance.
        """

        plugin_instance = None

        if legacy_api:
            kwargs["plugin"] = plugin
            return LegacyPlugin(uri, self._legacy_format_manager, **kwargs)

        if plugin is not None:
            try:
                plugin_instance = self._known_plugins[plugin]
            except KeyError:
                raise ValueError(f"'{plugin}' is not a registered plugin name.")

        else:
            for candidate_plugin in self._known_plugins.values():
                if candidate_plugin.can_open(uri):
                    plugin_instance = candidate_plugin
                    break
            else:
                raise IOError(f"No registered plugin can read {uri}")

        return plugin_instance(uri, **kwargs)

    @classmethod
    def register_plugin(cls, plugin_name, plugin_class):
        """Register a new plugin to be used when opening URIs.

        Parameters
        ----------
        plugin_name : str
            The name of the plugin to be registered. If the name already exists
            it will be overwritten.
        plugin_class : callable
            A callable that returns an instance of a plugin that conforms
            to the v3.0 API.
        """

        cls._known_plugins[plugin_name] = plugin_class


class Plugin(object):
    def __init__(self, uri):
        """Instantiate a new Legacy Plugin

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.

        """
        self._uri = uri

    def read(self, *, index=None, **kwargs):
        """
        Parses the given URI and creates a ndarray from it.

        Parameters
        ----------
        index : {integer}
            If the URI contains a list of ndimages return the index-th image. If
            None, read all ndimages in the URI and attempt to stack them along
            a new 0-th axis (equivalent to np.stack(imgs, axis=0))
        kwargs : ...
            To be replaced by the implementing plugin. Custom plugin arguments
            go here.
        """
        raise NotImplementedError

    def write(self, image, **kwargs):
        """
        Write an ndimage to the specified URI.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage or list of ndimages to write.
        kwargs : ...
            To be replaced by the implementing plugin. Custom plugin arguments
            go here.
        """
        raise IOError(
            f"The {self.__name__} plugin can not write to the given URI. "
            "Try using a different plugin."
        )

    def iter(self, **kwargs):
        """
        Iterate over a list of ndimages given by the URI

        Parameters
        ----------
        kwargs : ... To be replaced by the
            implementing plugin. Custom plugin arguments go here.
        """

        raise NotImplementedError

    def get_meta(self, *, index=None):
        """Read ndimage metadata from the URI

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the metadata
            corresponding to the index-th image. If None, behavior is decided
            by the plugin. Typically, it returns the metadata for the 0-th
            ndimage.
        """
        raise NotImplementedError

    @classmethod
    def can_open(cls, uri):
        """Verify that plugin can open the given URI

        Verifying that the plugin a URI doesn't make a specific claim on whether
        or not the plugin can read or write the file. Most plugins support both,
        but some may only support reading or writing. E.g. if the location is on
        a remote host (web URL), writing may not be supported. This rules out
        any plugins that are definitely incapable of handling the URI.

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
        raise NotImplementedError

    def can_write(self, uri):
        """Verify that plugin can write to the given URI

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
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


class LegacyPlugin(Plugin):
    """A plugin to expose v2.9 plugins in the v3.0 API

    This plugin is a wrapper around the old FormatManager class and exposes
    all the old plugins via the new API. On top of this it has
    ``legacy_get_reader`` and ``legacy__get_writer`` methods to allow using
    it with the v2.9 API.
    """

    def __init__(self, uri, plugin_manager, plugin=None):
        """Instantiate a new Legacy Plugin

        Parameters
        ----------
        uri : {str, pathlib.Path, bytes, file}
            The resource to load the image from, e.g. a filename, pathlib.Path,
            http address or file object, see the docs for more info.
        plugin_manager : {format.FormatManager instance}
            An instance of the legacy format manager used to find an appropriate
            plugin to load the image. It has to be the reference to the one
            global instance.
        plugin : {object, None}
            The plugin to use to interface with the URI. If None imageio selects
            the appropriate plugin for you based on the URI.

        """
        self._uri = uri
        self._plugin_manager = plugin_manager
        self._plugin = plugin_manager[plugin]

    def legacy_get_reader(self, iio_mode="?", **kwargs):
        """legacy_get_reader( iio_mode='?' **kwargs)

        a utility method to provide support vor the V2.9 API

        Parameters
        ----------
        iio_mode : {'i', 'I', 'v', 'V', '?'}
            Used to give the reader a hint on what the user expects (default "?"):
            "i" for an image, "I" for multiple images, "v" for a volume,
            "V" for multiple volumes, "?" for don't care.
        kwargs : ...
            Further keyword arguments are passed to the reader. See :func:`.help`
            to see what arguments are available for a particular format.
        """

        if iio_mode is None:
            raise ValueError("mode=None is not supported" " for legacy API calls.")
        mode = "r" + iio_mode

        request = Request(self._uri, mode, **kwargs)

        plugin = self._plugin
        if plugin is None:
            plugin = self._plugin_manager.search_read_format(request)

        if plugin is None:
            modename = MODENAMES.get(mode, mode)
            raise ValueError(
                "Could not find a format to read the specified file"
                " in %s mode" % modename
            )

        return plugin.get_reader(request)

    def read(self, *, index=None, iio_mode="?", **kwargs):
        """
        Parses the given URI and creates a ndarray from it.

        .. deprecated:: 2.9.0
          `iio_mode='?'` will be replaced by `iio_mode=None` in
          imageio v3.0.0 .

        Parameters
        ----------
        index : {integer, None}
            If the URI contains a list of ndimages return the index-th
            image. If None, behavior depends on the used api::

                Legacy-style API: return the first element (index=0)
                New-style API: stack list into ndimage along the 0-th dimension
                    (equivalent to np.stack(imgs, axis=0))

        iio_mode : {'i', 'v', '?', None}
            Used to give the reader a hint on what the user expects
            (default "?"): "i" for an image, "v" for a volume, "?" for don't
            care, and "None" to use the new API.
        kwargs : ...
            Further keyword arguments are passed to the reader. See
            :func:`.help` to see what arguments are available for a particular
            format.
        """

        if index is None:
            images = [image for image in self.iter(iio_mode=iio_mode, **kwargs)]
            if len(images) > 1:
                raise IOError(
                    "The image contains more than one image."
                    " Use iter(...) or use index=n"
                    " to load the n-th image instead."
                )
            return images[0]

        reader = self.legacy_get_reader(iio_mode=iio_mode, **kwargs)
        return reader.get_data(index)

    def legacy_get_writer(self, *, iio_mode="?", **kwargs):
        """legacy_get_writer(iio_mode='?', **kwargs)

        Returns a :class:`.Writer` object which can be used to write data
        and meta data to the specified file.

        Parameters
        ----------
        mode : {'i', 'I', 'v', 'V', '?'}
            Used to give the writer a hint on what the user expects (default '?'):
            "i" for an image, "I" for multiple images, "v" for a volume,
            "V" for multiple volumes, "?" for don't care.
        kwargs : ...
            Further keyword arguments are passed to the writer. See :func:`.help`
            to see what arguments are available for a particular format.
        """

        if iio_mode is None:
            raise ValueError("mode=None is not supported" " for legacy API calls.")
        mode = "w" + iio_mode

        plugin = self._plugin
        uri = self._uri

        request = Request(uri, mode, **kwargs)
        if plugin is None:
            plugin = self._plugin_manager.search_write_format(request)

        if plugin is None:
            modename = MODENAMES.get(mode, mode)
            raise ValueError(
                "Could not find a format to write the specified file"
                " in %s mode" % modename
            )

        return plugin.get_writer(request)

    def write(self, image, *, iio_mode="?", **kwargs):
        """
        Write an ndimage to the URI specified in path.

        If the URI points to a file on the current host and the file does not
        yet exist it will be created. If the file exists already, it will be
        appended if possible; otherwise, it will be replaced.

        Parameters
        ----------
        image : numpy.ndarray
            The ndimage or list of ndimages to write.
        iio_mode : {'i', 'I', 'v', 'V', '?', None}
            Used to give the writer a hint on what the user expects
            (default "?"): "i" for an image, "I" for multiple images,
            "v" for a volume, "V" for multiple volumes, "?" for don't
            care, and "None" to use the new API prior to imageio v3.0.0.
        kwargs : ...
            Further keyword arguments are passed to the writer. See
            :func:`.help` to see what arguments are available for a
            particular format.
        """
        with self.legacy_get_writer(iio_mode=iio_mode, **kwargs) as writer:
            if iio_mode in "iv?":
                writer.append_data(image)
            else:
                written = None
                for written, image in enumerate(image):
                    # Test image
                    imt = type(image)
                    image = np.asanyarray(image)
                    if not np.issubdtype(image.dtype, np.number):
                        raise ValueError(
                            "Image is not numeric, but {}.".format(imt.__name__)
                        )
                    elif iio_mode == "I":
                        if image.ndim == 2:
                            pass
                        elif image.ndim == 3 and image.shape[2] in [1, 3, 4]:
                            pass
                        else:
                            raise ValueError(
                                "Image must be 2D " "(grayscale, RGB, or RGBA)."
                            )
                    else:  # iio_mode == "V"
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

                if written is None:
                    raise RuntimeError("Zero images were written.")

        return writer.request.get_result()

    # this could also be __iter__
    def iter(self, *, iio_mode="?", **kwargs):
        """Iterate over a list of ndimages given by the URI

        .. deprecated:: 2.9.0
          `iio_mode='?'` will be replaced by `iio_mode=None` in
          imageio v3.0.0 .

        Parameters
        ----------
        iio_mode : {'I', 'V', '?', None}
            Used to give the reader a hint on what the user expects (default
            "?"): "I" for multiple images, "V" for multiple volumes, "?" for
            don't care, and "None" to use the new API.
        kwargs : ...
            Further keyword arguments are passed to the reader. See
            :func:`.help` to see what arguments are available for a particular
            format.
        """

        reader = self.legacy_get_reader(iio_mode=iio_mode, **kwargs)
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

        mode = "r?"
        request = Request(self._uri, mode)
        plugin = self._plugin

        if plugin is None:
            plugin = self._plugin_manager.search_read_format(request)

        if plugin is None:
            modename = MODENAMES.get(mode, mode)
            raise ValueError(
                "Could not find a format to read the specified file"
                " in %s mode" % modename
            )

        return plugin.get_meta_data(index=index)
