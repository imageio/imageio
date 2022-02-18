from typing import Any, Dict, Iterator, Optional

import numpy as np

from imageio.core.v3_plugin_api import ImageProperties

from .core.imopen import imopen


def imread(
    uri,
    *,
    index: Optional[int] = 0,
    plugin: str = None,
    format_hint: str = None,
    **kwargs
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
    ------
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


def improps(
    uri, *, index: Optional[int] = 0, plugin: str = None, **kwargs
) -> ImageProperties:
    """Read standardized metadata.

    Opens the given URI and reads the properties of an ndimage from it. The
    properties represent standardized metadata. This means that they will have
    the same name regardless of the format being read or plugin/backend being
    used. Further, any field will be, where possible, populated with a sensible
    default (may be `None`) if the ImageResource does not declare a value in its
    metadata.

    Parameters
    ----------
    index : int
        The index of the ndimage for which to return properties. If the
        index is out of bounds a ``ValueError`` is raised. If ``None``,
        return the properties for the ndimage stack. If this is impossible,
        e.g., due to shape missmatch, an exception will be raised.
    plugin : {str, None}
        The plugin to be used. If None, performs a search for a matching
        plugin.
    **kwargs :
        Additional keyword arguments will be passed to the plugin's ``properties``
        call.

    Returns
    -------
    properties : ImageProperties
        A dataclass filled with standardized image metadata.

    Notes
    -----
    Where possible, this will avoid loading pixel data.

    """

    plugin_kwargs = {"legacy_mode": False, "plugin": plugin}

    with imopen(uri, "r", **plugin_kwargs) as img_file:
        properties = img_file.properties(index=index, **kwargs)

    return properties


def immeta(
    uri,
    *,
    index: Optional[int] = 0,
    plugin: str = None,
    exclude_applied: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """Read format-specific metadata.

    Opens the given URI and reads metadata for an ndimage from it. The contents
    of the returned metadata dictionary is specific to both the image format and
    plugin used to open the ImageResource. To learn about the exact behavior,
    check the documentation of the relevant plugin. Typically, immeta returns a
    dictionary specific to the image format, where keys match metadata field
    names and values are a field's contents.

    Parameters
    ----------
    uri : {str, pathlib.Path, bytes, file}
        The resource to load the image from, e.g. a filename, pathlib.Path, http
        address or file object, see the docs for more info.
    index : {int, None}
        If the URI contains multiple ndimages, select the index-th ndimage from
        among them and return it.
    plugin : {str, None}
        The plugin to be used. If None (default), performs a search for a
        matching plugin.
    **kwargs :
        Additional keyword arguments will be passed to the plugin's metadata
        method.

    Returns
    -------
    image : ndimage
        The ndimage located at the given URI.

    """

    plugin_kwargs = {"legacy_mode": False, "plugin": plugin}

    with imopen(uri, "r", **plugin_kwargs) as img_file:
        metadata = img_file.metadata(
            index=index, exclude_applied=exclude_applied, **kwargs
        )

    return metadata


__all__ = ["imopen", "imread", "imwrite", "imiter", "improps", "immeta"]
