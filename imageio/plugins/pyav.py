"""Read/Write Videos (and images) using PyAV.

Backend Library: `PyAV <https://pyav.org/docs/stable/>`_

PyAVPlugin is a plugin that wraps pyAV. pyAV is a set of pythonic bindings for
the FFMPEG library. As such this plugin is similar our famous FFMPEG plugin, but
offers nicer bindings and aims to superseed it in the future.

"""

from math import ceil
from typing import Any, Dict, List, Optional, Tuple, Union
from fractions import Fraction

import av
import av.filter
import numpy as np
from numpy.typing import ArrayLike
from numpy.lib.stride_tricks import as_strided

from ..core import Request
from ..core.request import InitializationError, IOMode, URI_BYTES
from ..core.v3_plugin_api import PluginV3, ImageProperties


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

    Parameters
    ----------
    frame : av.VideoFrame
        A frame for which the resulting shape should be computed.

    Returns
    -------
    shape : Tuple[int, ...]
        A tuple describing the shape of the image data in the frame.

    Notes
    -----

    This function assumes that channel components will be byte-aligned upstream
    if necessary. This applies to the formats monow, monob, rgb4, and rgb8.
    (This will be converted to gray8/rgb24 upstream.)

    """

    widths = [component.width for component in frame.format.components]
    heights = [component.height for component in frame.format.components]
    bits = np.array([component.bits for component in frame.format.components])
    line_sizes = [plane.line_size for plane in frame.planes]

    subsampled_width = widths[:-1] != widths[1:]
    subsampled_height = heights[:-1] != heights[1:]
    unaligned_components = np.any(bits % 8 != 0) or (line_sizes[:-1] != line_sizes[1:])
    if subsampled_width or subsampled_height or unaligned_components:
        raise IOError(
            f"{frame.format.name} can't be expressed as a strided array."
            "Use `format=` to select a format to convert into."
        )

    shape = [frame.height, frame.width]

    n_planes = max([component.plane for component in frame.format.components]) + 1
    if n_planes > 1:
        shape = [n_planes] + shape

    channels_per_plane = [0] * n_planes
    for component in frame.format.components:
        channels_per_plane[component.plane] += 1
    n_channels = max(channels_per_plane)

    if n_channels > 1:
        shape = shape + [n_channels]

    return tuple(shape)


class PyAVPlugin(PluginV3):
    """Support for pyAV as backend.

    Parameters
    ----------
    request : iio.Request
        A request object that represents the users intent. It provides a
        standard interface to access various the various ImageResources and
        serves them to the plugin as a file object (or file). Check the docs for
        details.

    """

    def __init__(
        self,
        request: Request,
        *,
        container: str = None,
    ) -> None:
        """Initialize a new Plugin Instance.

        See Plugin's docstring for detailed documentation.

        Notes
        -----
        The implementation here stores the request as a local variable that is
        exposed using a @property below. If you inherit from PluginV3, remember
        to call ``super().__init__(request)``.

        """

        super().__init__(request)

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
                raise InitializationError(msg) from None
        else:
            file_handle = self.request.get_file()
            filename = getattr(file_handle, "name", None)
            extension = self.request.extension or self.request.format_hint
            if extension is None:
                raise InitializationError("Can't determine output container to use.")

            # hacky, but beats running our own format selection logic
            # (since av_guess_format is not exposed)
            try:
                setattr(file_handle, "name", filename or "tmp" + extension)
            except AttributeError:
                pass  # read-only, nothing we can do

            try:
                self._container = av.open(file_handle, mode="w", format=container)
            except av.AVError:
                resource = (
                    "<bytes>"
                    if isinstance(self.request.raw_uri, bytes)
                    else self.request.raw_uri
                )
                raise InitializationError(f"PyAV can not write to `{resource}`")

    def read(
        self,
        *,
        index: int = 0,
        format: str = "rgb24",
        filter_sequence: List[Tuple[str, Union[str, dict]]] = None,
        filter_graph: Tuple[dict, List] = None,
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
            Set the returned pixel format. If not None (default: rgb24), convert
            the data into the given format before returning it if needed. If
            ``None`` return the data in the encoded format if it can be
            expressed as a strided array; otherwise raise an Exception.
        filter_sequence : List[str, str, dict]
            If not None, apply the given sequence of FFmpeg filters to each
            ndimage. Check the (module-level) plugin docs for details and
            examples.
        filter_graph : (dict, List)
            If not None, apply the given graph of FFmpeg filters to each
            ndimage. The graph is given as a tuple of two dicts. The first dict
            contains a (named) set of nodes, and the second dict contains a set
            of edges between nodes of the previous dict.Check the (module-level)
            plugin docs for details and examples.
        constant_framerate : bool
            If True assume the video's framerate is constant. This allows for
            faster seeking inside the file. If False, the video is reset before
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
        bidirectionaly predicted pictures. I don't have any test videos of this
        though.

        ``format``s that do not have their pixel components byte-aligned, will
        be promoted to equivalent formats with byte-alignment for compatibility
        with numpy.

        Reading from an index other than None currently doesn't support filters
        that introduce delays.

        """

        if constant_framerate is None:
            constant_framerate = self._container.format.variable_fps

        if index is None:
            self._container.seek(0)

            frames = np.stack(
                [
                    x
                    for x in self.iter(
                        format=format,
                        filter_sequence=filter_sequence,
                        filter_graph=filter_graph,
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
        ffmpeg_filter = self._build_filter(filter_sequence, filter_graph)
        ffmpeg_filter.send(None)  # init

        self._seek(index, constant_framerate=constant_framerate)
        desired_frame = next(self._container.decode(video=0))

        return self._unpack_frame(ffmpeg_filter.send(desired_frame), format=format)

    def iter(
        self,
        *,
        format: str = None,
        filter_sequence: List[Tuple[str, Union[str, dict]]] = None,
        filter_graph: Tuple[dict, List] = None,
        thread_count: int = 0,
        thread_type: str = None,
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
        filter_sequence : List[str, str, dict]
            If not None, apply the given sequence of FFmpeg filters to each
            ndimage. Check the (module-level) plugin docs for details and
            examples.
        filter_graph : (dict, List)
            If not None, apply the given graph of FFmpeg filters to each
            ndimage. The graph is given as a tuple of two dicts. The first dict
            contains a (named) set of nodes, and the second dict contains a set
            of edges between nodes of the previous dict. Check the (module-level)
            plugin docs for details and examples.
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
        ffmpeg_filter = self._build_filter(filter_sequence, filter_graph)
        ffmpeg_filter.send(None)  # init

        for frame in self._container.decode(video=0):
            frame = ffmpeg_filter.send(frame)

            if frame is None:
                continue

            yield self._unpack_frame(frame, format=format)

        for frame in ffmpeg_filter:
            yield self._unpack_frame(frame, format=format)

    def _unpack_frame(self, frame: av.VideoFrame, *, format: str = None) -> np.ndarray:
        """Convert a av.VideoFrame into a ndarray

        Parameters
        ----------
        frame : av.VideoFrame
            The frame to unpack.
        format : str
            If not None, convert the frame to the given format before unpacking.

        """

        if format is not None:
            frame = frame.reformat(format=format)

        dtype = _format_to_dtype(frame.format)
        shape = _get_frame_shape(frame)

        planes = list()
        for idx in range(len(frame.planes)):
            n_channels = sum(
                [
                    x.bits // (dtype.itemsize * 8)
                    for x in frame.format.components
                    if x.plane == idx
                ]
            )
            av_plane = frame.planes[idx]
            plane_shape = (av_plane.height, av_plane.width)
            plane_strides = (av_plane.line_size, n_channels * dtype.itemsize)
            if n_channels > 1:
                plane_shape += (n_channels,)
                plane_strides += (dtype.itemsize,)

            np_plane = as_strided(
                np.frombuffer(av_plane, dtype=dtype),
                shape=plane_shape,
                strides=plane_strides,
            )
            planes.append(np_plane)

        if len(planes) > 1:
            # Note: the planes *should* exist inside a contigous memory block
            # somewhere inside av.Frame however pyAV does not appear to expose this,
            # so we are forced to copy the planes individually instead of wrapping
            # them :(
            out = np.concatenate(planes).reshape(shape)
        else:
            out = planes[0]

        return out

    def write(
        self,
        ndimage: Union[ArrayLike, List[ArrayLike]],
        *,
        codec: str,
        is_batch: bool = True,
        fps: int = 24,
        in_pixel_format: str = "rgb24",
        out_pixel_format: str = None,
        filter_sequence: List[Tuple[str, Union[str, dict]]] = None,
        filter_graph: Tuple[dict, List] = None,
    ) -> Optional[bytes]:
        """Save a ndimage as a video.

        Given a batch of frames (stacked along the first axis) or a list of
        frames, encode them and save the result in the ImageResource.

        Parameters
        ----------
        ndimage : ArrayLike, List[ArrayLike]
            The ndimage to encode and write to the current ImageResource.
        codec : str
            The codec to use when encoding frames.
        container_format: str
            The container format to use when writing the video. If None (default)
            this is chosen based on the request if possible. This only affects
            writing.
        is_batch : bool
            If True (default), the ndimage is a batch of images, otherwise it is
            a single image. This parameter has no effect on lists of ndimages.
        fps : str
            The resulting videos frames per second.
        in_pixel_format : str
            The pixel format of the incoming ndarray. Defaults to "rgb24" and can
            be any stridable pix_fmt supported by FFmpeg.
        out_pixel_format : str
            The pixel format to use while encoding frames. If None (default)
            use the codec's default.
        filter_sequence : List[str, str, dict]
            If not None, apply the given sequence of FFmpeg filters to each
            ndimage. Check the (module-level) plugin docs for details and
            examples.
        filter_graph : (dict, List)
            If not None, apply the given graph of FFmpeg filters to each
            ndimage. The graph is given as a tuple of two dicts. The first dict
            contains a (named) set of nodes, and the second dict contains a set
            of edges between nodes of the previous dict. Check the (module-level)
            plugin docs for details and examples.

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

        Writing currently only supports filters that don't introduce delay.

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

        ffmpeg_filter = self._build_filter(filter_sequence, filter_graph)
        ffmpeg_filter.send(None)  # init

        pixel_format = av.VideoFormat(in_pixel_format)
        img_dtype = _format_to_dtype(pixel_format)
        width = ndimage.shape[3 if pixel_format.is_planar else 2]
        height = ndimage.shape[2 if pixel_format.is_planar else 1]

        frame = av.VideoFrame(width, height, in_pixel_format)
        frame.time_base = Fraction(1, fps)
        n_channels = [
            sum(
                [
                    x.bits // (img_dtype.itemsize * 8)
                    for x in frame.format.components
                    if x.plane == idx
                ]
            )
            for idx in range(len(frame.planes))
        ]

        for img in ndimage:
            frame.pts = self._video_stream.frames
            # manual packing of ndarray into frame
            # (this should live in pyAV, but it doesn't support many formats
            # and PRs there are slow)
            if pixel_format.is_planar:
                for idx, plane in enumerate(frame.planes):
                    plane_array = np.frombuffer(plane, dtype=img_dtype)
                    plane_array = as_strided(
                        plane_array,
                        shape=(plane.height, plane.width),
                        strides=(plane.line_size, img_dtype.itemsize),
                    )
                    plane_array[...] = img[idx]
            else:
                n_channels = len(pixel_format.components)
                plane = frame.planes[0]

                plane_shape = (plane.height, plane.width)
                plane_strides = (plane.line_size, n_channels * img_dtype.itemsize)
                if n_channels > 1:
                    plane_shape += (n_channels,)
                    plane_strides += (img_dtype.itemsize,)

                plane_array = as_strided(
                    np.frombuffer(plane, dtype=img_dtype),
                    shape=plane_shape,
                    strides=plane_strides,
                )
                plane_array[...] = img

            out_frame = ffmpeg_filter.send(frame)
            if out_frame is None:
                continue

            out_frame = out_frame.reformat(format=out_pixel_format)

            for packet in stream.encode(out_frame):
                self._container.mux(packet)

        for out_frame in ffmpeg_filter:
            out_frame.pts = self._video_stream.frames
            for packet in stream.encode(out_frame):
                self._container.mux(packet)

        if self.request._uri_type == URI_BYTES:
            # bytes are immutuable, so we have to flush immediately
            # and can't support appending to an active stream
            for packet in self._video_stream.encode():
                self._container.mux(packet)
            self._video_stream = None
            self._container.close()

            return self.request.get_file().getvalue()

    def _init_write_stream(
        self,
        codec: str,
        fps: int,
        shape: Tuple[int, ...],
        in_pixel_format: Optional[str],
        out_pixel_format: Optional[str],
    ) -> None:
        """Initialize encoder and create a new video stream.

        Parameters
        ----------
        codec : str
            The codec to use.
        fps : str
            The resulting videos frames per second.
        shape : Tuple[int, ...]
            The shape of the frames that will be written.
        in_pixel_format : str
            The pixel format of the incoming ndarray.
        out_pixel_format : str
            The pixel format to use while encoding frames. If None (default)
            use the codec's default.

        """

        stream = self._container.add_stream(codec, fps)
        px_format = av.VideoFormat(in_pixel_format)
        stream.width = shape[3 if px_format.is_planar else 2]
        stream.height = shape[2 if px_format.is_planar else 1]
        stream.time_base = Fraction(1, fps)

        if out_pixel_format is not None:
            stream.pix_fmt = out_pixel_format
        elif in_pixel_format in [x.name for x in stream.codec.video_formats]:
            stream.pix_fmt = in_pixel_format
        else:
            pass  # use the default pixel format

        self._video_stream = stream

    def _build_filter(
        self,
        filter_sequence: List[Tuple[str, Union[str, dict]]] = None,
        filter_graph: Tuple[dict, List] = None,
    ) -> av.VideoFrame:
        """Create a FFmpeg filter graph.

        This function is a python co-routine. This means it returns a
        generator and you can feed it frames using ``generator.send(frame)``
        and it will return the next frame or None (if the filter has lag).
        To send EOF use ``generator.send(None)``


        Parameters
        ----------
        filter_sequence : List[str, str, dict]
            If not None, apply the given sequence of FFmpeg filters to each
            ndimage. Check the (module-level) plugin docs for details and
            examples.
        filter_graph : (dict, List)
            If not None, apply the given graph of FFmpeg filters to each
            ndimage. The graph is given as a tuple of two dicts. The first dict
            contains a (named) set of nodes, and the second dict contains a set
            of edges between nodes of the previous dict.Check the (module-level)
            plugin docs for details and examples.

        Yields
        -------
        frame : Optional[av.VideoFrame]
            A frame that was filtered using the created filter or None if the
            filter has lag and didn't send any frames yet.

        """

        node_descriptors: Dict[str, Tuple[str, Union[str, Dict]]]
        edges: List[Tuple[str, str, int, int]]

        # Nothing to do :)
        if filter_sequence is None and filter_graph is None:
            frame = yield

            while frame is not None:
                frame = yield frame

            return

        if filter_sequence is None:
            filter_sequence = list()

        if filter_graph is None:
            node_descriptors, edges = dict(), [("video_in", "video_out", 0, 0)]
        else:
            node_descriptors, edges = filter_graph

        graph = av.filter.Graph()

        previous_node = graph.add_buffer(template=self._video_stream)
        for filter_name, argument in filter_sequence:
            if isinstance(argument, str):
                current_node = graph.add(filter_name, argument)
            else:
                current_node = graph.add(filter_name, **argument)
            previous_node.link_to(current_node)
            previous_node = current_node

        nodes = dict()
        nodes["video_in"] = previous_node
        nodes["video_out"] = graph.add("buffersink")
        for name, (filter_name, arguments) in node_descriptors.items():
            if isinstance(arguments, str):
                nodes[name] = graph.add(filter_name, arguments)
            else:
                nodes[name] = graph.add(filter_name, **arguments)

        for from_note, to_node, out_idx, in_idx in edges:
            nodes[from_note].link_to(nodes[to_node], out_idx, in_idx)

        graph.configure()

        # this starts a co-routine
        # send frames using graph.send()
        frame = yield None

        # send and receive frames in "parallel"
        while frame is not None:
            graph.push(frame)
            try:
                frame = yield graph.pull()
            except av.error.BlockingIOError:
                # filter has lag and needs more frames
                frame = yield None

        try:
            # send EOF in av>=9.0
            graph.push(None)
        except ValueError:
            pass

        # all frames have been sent, empty the filter
        while True:
            try:
                yield graph.pull()
            except av.error.EOFError:
                break  # EOF
            except av.error.BlockingIOError:
                break  # graph exhausted

    def properties(self, index: int = 0, *, format: str = None) -> ImageProperties:
        """Standardized ndimage metadata.

        Parameters
        ----------
        index : int
            The index of the ndimage for which to return properties. If the
            index is out of bounds a ``ValueError`` is raised. If ``None``,
            return the properties for the ndimage stack. If this is impossible,
            e.g., due to shape missmatch, an exception will be raised.
        format : str
            If not None, convert the data into the given format before returning
            it. If None (default) return the data in the encoded format if it
            can be expressed as a strided array; otherwise raise an Exception.

        Returns
        -------
        properties : ImageProperties
            A dataclass filled with standardized image metadata.

        Notes
        -----
        The provided metadata provides information about the ImageResource and
        does not include modifications by any filters (through
        ``filter_sequence`` or ``filter_graph``).

        """

        video_width = self._video_stream.codec_context.width
        video_height = self._video_stream.codec_context.height
        pix_format = format or self._video_stream.codec_context.pix_fmt
        frame_template = av.VideoFrame(video_width, video_height, pix_format)

        shape = _get_frame_shape(frame_template)
        if index is None:
            n_frames = self._video_stream.frames
            shape = (n_frames,) + shape

        return ImageProperties(
            shape=tuple(shape),
            dtype=_format_to_dtype(frame_template.format),
            is_batch=True if index is None else False,
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
            frame_delta = 1000 // self._video_stream.guessed_rate
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

    def __enter__(self) -> "PyAVPlugin":
        return super().__enter__()
