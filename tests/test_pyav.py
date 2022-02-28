import pytest
from pathlib import Path
import imageio.v3 as iio
import numpy as np
import io

av = pytest.importorskip("av", reason="pyAV is not installed.")

from av.video.format import names as video_format_names  # noqa: E402
from imageio.plugins.pyav import _format_to_dtype  # noqa: E402


def test_mp4_read(test_images: Path):
    with av.open(str(test_images / "cockatoo.mp4"), "r") as container:
        for idx, frame in enumerate(container.decode(video=0)):
            if idx == 4:
                break

    # ImageIO serves the data channel-first
    expected = frame.to_ndarray(format="rgb24")

    result = iio.imread(
        test_images / "cockatoo.mp4", index=42, plugin="pyav", format="rgb24"
    )
    np.allclose(result, expected)

    result = iio.imread(
        test_images / "cockatoo.mp4",
        index=42,
        plugin="pyav",
        constant_framerate=False,
        format="rgb24",
    )
    np.allclose(result, expected)


def test_mp4_writing(tmp_path, test_images):
    frames = iio.imread(test_images / "newtonscradle.gif", index=None)

    with av.open(str(tmp_path / "expected.mp4"), mode="w") as container:
        stream = container.add_stream("libx264", rate=None)
        stream.width = frames.shape[2]
        stream.height = frames.shape[1]

        for frame in frames:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            for packet in stream.encode(av_frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)

    mp4_bytes = iio.imwrite(
        "<bytes>",
        frames,
        format_hint=".mp4",
        plugin="pyav",
        codec="libx264",
    )

    expected = Path(tmp_path / "expected.mp4").read_bytes()
    # actual = Path(tmp_path / "actual.mp4").read_bytes()
    assert expected == mp4_bytes


def test_metadata(test_images: Path):
    with iio.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        meta = plugin.metadata()
        assert meta["profile"] == "High 4:4:4 Predictive"
        assert meta["codec"] == "h264"

        plugin.metadata(index=4)
    print("")


def test_properties(test_images: Path):
    with iio.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        with pytest.raises(IOError):
            # subsampled format
            plugin.properties(format="yuv420p")

        with pytest.raises(IOError):
            # components per channel differs
            plugin.properties(format="nv24")

        props = plugin.properties()
        assert props.shape == (3, 720, 1280)
        assert props.dtype == np.uint8
        assert props.is_batch is False

        props = plugin.properties(index=4, format="rgb48")
        assert props.shape == (720, 1280, 3)
        assert props.dtype == np.uint16
        assert props.is_batch is False

        props = plugin.properties(index=None)
        assert props.shape == (280, 3, 720, 1280)
        assert props.dtype == np.uint8
        assert props.is_batch is True


def test_video_format_to_dtype():
    fake_formats = [
        "vdpau",
        "dxva2_vld",
        "vaapi_moco",
        "drm_prime",
        "mediacodec",
        "qsv",
        "mmal",
        "vulkan",
        "vaapi_vld",
        "d3d11",
        "d3d11va_vld",
        "videotoolbox_vld",
        "vaapi_idct",
        "opencl",
        "cuda",
        "xvmc",
    ]

    for name in video_format_names:
        format = av.VideoFormat(name)

        if name in fake_formats:
            # should fail
            with pytest.raises(ValueError):
                _format_to_dtype(format)
        else:
            # should succseed
            _format_to_dtype(format)


def test_filter_sequence(test_images):
    frames = iio.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("drawgrid", "w=iw/3:h=ih/3:t=2:c=white@0.5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
            ("tpad", "start=3"),
        ],
    )

    assert frames.shape == (283, 3, 480, 640)


def test_filter_sequence2(test_images):
    frames = iio.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )

    assert frames.shape == (56, 3, 480, 640)


def test_write_bytes(test_images, tmp_path):
    img = iio.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )
    img_bytes = iio.imwrite(
        "<bytes>",
        img,
        format_hint=".mp4",
        plugin="pyav",
        in_pixel_format="yuv444p",
        codec="libx264",
    )

    iio.imwrite(
        tmp_path / "foo.mp4",
        img,
        plugin="pyav",
        in_pixel_format="yuv444p",
        codec="libx264",
    )
    expected = Path(tmp_path / "foo.mp4").read_bytes()

    assert img_bytes is not None
    assert img_bytes == expected


def test_read_png(test_images):
    img_expected = iio.imread(test_images / "chelsea.png", plugin="pillow")
    img_actual = iio.imread(test_images / "chelsea.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_write_png(test_images, tmp_path):
    img_expected = iio.imread(test_images / "chelsea.png", plugin="pyav")
    iio.imwrite(
        tmp_path / "out.png", img_expected, plugin="pyav", codec="png", is_batch=False
    )
    img_actual = iio.imread(tmp_path / "out.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_gif_write(test_images, tmp_path):
    frames_expected = iio.imread(
        test_images / "newtonscradle.gif", plugin="pyav", index=None, format="gray"
    )

    # touch the codepath that creates a video from a list of frames
    frame_list = list(frames_expected)

    iio.imwrite(
        tmp_path / "test.gif",
        frame_list,
        plugin="pyav",
        codec="gif",
        out_pixel_format="gray",
        in_pixel_format="gray",
    )
    frames_actual = iio.imread(
        tmp_path / "test.gif", plugin="pyav", index=None, format="gray"
    )
    np.allclose(frames_actual, frames_expected)

    # with iio.v3.imopen("test2.gif", "w", plugin="pyav", container_format="gif", legacy_mode=False) as file:
    #     file.write(frames, codec="gif", out_pixel_format="gray", in_pixel_format="gray")


def test_gif_gen(test_images):
    frames = iio.imread(
        test_images / "cockatoo.mp4",
        plugin="pyav",
        index=None,
        format="gray",
        filter_sequence=[
            ("fps", "50"),
            ("scale", "320:-1:flags=lanczos"),
            ("format", "gray"),
        ],
    )

    iio.imwrite(
        "test.gif",
        frames,
        plugin="pyav",
        codec="gif",
        fps=50,
        in_pixel_format="gray",
        out_pixel_format="gray",
        filter_graph=(
            {  # Nodes
                "split": ("split", ""),
                "palettegen": ("palettegen", {"stats_mode": "single"}),
                "paletteuse": ("paletteuse", "new=1"),
                # "format": ("format", "gray"),
            },
            [  # Edges
                ("video_in", "split", 0, 0),
                ("split", "palettegen", 0, 0),
                ("split", "paletteuse", 1, 0),
                ("palettegen", "paletteuse", 0, 1),
                ("paletteuse", "video_out", 0, 0),
                # ("paletteuse", "format", 0, 0),
                # ("format", "video_out", 0, 0),
            ],
        ),
    )


def test_variable_fps_seek(test_images):
    expected = iio.imread(test_images / "cockatoo.mp4", index=3, plugin="pyav")
    actual = iio.imread(
        test_images / "cockatoo.mp4", index=3, plugin="pyav", constant_framerate=False
    )

    assert np.allclose(actual, expected)


def test_multiple_writes(test_images, tmp_path):
    frames = iio.imread(test_images / "newtonscradle.gif", index=None, plugin="pyav")

    expected = iio.imwrite(
        "<bytes>",
        frames,
        format_hint=".mp4",
        plugin="pyav",
        codec="libx264",
        in_pixel_format="rgba",
        filter_sequence=[("tpad", "start=3")],
    )

    out_buffer = io.BytesIO()
    with iio.imopen(out_buffer, "w", plugin="pyav", format_hint=".mp4") as file:
        for frame in iio.imiter(
            test_images / "newtonscradle.gif",
            plugin="pyav",
            filter_sequence=[("tpad", "start=3")],
        ):
            file.write(frame, is_batch=False, codec="libx264", in_pixel_format="rgba")

    actual = out_buffer.getvalue()
    assert expected == actual


# def test_shape_from_frame():
#     foo = list()
#     for name in video_format_names:
#         try:
#             test_format = desired_frame.reformat(format=name)
#             foo.append((name, _get_frame_shape(desired_frame.reformat(format=name))))
#         except IOError:
#             pass
#         except ValueError:
#             pass  # unspported by FFMPEG
