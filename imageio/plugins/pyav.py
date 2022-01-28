"""Read/Write Videos (and images) using PyAV.

Backend Library: `PyAV <https://pyav.org/docs/stable/>`_

PyAVPlugin is a plugin that wraps pyAV. pyAV is a set of pythonic bindings for
the FFMPEG library. As such this plugin is similar our famous FFMPEG plugin, but
offers nicer bindings and aims to superseed it in the future.

"""

from ..core import Request
from numpy.typing import ArrayLike
import numpy as np
from typing import Optional, Dict, Any, Tuple, Union, List
from ..core.request import InitializationError, IOMode

import av


class ImageProperties:
    def __init__(self, shape: Tuple[int, ...], dtype: np.dtype) -> None:
        # TODO: replace with dataclass once py3.6 is dropped.
        self.shape = shape
        self.dtype = dtype


class PyAVPlugin:
    """Support for pyAV as backend.

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

        if request.mode.io_mode == IOMode.read:
            try:
                self._container = av.open(request.get_file())
            except av.error.InvalidDataError as e:
                if isinstance(request.raw_uri, bytes):
                    msg = "PyAV does not support `<bytes>`"
                else:
                    msg = f"PyAV does not support `{request.raw_uri}`"
                raise InitializationError(msg)
        elif request.mode.io_mode == IOMode.write:
            self._container = av.open(request.get_file(), mode="w")
            # TODO: translate exceptions into Initialization Errors

            raise InitializationError("Writing is currently not supported.")
        else:
            raise InitializationError("Unsupported mode.")

    def read(self, *, index: int = 0, format: str = "rgb24") -> np.ndarray:
        """Read frames from the video.

        If ``index`` is numerical, this function reads the index-th frame from
        the file. If ``index`` is None, this function reads all frames from the
        video, stacks them along the first dimension, and returns a batch of
        frames.

        Parameters
        ----------
        index : int
            The index of the frame to read, e.g. ``index=5`` reads the 5th
            frame. If ``None``, read all the frames in the video and stack them
            along a new, prepended, batch dimension.
        format : str
            If not None, convert the data into the given format before returning
            it.

        Returns
        -------
        frame : np.ndarray
            A numpy array containing loaded frame data.

        Notes
        -----
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

        frame_generator = self._container.decode(video=0)

        if index is None:
            frames = [x.to_ndarray(format=format) for x in frame_generator]
            return np.stack(frames)

        for _ in range(index):
            next(frame_generator)

        return next(frame_generator).to_ndarray(format=format)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        codec: str = "mpeg4",
        fps: int = 24,
        pixel_format: str = "yuv420p",
        numpy_format: str = "rgb24",
    ) -> Optional[bytes]:
        """Save a ndimage as a video.

        Given a batch of frames (stacked along the first axis) or a list of
        frames, encode them and save the result in the ImageResource.

        Parameters
        ----------
        ndimage : ArrayLike
            The ndimage to encode and write to the current ImageResource.


        Returns
        -------
        encoded_image : bytes or None
            If the chosen ImageResource is the special target ``"<bytes>"`` then
            write will return a byte string containing the encoded image data.
            Otherwise, it returns None.

        """

        was_list = False

        if isinstance(ndimage, list):
            # frames _should_ be stackable
            ndimage = np.stack(ndimage)
            was_list = True
        else:
            ndimage = np.asarray(ndimage)

        # make ndimage (batch, width, heigh, [channel])
        if was_list:
            pass  # nothing to do
        elif ndimage.ndim > 3:
            pass  # (time, height, width, channel)
        elif ndimage.ndim == 2:
            # single gray frame
            ndimage = ndimage[None, ...]
        elif ndimage.ndim == 1:
            raise ValueError("ndimage should be at least 2D.")
        elif ndimage.shape[-1] < 4:
            # TODO: use a more sophisticated resolution.
            # basing it on shape is hacky af

            # single frame with channel
            ndimage = ndimage[None, ...]
        else:
            raise ValueError("Malformatted input image.")

        duration = 4
        total_frames = duration * fps

        stream = self._container.add_stream(codec, rate=fps)
        stream.width = ndimage.shape[2]
        stream.height = ndimage.shaoe[1]
        stream.pix_fmt = pixel_format

        for img in ndimage:
            frame = av.VideoFrame.from_ndarray(img, format=numpy_format)
            for packet in stream.encode(frame):
                self._container.mux(packet)

        # Flush stream
        for packet in stream.encode():
            self._container.mux(packet)

    def iter(self, *, format="rgb24") -> np.ndarray:
        """Yield frames from the video.

        Parameters
        ----------
        frame : np.ndarray
            A numpy array containing loaded frame data.


        Yields
        ------
        frame : np.ndarray
            A (decoded) video frame.


        """

        for frame in self._container.decode(video=0):
            yield frame.to_ndarray(format=format)

    def properties(self, index: int = None) -> ImageProperties:
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

        The `kwarg` ``index`` behaves similar to its counterpart in ``read``
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
        """Close the Video."""

        self.request.finish()
        self._container.close()

    @property
    def request(self) -> Request:
        return self._request

    def __enter__(self) -> "PyAVPlugin":
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
