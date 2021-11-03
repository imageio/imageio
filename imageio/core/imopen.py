import warnings
from pathlib import Path

from .request import IOMode, Request, InitializationError
from ..config.plugins import known_plugins, PluginConfig, _plugin_list
from ..config.extensions import _extension_dict

class imopen:
    """Open a URI and return a plugin instance that can read/write the URIs content.

    ``imopen`` takes a URI and searches for a plugin capable of opening it. Once
    a suitable plugin is found, a plugin instance is created that implements the
    imageio API to interact with the image data. The search can be skipped using
    the optional ``plugin="plugin_name"`` argument.

    Notes
    -----
    Registered plugins are controlled via the ``known_plugins`` dict in
    ``imageio.config``.

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

    def __call__(
        self,
        uri,
        io_mode: str,
        *,
        plugin: str = None,
        search_legacy_only: bool = True,
        legacy_mode:bool = True,
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

        # complete call using the specified plugin, if specified
        if plugin is None:
            pass  # user did not request plugin explicitly
        elif legacy_mode and plugin not in known_plugins:
            plugin_as_path = Path(plugin)
            plugin = plugin.lower()
            
            if plugin in _extension_dict:
                plugin = _extension_dict[plugin][0].priority[0]
            elif plugin_as_path.suffix.lower() in _extension_dict:
                plugin = plugin_as_path.suffix.lower()
                plugin = _extension_dict[plugin][0].priority[0]
            else:
                request.finish()
                raise IndexError(f"'{plugin}' is not a registered plugin name.")
            
            candidate_plugin = known_plugins[plugin].plugin_class
        elif plugin in known_plugins:
            candidate_plugin = known_plugins[plugin].plugin_class
            try:
                plugin_instance = candidate_plugin(request, **kwargs)
            except InitializationError:
                request.finish()
                raise IOError(f"'{plugin}' can not handle the given uri.")

            return plugin_instance
        else:
            request.finish()
            if legacy_mode:
                # the old API raises an IndexError here.
                raise IndexError(f"'{plugin}' is not a registered plugin name.")
            raise ValueError(f"'{plugin}' is not a registered plugin name.")

        # if all else fails, check all known plugins
        for config in _plugin_list:
            if search_legacy_only and not config.is_legacy:
                continue

            candidate_plugin = config.plugin_class

            try:
                plugin_instance = candidate_plugin(request, **kwargs)
            except InitializationError:
                continue
            else:
                return plugin_instance
        else:
            request.finish()
            raise IOError(
                f"Could not find a backend to open {uri} with iomode '{io_mode}'"
            )
