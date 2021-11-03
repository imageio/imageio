from pathlib import Path

from .request import Request, InitializationError
from ..config.plugins import known_plugins, _plugin_list
from ..config.extensions import _extension_dict


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
    uri : {str, pathlib.Path, bytes, file}
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

    Examples
    --------

    >>> import imageio.v3 as iio
    >>> with iio.imopen("/path/to/image.png", "r") as file:
    >>>     im = file.read()

    >>> with iio.imopen("/path/to/output.jpg", "w") as file:
    >>>     file.write(im)

    """

    request = Request(uri, io_mode)

    # complete call using the specified plugin, if specified
    if plugin is not None:
        if plugin in known_plugins:
            pass
        elif not legacy_mode:
            request.finish()
            raise ValueError(f"'{plugin}' is not a registered plugin name.")
        elif plugin.lower() in _extension_dict:
            # for v2 compatibility, delete in v3
            plugin = _extension_dict[plugin.lower()][0].priority[0]
        elif Path(plugin).suffix.lower() in _extension_dict:
            # for v2 compatibility, delete in v3
                plugin = Path(plugin).suffix.lower()
                plugin = _extension_dict[plugin][0].priority[0]
        else:
            # for v2 compatibility, delete in v3
            request.finish()
            raise IndexError(f"'{plugin}' is not a registered plugin name.")

        candidate_plugin = known_plugins[plugin].plugin_class

        try:
            plugin_instance = candidate_plugin(request, **kwargs)
        except InitializationError:
            request.finish()
            err_type = RuntimeError if legacy_mode else IOError
            raise err_type(f"'{plugin}' can not handle the given uri.")

        return plugin_instance

    # if all else fails, check all known plugins
    for config in _plugin_list:
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
        raise IOError(f"Could not find a backend to open {uri} with iomode '{io_mode}'")
