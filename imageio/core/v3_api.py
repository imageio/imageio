from .imopen import imopen
import numpy as np
from typing import Optional, Iterator


# create name in this namespace to allow ``import imageio.v3 as iio``
imopen = imopen


def imread(
    uri, *, index: int = None, plugin: str = None, format_hint: str = None, **kwargs
) -> np.ndarray:
    """Read an ndimage from a URI.

    Opens the given URI and reads an ndimage from it. The exact behavior
    depends on both the file type and plugin used to open the file. To learn
    about the exact behavior, check the documentation of the relevant plugin.
    Typically, imread attempts to read all data stored in the URI.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    index : {int, None}
        If the URI contains multiple ndimages, select the index-th ndimage
        from among them and return it. The exact behavior is plugin dependent.
    plugin : {str, None}
        The plugin to use. If set to None (default) imread will perform a
        search for a matching plugin. If not None, this takes priority over
        the provided format hint  (if present).
    format_hint : str
        A format hint to help optimize plugin selection given as the format's
        extension, e.g. ".png". This can speed up the selection process for
        ImageResources that don't have an explicit extension, e.g. streams, or
        for ImageResources where the extension does not match the resource's
        content.
    **kwargs :
        Additional keyword arguments will be passed to the plugin's read call.

    Returns
    -------
    image : ndimage
        The ndimage located at the given URI.
    """

    plugin_kwargs = {"legacy_mode": False, "plugin": plugin, "format_hint": format_hint}

    with imopen(uri, "r", **plugin_kwargs) as img_file:
        return np.asarray(img_file.read(index=index, **kwargs))


def imiter(
    uri, *, plugin: str = None, format_hint: str = None, **kwargs
) -> Iterator[np.ndarray]:
    """Read a sequence of ndimages from a URI.

    Returns an iterable that yields ndimages from the given URI. The exact
    behavior depends on both, the file type and plugin used to open the file.
    To learn about the exact behavior, check the documentation of the relevant
    plugin.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path,
        http address or file object, see the docs for more info.
    plugin : {str, None}
        The plugin to use. If set to None (default) imiter will perform a
        search for a matching plugin. If not None, this takes priority over
        the provided format hint (if present).
    format_hint : str
        A format hint to help optimize plugin selection given as the format's
        extension, e.g. ".png". This can speed up the selection process for
        ImageResources that don't have an explicit extension, e.g. streams, or
        for ImageResources where the extension does not match the resource's
        content. If the ImageResource lacks an explicit extension, it will be
        set to this format.
    **kwargs :
        Additional keyword arguments will be passed to the plugin's ``iter``
        call.

    Yields
    -------
    image : ndimage
        The next ndimage located at the given URI.

    """

    plugin_kwargs = {"legacy_mode": False, "plugin": plugin, "format_hint": format_hint}

    with imopen(uri, "r", **plugin_kwargs) as img_file:
        for image in img_file.iter(**kwargs):
            # Note: casting to ndarray here to ensure compatibility
            # with the v2.9 API
            yield np.asarray(image)


def imwrite(
    uri, image: np.ndarray, *, plugin: str = None, format_hint: str = None, **kwargs
) -> Optional[bytes]:
    """Write an ndimage to the given URI.

    The exact behavior depends on the file type and plugin used. To learn about
    the exact behavior, check the documentation of the relevant plugin.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to save the image to, e.g. a filename, pathlib.Path,
        http address or file object, check the docs for more info.
    image : np.ndarray
        The image to write to disk.
    plugin : {str, None}
        The plugin to use. If set to None (default) imwrite will perform a
        search for a matching plugin. If not None, this takes priority over
        the provided format hint (if present).
    format_hint : str
        A format hint to help optimize plugin selection given as the format's
        extension, e.g. ".png". This can speed up the selection process for
        ImageResources that don't have an explicit extension, e.g. streams, or
        for ImageResources where the extension does not match the resource's
        content. If the ImageResource lacks an explicit extension, it will be
        set to this format.
    **kwargs :
        Additional keyword arguments will be passed to the plugin's ``write``
        call.

    Returns
    -------
    encoded_image : None or Bytes
        Returns ``None`` in all cases, except when ``uri`` is set to ``<bytes>``.
        In this case it returns the encoded ndimage as a bytes string.

    """

    plugin_kwargs = {"legacy_mode": False, "plugin": plugin, "format_hint": format_hint}

    with imopen(uri, "w", **plugin_kwargs) as img_file:
        encoded = img_file.write(image, **kwargs)

    return encoded
