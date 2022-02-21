import pytest
from pathlib import Path
import imageio as iio
import numpy as np

av = pytest.importorskip("av", reason="pyAV is not installed.")

from av.video.format import names as video_format_names  # noqa: E402
from imageio.plugins.pyav import _format_to_dtype  # noqa: E402


@pytest.fixture()
def video_array():
    # shamelessly based on the pyav example
    duration = 4
    fps = 24
    total_frames = duration * fps

    frames = np.ones((total_frames, 320, 480, 3), dtype=np.uint8)
    for idx in range(total_frames):
        img = np.ones((320, 480, 3)) * [0, 1, 2]
        img = 0.5 + 0.5 * np.sin(2 * np.pi * (img / 3 + idx / total_frames))
        img = np.round(255 * img)
        img = np.clip(img, 0, 255)
        img = img.astype(np.uint8)
        frames[idx] = img

    return frames


def test_mp4_read(test_images: Path):
    with av.open(str(test_images / "cockatoo.mp4"), "r") as container:
        for idx, frame in enumerate(container.decode(video=0)):
            if idx == 4:
                break

    # ImageIO serves the data channel-first
    expected = frame.to_ndarray(format="rgb24")

    result = iio.v3.imread(
        test_images / "cockatoo.mp4", index=42, plugin="pyav", format="rgb24"
    )
    np.allclose(result, expected)

    result = iio.v3.imread(
        test_images / "cockatoo.mp4",
        index=42,
        plugin="pyav",
        constant_framerate=False,
        format="rgb24",
    )
    np.allclose(result, expected)


def test_realshort(test_images: Path):
    iio.v3.imread(
        test_images / "realshort.mp4", index=10, plugin="pyav", format="yuv444p"
    )
    print("")


def test_mp4_writing(tmp_path, video_array):
    # shamelessly based on the pyav example

    with av.open(str(tmp_path / "expected.mp4"), mode="w") as container:
        stream = container.add_stream("libx264", rate=24)
        stream.width = 480
        stream.height = 320
        stream.pix_fmt = "yuv420p"

        for frame in video_array:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            for packet in stream.encode(av_frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)

    iio.v3.imwrite(tmp_path / "foo.mp4", video_array, plugin="pyav", codec="libx264")

    expected = Path(tmp_path / "expected.mp4").read_bytes()
    result = Path(tmp_path / "foo.mp4").read_bytes()

    assert expected == result


def test_metadata(test_images: Path):
    with iio.v3.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        meta = plugin.metadata()
        assert meta["profile"] == "High 4:4:4 Predictive"
        assert meta["codec"] == "h264"

        plugin.metadata(index=4)
    print("")


def test_properties(test_images: Path):
    with iio.v3.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        plugin.properties()
        plugin.properties(index=4)


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
    frames = iio.v3.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("drawgrid", "w=iw/3:h=ih/3:t=2:c=white@0.5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )

    assert frames.shape == (280, 3, 480, 640)


def test_filter_sequence2(test_images):
    frames = iio.v3.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )

    assert frames.shape == (56, 3, 480, 640)


def test_write_bytes(test_images):
    img = iio.v3.imread(
        test_images / "cockatoo.mp4",
        index=None,
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )
    img_bytes = iio.v3.imwrite(
        "<bytes>",
        img,
        format_hint=".mp4",
        plugin="pyav",
        in_pixel_format="yuv444p",
        codec="libx264",
    )

    assert img_bytes is not None


def test_read_png(test_images):
    img_expected = iio.v3.imread(test_images / "chelsea.png", plugin="pillow")
    img_actual = iio.v3.imread(test_images / "chelsea.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_write_png(test_images, tmp_path):
    img_expected = iio.v3.imread(test_images / "chelsea.png", plugin="pyav")
    iio.v3.imwrite(
        tmp_path / "out.png", img_expected, plugin="pyav", codec="png", is_batch=False
    )
    img_actual = iio.v3.imread(tmp_path / "out.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_gif_gen(test_images):
    frames = iio.v3.imread(
        test_images / "cockatoo.mp4", plugin="pyav", index=None, format="rgb24"
    )

    iio.v3.imwrite(
        "test.gif",
        frames,
        plugin="pyav",
        codec="gif",
        out_pixel_format="pal8",
        filter_sequence=[
            ("fps", "15"),
            ("scale", "320:-1:flags=lanczos"),
        ],
        filter_graph=(
            {  # Nodes
                "split": ("split", ""),
                "palettegen": ("palettegen", {"stats_mode": "single"}),
                "paletteuse": ("paletteuse", ""),
                "format": ("format", "pal8"),
            },
            [  # Edges
                ("video_in", "split", 0, 0),
                ("split", "palettegen", 0, 0),
                ("split", "paletteuse", 1, 0),
                ("palettegen", "paletteuse", 0, 1),
                ("paletteuse", "format", 0, 0),
                ("format", "video_out", 0, 0),
            ],
        ),
    )
    # ffmpeg -ss 30 -t 3 -i input.mp4 -vf "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output.gif


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
