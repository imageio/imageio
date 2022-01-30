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
from dataclasses import dataclass
from math import ceil

import av
from av.video.format import names as video_format_names


@dataclass
class PixelFormat:
    name: str
    dtype: str


available_pix_formats = [
    PixelFormat(
        name="rgb24",
        dtype="|u1",
    )
]


def _video_format_to_dtype(format: av.VideoFormat) -> np.dtype:
    """Convert a pyAV video format into a numpy dtype"""

    if len(format.components) == 0:
        # fake format
        raise ValueError(
            f"Can't determine dtype from format `{format.name}`. It has no channels."
        )

    endian = ">" if format.is_big_endian else "<"
    dtype = "f" if "f32" in format.name else "u"
    bits_per_channel = [x.bits for x in format.components]
    n_bytes = str(int(ceil(bits_per_channel[0] / 8)))

    return np.dtype(endian + dtype + n_bytes)


def _extension_to_codec(extension: str) -> str:
    # TODO: populate
    return "mpeg4"


def _guess_video_format(ndimage: np.ndarray) -> av.VideoFormat:
    """Guesses the video format from array dtype and shape.

    This will !! __NOT__ !! always do the right thing. dtype + shape is too
    little information to uniquely determine the type. In cases where multiple
    formats alias, we assume that the data is in the more commonly used format and
    hope that users of more esoteric formats will specify the format explicitly.

    Parameters
    ----------
    ndimage : np.ndarray
        The array for which to guess the video format. This function assumes
        that the first dimension is the batch dimension along which frames are
        stacked.

    Returns
    -------
    format : av.VideoFormat
        The inferred video format.

    """

    dtype = ndimage.dtype
    shape = ndimage.shape[1:]
    ndim = ndimage.ndim

    if dtype == bool:
        # we assume that True == white
        return "monow"

    if ndim == 2:
        # gray image
        for name in (name for name in video_format_names if "gray" in name):
            format = av.VideoFormat(name)
            format_dtype = _video_format_to_dtype(format)
            if format_dtype == dtype:
                return format

    for name in video_format_names:
        format = av.VideoFormat(name)
        format_dtype = _video_format_to_dtype(format)

    return "rgb24"


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
                self._video_stream = self._container.streams.video[0]
                self._decoder = self._container.decode(video=0)
            except av.AVError:
                if isinstance(request.raw_uri, bytes):
                    msg = "PyAV does not support these `<bytes>`"
                else:
                    msg = f"PyAV does not support `{request.raw_uri}`"
                raise InitializationError(msg)
        elif request.mode.io_mode == IOMode.write:
            try:
                self._container = av.open(request.get_file(), mode="w")
            except av.AVError:
                raise InitializationError(f"PyAV can not write to `{request.raw_uri}`")
        else:
            raise InitializationError("Unsupported mode.")

    def read(
        self,
        *,
        index: int = 0,
        format: str = "rgb24",
        constant_framerate: bool = True,
        thread_count: int = 0,
    ) -> np.ndarray:
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
        constant_framerate : bool
            If True (default) assume the video's framerate is constant. This
            allows for faster seeking in side the file. If False, the video
            is reset before each read and searched from the beginning.
        thread_count : int
            How many threads to use when decoding a frame. The default is 0,
            which will set the number using ffmpeg's default, which is based on
            the codec, number of available cores, threadding model, and other
            considerations.

        Returns
        -------
        frame : np.ndarray
            A numpy array containing loaded frame data.

        Notes
        -----
        Accessing random frames repeatedly is costly (O(n)) so you should do so
        only sparingly if possible. In some cases, it can be faster to
        bulk-load the video (if it fits into memory) and to then access the
        returned ndarray randomly.

        This may cause problems for b-frames, i.e., bidirectionaly predicted
        pictures. I don't have any test videos for this ...

        """

        if index is None:
            if self._video_stream.codec.frame_threads:
                # "FRAME" is the better threadding model for bulk reads
                self._video_stream.thread_type = "FRAME"

            frames = np.stack(
                [x for x in self.iter(format=format, thread_count=thread_count)]
            )

            # reset stream container, because threading model can't change after
            # first access
            self._video_stream.close()
            self._video_stream = self._container.streams.video[0]

            return frames

        self._video_stream.codec_context.thread_count = thread_count

        self._seek(index, constant_framerate=constant_framerate)

        desired_frame = next(self._container.decode(video=0))
        return desired_frame.to_ndarray(format=format)

    def iter(self, *, format="rgb24", thread_count: int = 0) -> np.ndarray:
        """Yield frames from the video.

        Parameters
        ----------
        frame : np.ndarray
            A numpy array containing loaded frame data.
        thread_count : int
            How many threads to use when decoding a frame. The default is 0,
            which will set the number using ffmpeg's default, which is based on
            the codec, number of available cores, threadding model, and other
            considerations.


        Yields
        ------
        frame : np.ndarray
            A (decoded) video frame.


        """

        self._video_stream.codec_context.thread_count = thread_count

        for frame in self._container.decode(video=0):
            yield frame.to_ndarray(format=format)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        codec: str = None,
        fps: int = None,
        pixel_format: str = None,
    ) -> Optional[bytes]:
        """Save a ndimage as a video.

        Given a batch of frames (stacked along the first axis) or a list of
        frames, encode them and save the result in the ImageResource.

        Parameters
        ----------
        ndimage : ArrayLike
            The ndimage to encode and write to the current ImageResource.
        codec : str
            The codec to use when encoding frames. If None (default) it is
            chosen automatically.
        fps : str
            The resulting videos frames per second. If None (default) use let
            pyAV decide.
        pixel_format : str
            The pixel format to use while encoding frames. If None (default)
            use the codec's default FPS.

        Returns
        -------
        encoded_image : bytes or None
            If the chosen ImageResource is the special target ``"<bytes>"`` then
            write will return a byte string containing the encoded image data.
            Otherwise, it returns None.

        Notes
        -----
        Leaving FPS at None typically results in 24 FPS, since this is the
        hardcoded default inside pyAV.

        FFMPEG (and by extension pyAV) is, by default, liberal with the pixel
        format (colorspace). If the given ``pixel_format`` is not compatible
        with the selected codec it will emit a warning and switch to a
        compatible one. To raise an exception instead prepend the format with a
        ``+``. For example, to force the rgb24 format (or fail) use
        ``pixel_format="+rgb24"``.

        The typical colorspace in pydata land is RGB (specifically rgb24).
        However, this is not the default colorspace for most codecs. This means
        that the colorspace will typically change during encoding. If this is
        undesired use ``pixel_format="+"`` to force the output format to match
        the input format (and fail if that format isn't supported by the chosen
        codec).

        """

        was_list = False

        if isinstance(ndimage, list):
            ndimage = np.stack(ndimage)
            was_list = True
        else:
            ndimage = np.asarray(ndimage)

        # normalize array dimensions to
        # (time, height, width, [channel])
        if was_list:
            pass
        elif ndimage.ndim == 1:
            raise ValueError("ndimage should be at least 2D.")
        elif ndimage.ndim == 2:
            ndimage = ndimage[None, ...]
        elif ndimage.ndim == 3:
            # TODO: be more sophisticated
            # basing this on shape[-1] is hacky af
            if ndimage.shape[-1] <= 4:
                # single channel-last frame
                ndimage = ndimage[None, ...]
            else:
                # stack of single-channel frames
                pass
        elif ndimage.ndim == 4:
            pass
        else:
            raise ValueError("Unsuitable array shape for video.")

        if codec is None:
            extension = self.request.extension
            # TODO: use format hint (once merged) if extension is still None

            if extension is None:
                raise ValueError(
                    "Can't automatically choose a codec. Set `codec` explicitly."
                )

            codec = _extension_to_codec(extension)

            if codec is None:
                raise ValueError(
                    "Failed to automatically choose a codec. Set `codec` explicitly."
                )

        stream = self._container.add_stream(codec, rate=fps)
        stream.width = ndimage.shape[2]
        stream.height = ndimage.shape[1]
        if pixel_format:
            stream.pix_fmt = pixel_format

        for img in ndimage:
            frame = av.VideoFrame.from_ndarray(
                img, format=_guess_video_format(ndimage).name
            )
            for packet in stream.encode(frame):
                self._container.mux(packet)

        # encode a frame=None to flush any pending packets
        for packet in stream.encode():
            self._container.mux(packet)

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

        width = self._video_stream.codec_context.width
        height = self._video_stream.codec_context.height
        pix_format = self._video_stream.codec_context.pix_fmt
        video_format = av.VideoFormat(pix_format)

        shape = [height, width]

        n_channels = len(video_format.components)
        if n_channels > 1:
            shape += [len(video_format.components)]

        if index is None:
            n_frames = self._video_stream.frames
            shape = [n_frames] + shape

        return ImageProperties(
            shape=tuple(shape), dtype=_video_format_to_dtype(video_format)
        )

    def metadata(
        self,
        index: int = None,
        exclude_applied: bool = True,
        constant_framerate: bool = True,
    ) -> Dict[str, Any]:
        """Read a dictionary filled with metadata.

        Parameters
        ----------
        index : int
            If None (default) return global metadata (the metadata stored in the
            container and video stream). If not None, return the side data
            stored in the frame at the given index.
        exclude_applied : bool
            Currently, this parameter has no effect. It exists for compliance with
            the ImageIO v3 API.
        constant_framerate : bool
            If True (default) assume the video's framerate is constant. This
            allows for faster seeking in side the file. If False, the video
            is reset before each read and searched from the beginning.

        Returns
        -------
        metadata : dict
            A dictionary filled with format-specific metadata fields and their
            values.

        """

        metadata = dict()

        if index is None:
            # useful flags defined on the container and/or video stream
            metadata.update({"video_format": self._video_stream.codec_context.pix_fmt})

            metadata.update(self._container.metadata)
            metadata.update(self._video_stream.metadata)
            return metadata

        self._seek(index, constant_framerate=constant_framerate)
        desired_frame = next(self._container.decode(video=0))

        # useful flags defined on the frame
        metadata.update(
            {
                "key_frame": bool(desired_frame.key_frame),
                "time": desired_frame.time,
                "interlaced_frame": bool(desired_frame.interlaced_frame),
            }
        )

        # side data
        metadata.update({key: value for key, value in desired_frame.side_data.items()})

        return self._container.metadata

    def _seek(self, index, *, constant_framerate: bool = True) -> None:
        """Seeks to the frame at the given index."""

        # this may be made faster for formats that have some kind
        # of keyframe table in their header data.
        if not constant_framerate:
            self._container.seek(0)
            frames_to_yield = index
        else:
            n_frames = self._video_stream.frames
            duration = self._video_stream.duration
            frame_delta = duration // n_frames
            requested_index = frame_delta * index

            # this only seeks to the closed (preceeding) keyframe
            self._container.seek(requested_index)

            keyframe = next(self._container.decode(video=0))
            frames_to_yield = index - keyframe.pts // frame_delta
            self._container.seek(requested_index)

        frame_generator = self._container.decode(video=0)
        for _ in range(frames_to_yield):
            next(frame_generator)

    def close(self) -> None:
        """Close the Video."""

        self._container.close()
        self.request.finish()

    @property
    def request(self) -> Request:
        return self._request

    def __enter__(self) -> "PyAVPlugin":
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
