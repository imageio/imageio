"""Read/Write Videos (and images) using PyAV.

Backend Library: `PyAV <https://pyav.org/docs/stable/>`_

PyAVPlugin is a plugin that wraps pyAV. pyAV is a set of pythonic bindings for
the FFMPEG library. As such this plugin is similar our famous FFMPEG plugin, but
offers nicer bindings and aims to superseed it in the future.

"""

from math import ceil
from typing import Any, Dict, List, Optional, Tuple, Union
import io

import av
import numpy as np
from av.video.format import names as video_format_names
from av.codec.codec import UnknownCodecError
from numpy.typing import ArrayLike

from ..core import Request
from ..core.request import InitializationError, IOMode


def _format_to_dtype(format: av.VideoFormat) -> np.dtype:
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


def _get_frame_shape(frame: av.VideoFrame) -> Tuple[int, ...]:
    """Compute the frame's array shape

    Notes
    -----

    I can't work out how to express some of the formats as strided arrays.
    For these, an exception will be raised upstream. This affects the following
    formats: nv21, yuv420p. Videos in these formats can still be read, but
    you will have to explicitly specify a stridable format to convert into, e.g.
    rgb24 or YUV444p

    This function assumes that channel components will be byte-aligned upstream
    if necessary. This applies to the formats monow, monob, rgb4, and rgb8.
    (This will be converted to gray8/rgb24 upstream.)

    """

    widths = tuple(x.width for x in frame.format.components)
    heights = tuple(x.height for x in frame.format.components)
    shape = [min(heights), min(widths)]

    if len(frame.format.components) == 0:
        # fake format
        raise ValueError(
            f"Can't determine shape for format `{frame.format.name}`. It has no channels."
        )

    # compute distribution of macropixel components per plane
    # (YUV can be strided on a marcopixel level [at least the channel-last variants])
    components_per_plane = [0] * len(frame.planes)
    for component in frame.format.components:
        components_per_plane[component.plane] += (component.width // min(widths)) * (
            component.height // min(heights)
        )

    if not components_per_plane[:-1] == components_per_plane[1:]:
        raise IOError(
            f"Can not express pixel format `{frame.format.name}` as strided array."
            " Set `format=` explicitly and use a stridable format."
        )

    components = components_per_plane[0]

    if frame.format.is_planar:
        shape = [len(frame.planes)] + shape

    if components > 1:
        shape = shape + [components]

    return shape


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
    container_format: str
        The container format to use when writing the video. If None (default)
        this is chosen based on the request if possible. This only affects
        writing.

    """

    def __init__(self, request: Request, *, container_format: str = None) -> None:
        """Initialize a new Plugin Instance.

        See Plugin's docstring for detailed documentation.

        Notes
        -----
        The implementation here stores the request as a local variable that is
        exposed using a @property below. If you inherit from PluginV3, remember
        to call ``super().__init__(request)``.

        """

        self._request = request
        self._container = None
        self._video_stream = None

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
        else:
            file_handle = request.get_file()

            # this assumes a certain implementation of av.open, but beats
            # running our own format selection logic (since av_guess_format is
            # not exposed)
            if (
                container_format is None
                and hasattr(file_handle, "name")
                and file_handle.name is None
            ):
                extension = self.request.extension or self.request.format_hint
                if extension is not None:
                    setattr(file_handle, "name", "tmp" + extension)

            try:
                self._container = av.open(
                    file_handle, mode="w", format=container_format
                )
            except ValueError:
                if container_format is not None:
                    raise InitializationError(
                        "Could not find a suitable container for "
                        f"extension `.{extension}`. Set `container` explicitly."
                    ) from None
            except av.AVError:
                resource = (
                    "<bytes>" if isinstance(request.raw_uri, bytes) else request.raw_uri
                )
                raise InitializationError(f"PyAV can not write to `{resource}`")

    def read(
        self,
        *,
        index: int = 0,
        format: str = None,
        constant_framerate: bool = None,
        thread_count: int = 0,
        thread_type: str = None,
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
            it. If None (default) return the data in the encoded format if it
            can be expressed as a strided array; otherwise raise an Exception.
        constant_framerate : bool
            If True assume the video's framerate is constant. This allows for
            faster seeking in side the file. If False, the video is reset before
            each read and searched from the beginning. If None (default), this
            value will be read from the container format.
        thread_count : int
            How many threads to use when decoding a frame. The default is 0,
            which will set the number using ffmpeg's default, which is based on
            the codec, number of available cores, threadding model, and other
            considerations.
        thread_type : str
            The threading model to be used. One of

            - `"SLICE"`: threads assemble parts of the current frame
            - `"Frame"`: threads may assemble future frames
            - None (default): Uses SLICE when reading single frames and FRAME
              when reading batches of frames.


        Returns
        -------
        frame : np.ndarray
            A numpy array containing loaded frame data.

        Notes
        -----
        Accessing random frames repeatedly is costly (O(k), where k is the
        average distance between two keyframes). You should do so only sparingly
        if possible. In some cases, it can be faster to bulk-read the video (if
        it fits into memory) and to then access the returned ndarray randomly.

        The current implementation may cause problems for b-frames, i.e.,
        bidirectionaly predicted pictures. I don't have any test videos this
        though.

        ``format``s that do not have their pixel components byte-aligned, will
        be promoted to equivalent formats with byte-alignment for compatibility
        with numpy.

        """

        constant_framerate = constant_framerate or self._container.variable_fps

        if index is None:

            frames = np.stack(
                [
                    x
                    for x in self.iter(
                        format=format,
                        thread_count=thread_count,
                        thread_type=thread_type or "FRAME",
                    )
                ]
            )

            # reset stream container, because threading model can't change after
            # first access
            self._video_stream.close()
            self._video_stream = self._container.streams.video[0]

            return frames

        self._video_stream.thread_type = thread_type or "SLICE"
        self._video_stream.codec_context.thread_count = thread_count

        self._seek(index, constant_framerate=constant_framerate)
        desired_frame = next(self._container.decode(video=0))

        return self._unpack_frame(desired_frame, format=format)

    def iter(
        self, *, format: str = None, thread_count: int = 0, thread_type: str = None
    ) -> np.ndarray:
        """Yield frames from the video.

        Parameters
        ----------
        frame : np.ndarray
            A numpy array containing loaded frame data.
        format : str
            If not None, convert the data into the given format before returning
            it. If None (default) return the data in the encoded format if it
            can be expressed as a strided array; otherwise raise an Exception.
        thread_count : int
            How many threads to use when decoding a frame. The default is 0,
            which will set the number using ffmpeg's default, which is based on
            the codec, number of available cores, threadding model, and other
            considerations.
        thread_type : str
            The threading model to be used. One of

            - `"SLICE"` (default): threads assemble parts of the current frame
            - `"Frame"`: threads may assemble future frames


        Yields
        ------
        frame : np.ndarray
            A (decoded) video frame.


        """

        self._video_stream.thread_type = thread_type or "SLICE"
        self._video_stream.codec_context.thread_count = thread_count

        for frame in self._container.decode(video=0):
            yield self._unpack_frame(frame, format=format)

    def _unpack_frame(
        self, frame: av.VideoFrame, *, format: str = None, out: np.ndarray = None
    ) -> np.ndarray:
        """Convert a av.VideoFrame into a ndarray

        Parameters
        ----------
        frame : av.VideoFrame
            The frame to unpack.
        format : str
            If not None, convert the frame to the given format before unpacking.
        out : np.ndarray
            If not None, the destination to place the result into. It is assumed
            that the buffer is of the correct size.
        """

        if format is not None:
            frame = frame.reformat(format=format)

        # byte-align channel components if necessary (by promoting the type)
        if frame.format in ["monow", "monob"]:
            byte_aligned = frame.reformat(format="gray")
        elif frame.format in [
            "rgb4",
            "rgb4_byte",
            "rgb8",
            "rgb444le",
            "rgb555le",
            "rgb565le",
            "rgb444be",
            "rgb555be",
            "rgb565be",
        ]:
            byte_aligned = frame.reformat(format="rgb24")
        elif frame.format in [
            "bgr4",
            "bgr4_byte",
            "bgr8",
            "bgr444le",
            "bgr555le",
            "bgr565le",
            "bgr444be",
            "bgr555be",
            "bgr565be",
        ]:
            byte_aligned = frame.reformat(format="bgr24")
        else:
            byte_aligned = frame

        dtype = _format_to_dtype(frame.format)
        shape = _get_frame_shape(frame)

        # Note: the planes *should* exist inside a contigous memory block
        # somewhere inside av.Frame however pyAV does not appear to expose this,
        # so we are forced to copy the planes individually instead of wrapping
        # them :(
        # Note2: This may also be a good thing, because I don't know about pyAVs
        # memory model, and it would be bad if it frees the pixel data that we
        # would point to (if we could).
        frame_data = np.concatenate(
            [
                np.frombuffer(byte_aligned.planes[idx], dtype=dtype)
                for idx in range(len(byte_aligned.planes))
            ],
            out=out,
        )

        return frame_data.reshape(shape)

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        is_batch: bool = True,
        codec: str = None,
        fps: int = None,
        in_pixel_format: str = "rgb24",
        out_pixel_format: str = None,
    ) -> Optional[bytes]:
        """Save a ndimage as a video.

        Given a batch of frames (stacked along the first axis) or a list of
        frames, encode them and save the result in the ImageResource.

        Parameters
        ----------
        ndimage : ArrayLike, List[ArrayLike]
            The ndimage to encode and write to the current ImageResource.
        is_batch : bool
            If True (default), the ndimage is a batch of images, otherwise it is
            a single image. This parameter has no effect on lists of ndimages.
        codec : str
            The codec to use when encoding frames. If None (default) it is
            chosen automatically based on the chosen container.
        fps : str
            The resulting videos frames per second. If None (default) let
            pyAV decide.
        in_pixel_format : str
            The pixel format of the incoming ndarray. Defaults to "rgb24" and can
            be any pix_fmt supported by pyAV.
        out_pixel_format : str
            The pixel format to use while encoding frames. If None (default)
            use the codec's default.

        Returns
        -------
        encoded_image : bytes or None
            If the chosen ImageResource is the special target ``"<bytes>"`` then
            write will return a byte string containing the encoded image data.
            Otherwise, it returns None.

        Notes
        -----
        Leaving FPS at None typically results in 24 FPS, since this is the
        currently hardcoded default inside pyAV.

        """

        if isinstance(ndimage, list):
            # frames shapes must agree for video
            ndimage = np.stack(ndimage)
        elif not is_batch:
            ndimage = np.asarray(ndimage)[None, ...]
        else:
            ndimage = np.asarray(ndimage)

        if self._video_stream is None:
            self._init_write_stream(
                codec, fps, ndimage.shape, in_pixel_format, out_pixel_format
            )
        stream = self._video_stream

        for img in ndimage:
            frame = av.VideoFrame.from_ndarray(img, format=in_pixel_format)
            for packet in stream.encode(frame):
                self._container.mux(packet)

    def _init_write_stream(
        self,
        codec: Optional[str],
        fps: Optional[int],
        shape: Tuple[int, ...],
        in_pixel_format: Optional[str],
        out_pixel_format: Optional[str],
    ) -> None:
        """Initialize encoder and create a new video stream.

        Parameters
        ----------
        codec : str
            The codec to use. Can be None, in which case a codec is selected automagically.
        fps : str
            The resulting videos frames per second. If None (default) let
            pyAV decide.
        shape : Tuple[int, ...]
            The shape of the frames that will be written.
        in_pixel_format : str
            The pixel format of the incoming ndarray.
        out_pixel_format : str
            The pixel format to use while encoding frames. If None (default)
            use the codec's default.

        """

        if codec is not None:
            stream = self._container.add_stream(codec)
        else:
            # TODO: once/if av_guess_codec is exposed use this instead
            # TODO: alternatively, once the default codec for a container
            # is exposed, use that one instead.
            codecs = ["libx264", "mpeg4", *av.codecs_available]
            for x in codecs:
                try:
                    codec = av.Codec(x, "w")
                except UnknownCodecError:
                    continue  # codec known but not installed

                if codec.type != "video":
                    continue

                if out_pixel_format is not None:
                    for supported_format in codec.video_formats:
                        if out_pixel_format == supported_format:
                            break
                    else:
                        continue

                try:
                    stream = self._container.add_stream(codec, rate=fps)
                except ValueError:
                    continue  # Unsupported Format

                break
            else:
                raise ValueError(
                    "Failed to automatically choose a codec. Set `codec` explicitly."
                )

        px_format = av.VideoFormat(in_pixel_format)
        stream.width = shape[3 if px_format.is_planar else 2]
        stream.height = shape[2 if px_format.is_planar else 1]
        stream.pix_fmt = out_pixel_format or stream.pix_fmt

        self._video_stream = stream

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

        # TODO: make this more sophisticated, once we roll our own YUV unpacking
        # (the pyAV one is limted to YUV444)
        n_channels = len(video_format.components)
        if n_channels > 1:
            # Note: this will cause problems for NV formats
            # but pyav doesn't support them yet
            if video_format.is_planar:
                shape = [len(video_format.components)] + shape
            else:
                shape += [len(video_format.components)]

        if index is None:
            n_frames = self._video_stream.frames
            shape = [n_frames] + shape

        return ImageProperties(shape=tuple(shape), dtype=_format_to_dtype(video_format))

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
            metadata.update(
                {
                    "video_format": self._video_stream.codec_context.pix_fmt,
                    "codec": self._video_stream.codec.name,
                    "long_codec": self._video_stream.codec.long_name,
                    "profile": self._video_stream.profile,
                }
            )

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

        is_write = self.request.mode.io_mode == IOMode.write
        if is_write and self._video_stream is not None:
            # encode a frame=None to flush any pending packets
            for packet in self._video_stream.encode():
                self._container.mux(packet)

        if self._container is not None:
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
