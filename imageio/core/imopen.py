from pathlib import Path

from .request import Request, InitializationError
from ..config.plugins import PluginConfig
from ..config import known_plugins
from ..config.extensions import known_extensions


def _get_config(plugin:str, legacy_mode:bool) -> PluginConfig:
    """Look up the config for the given plugin name

    Factored out for legacy compatibility with FormatManager. Move
    back into imopen in V3.
    """

    if legacy_mode and Path(plugin).suffix.lower() in known_extensions:
        # for v2 compatibility, delete in v3
        name = Path(plugin).suffix.lower()
        name = known_extensions[name][0].priority[0]
    elif plugin in known_plugins:
        pass
    elif not legacy_mode:
        raise ValueError(f"'{plugin}' is not a registered plugin name.")
    elif plugin.lower() in known_extensions:
        # for v2 compatibility, delete in v3
        plugin = known_extensions[plugin.lower()][0].priority[0]
    elif "." + plugin.lower() in known_extensions:
        # for v2 compatibility, delete in v3
        name = known_extensions["." + plugin.lower()][0].priority[0]
    else:
        # for v2 compatibility, delete in v3
        raise IndexError(f"No format known by name `{plugin}`.")

    return known_plugins[plugin]


def imopen(
    uri,
    io_mode: str,
    *,
    plugin: str = None,
    legacy_mode: bool = True,
    **kwargs,
):
    """Open an ImageResource.

    Parameters
    ----------
    uri : str or pathlib.Path or bytes or file or Request
        The :doc:`ImageResources <getting_started.request>` to load the image
        from.
    io_mode : {str}
        The mode in which the file is opened. Possible values are::

            ``r`` - open the file for reading
            ``w`` - open the file for writing

        Depreciated since v2.9:
        A second character can be added to give the reader a hint on what
        the user expects. This will be ignored by new plugins and will
        only have an effect on legacy plugins. Possible values are::

            ``i`` for a single image,
            ``I`` for multiple images,
            ``v`` for a single volume,
            ``V`` for multiple volumes,
            ``?`` for don't care (default)

    plugin : {str, None}
        The plugin to use. If set to None (default) imopen will perform a
        search for a matching plugin.
    legacy_mode : bool
        If true (default) use the v2 behavior when searching for a suitable
        plugin. This will ignore v3 plugins and will check ``plugin``
        against known extensions if no plugin with the given name can be found.
    **kwargs : {any}
        Additional keyword arguments will be passed to the plugin upon
        construction.

    Notes
    -----
    Registered plugins are controlled via the ``known_plugins`` dict in
    ``imageio.config``.

    Passing a ``Request`` as the uri is only supported if ``legacy_mode``
    is ``True``. In this case ``io_mode`` is ignored.

    Examples
    --------

    >>> import imageio.v3 as iio
    >>> with iio.imopen("/path/to/image.png", "r") as file:
    >>>     im = file.read()

    >>> with iio.imopen("/path/to/output.jpg", "w") as file:
    >>>     file.write(im)

    """

    if isinstance(uri, Request) and legacy_mode:
        request = uri
    else:
        request = Request(uri, io_mode)

    if plugin is not None:
        # plugin specified, no search needed
        # (except in legacy mode)

        try:
            config = _get_config(plugin, legacy_mode)
        except (IndexError, ValueError):
            request.finish()
            raise

        try:
            candidate_plugin = config.plugin_class
        except ImportError:
            raise ImportError(
                f"The `{config.name}` plugin is not installed. "
                f"Use `pip install imageio[{config.install_name}]` to install it."
            )

        try:
            plugin_instance = candidate_plugin(request, **kwargs)
        except InitializationError:
            request.finish()
            err_type = RuntimeError if legacy_mode else IOError
            raise err_type(f"'{plugin}' can not handle the given uri.")

        return plugin_instance

    if request.extension in known_extensions:
        # fast-path based on file extension
        
        for candidate_format in known_extensions[request.extension]:
            for plugin_name in candidate_format.priority:
                config = known_plugins[plugin_name]
                
                try:
                    candidate_plugin = config.plugin_class
                except ImportError:
                    # not installed
                    continue

                try:
                    plugin_instance = candidate_plugin(request, **kwargs)
                except InitializationError:
                    # file extension doesn't match file type
                    continue

                return plugin_instance

    for config in known_plugins.values():
        # fallback option: try all plugins
        
        
        # Note: for v2 compatibility
        # this branch can be removed in ImageIO v3.0
        if legacy_mode and not config.is_legacy:
            continue

        try:
            plugin_instance = config.plugin_class(request, **kwargs)
        except InitializationError:
            continue
        else:
            return plugin_instance
    else:
        request.finish()
        err_type = ValueError if legacy_mode else IOError
        raise err_type(
            f"Could not find a backend to open {request.raw_uri}"
            f" with iomode '{request.mode.io_mode}'"
        )
