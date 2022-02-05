"""Read/Write Videos (and images) using PyAV.

Backend Library: `PyAV <https://pyav.org/docs/stable/>`_

PyAVPlugin is a plugin that wraps pyAV. pyAV is a set of pythonic bindings for
the FFMPEG library. As such this plugin is similar our famous FFMPEG plugin, but
offers nicer bindings and aims to superseed it in the future.

"""

from math import ceil
from typing import Any, Dict, List, Optional, Tuple, Union

import av
import numpy as np
from av.video.format import names as video_format_names
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


def _extension_to_codec(extension: str) -> str:
    # TODO: populate
    return "mpeg4"


def _guess_format(ndimage: np.ndarray) -> av.VideoFormat:
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
    shape = ndimage.shape[1:]  # pop batch dim
    ndim = ndimage.ndim - 1  # pop batch dim

    if dtype == bool:
        # we assume that True == white
        return "monow"

    if ndim == 2:
        is_planar = False
    else:
        # this may fail for planar frames with small width
        is_planar = shape[-1] not in [2, 3, 4, 6]

    n_channels = shape[0] if is_planar else shape[-1]
    bits_per_pixel = n_channels * dtype.itemsize * 8

    if ndim == 2:
        colorspace = "gray"
    else:
        colorspace = {
            2: "ya",
            3: "rgb",  # this is an assumption
            4: "rgba",  # this, too is an assumption. yuv422 is another good candidate
            6: "yuv411",
        }[n_channels]

    # only those with matching colorspace
    candidate_names = [x for x in video_format_names if colorspace in x]

    candidates = [av.VideoFormat(x) for x in candidate_names]

    # only those with components
    candidates = [x for x in candidates if len(x.components) > 0]

    # only those matching channel first/last
    candidates = [x for x in candidates if x.is_planar == is_planar]

    # only those matching dtype
    candidates = [x for x in candidates if _format_to_dtype(x) == dtype]

    # only those with enough bits per channel
    tmp_candidates = list()
    for candidate in candidates:
        if all(
            [channel.bits >= dtype.itemsize * 8 for channel in candidate.components]
        ):
            tmp_candidates.append(candidate)
    candidates = tmp_candidates

    # only tightly packed formats (ndimage is tightly packed, too)
    if ndimage.flags["C_CONTIGUOUS"]:
        candidates = [
            x for x in candidates if x.padded_bits_per_pixel == bits_per_pixel
        ]

    if len(candidates) == 0:
        raise ValueError(
            "No suitable video format for array of type"
            f" `{dtype}` and shape `{ndimage.shape}`"
        )

    return candidates[0]


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
        self._container = None

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
        format: str = None,
        constant_framerate: bool = True,
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
            If True (default) assume the video's framerate is constant. This
            allows for faster seeking in side the file. If False, the video
            is reset before each read and searched from the beginning.
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

        if format is not None:
            desired_frame = desired_frame.reformat(format=format)

        # byte-align channel components if necessary (by promoting the type)
        if desired_frame.format in ["monow", "monob"]:
            byte_aligned = desired_frame.reformat(format="gray")
        elif desired_frame.format in [
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
            byte_aligned = desired_frame.reformat(format="rgb24")
        elif desired_frame.format in [
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
            byte_aligned = desired_frame.reformat(format="bgr24")
        else:
            byte_aligned = desired_frame

        dtype = _format_to_dtype(desired_frame.format)
        shape = _get_frame_shape(desired_frame)

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
            ]
        )

        return frame_data.reshape(shape)

    def iter(
        self, *, format="rgb24", thread_count: int = 0, thread_type: str = None
    ) -> np.ndarray:
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
            The resulting videos frames per second. If None (default) let
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
        currently hardcoded default inside pyAV.

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
            frame = av.VideoFrame.from_ndarray(img, format=_guess_format(ndimage).name)
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
