from .imopen import imopen
import numpy as np


def imread(uri, *args, index=None, plugin=None, legacy_api=True,
           extra_kwargs_plugin=None, **extra_kwargs_read):
    """ Read an ndimage from a URI.

    Opens the given URI and reads an ndimage from it. The exact behavior
    depends on both, the file type and plugin used to open the file. To learn
    about the exact behavior, check the documentation of the relevant plugin.
    Typically, imread attempts to read all data stored in the URI.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    *args :
        Additional positional arguments will be passed to the plugin instance
        upon object creation.
    index : {int, None}
        If the URI contains multiple ndimages, select the index-th ndimage
        from among them and return it. The exact behavior is plugin dependent.
    plugin : {str, None}
        The plugin to be used. If None, performs a search for a matching plugin.
    legacy_api : {bool}
        The API to be used. If true use the v2.9 API, otherwise use the new
        v3.0 API.
    extra_kwargs_plugin : {dict, None}
        Additional keyword arguments to pass to the plugin's constructor.
    **extra_kwargs_read :
        Additional keyword arguments will be passed to the plugin's read call.

    Returns
    -------
    image : ndimage
    """

    plugin_kwargs = {
        "legacy_api": legacy_api,
        "plugin": plugin
    }

    if extra_kwargs_plugin is not None:
        plugin_kwargs.update(extra_kwargs_plugin)

    with imopen()(uri, *args, **plugin_kwargs) as img_file:
        return np.asarray(img_file.read(index=index, **extra_kwargs_read))


def imiter(uri, *args, plugin=None, legacy_api=True,
           extra_kwargs_plugin=None, **extra_kwargs_iter):
    """ Read a sequence of ndimages from a URI.

    Returns an iterable that yields ndimages from the given URI. The exact
    behavior depends on both, the file type and plugin used to open the file.
    To learn about the exact behavior, check the documentation of the relevant
    plugin.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    *args :
        Additional positional arguments will be passed to the plugin instance
        upon object creation.
    plugin : {str, None}
        The plugin to be used. If None, performs a search for a matching
        plugin.
    legacy_api : {bool}
        The API to be used. If true use the v2.9 API, otherwise use the new
        v3.0 API.
    extra_kwargs_plugin : {dict, None}
        Additional keyword arguments to pass to the plugin's constructor.
    **extra_kwargs_iter :
        Additional keyword arguments will be passed to the plugin's ``iter``
        call.

    Returns
    -------
    image : ndimage
    """

    plugin_kwargs = {
        "legacy_api": legacy_api,
        "plugin": plugin
    }

    if extra_kwargs_plugin is not None:
        plugin_kwargs.update(extra_kwargs_plugin)

    with imopen()(uri, *args, **plugin_kwargs) as img_file:
        for image in img_file.iter(**extra_kwargs_iter):
            # Note: casting to ndarray here to ensure compatibility
            # with the v2.9 API
            yield np.asarray(image)
