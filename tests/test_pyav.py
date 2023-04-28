import io
import platform
import warnings
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import pytest
from conftest import IS_PYPY

import imageio.v3 as iio

av = pytest.importorskip("av", reason="pyAV is not installed.")

from av.video.format import names as video_format_names  # type: ignore # noqa: E402

from imageio.plugins.pyav import _format_to_dtype  # noqa: E402

IS_AV_10_0_0 = tuple(int(x) for x in av.__version__.split(".")) == (10, 0, 0)
IS_MACOS = platform.system() == "Darwin"


def test_mp4_read(test_images: Path):
    with av.open(str(test_images / "cockatoo.mp4"), "r") as container:
        for idx, frame in enumerate(container.decode(video=0)):
            if idx == 4:
                break

    # ImageIO serves the data channel-first
    expected = frame.to_ndarray(format="rgb24")

    result = iio.imread(
        test_images / "cockatoo.mp4", index=4, plugin="pyav", format="rgb24"
    )
    assert np.allclose(result, expected)

    result = iio.imread(
        test_images / "cockatoo.mp4",
        index=4,
        plugin="pyav",
        constant_framerate=False,
        format="rgb24",
    )
    assert np.allclose(result, expected)


def test_mp4_read_bytes(test_images):
    encoded_video = (test_images / "cockatoo.mp4").read_bytes()

    img_expected = iio.imread(encoded_video, index=5)
    img = iio.imread(encoded_video, plugin="pyav", index=5)

    assert np.allclose(img, img_expected)


def test_mp4_writing(tmp_path, test_images):
    frames = iio.imread(test_images / "newtonscradle.gif")

    mp4_bytes = iio.imwrite(
        "<bytes>",
        frames,
        extension=".mp4",
        plugin="pyav",
        codec="libx264",
    )

    # libx264 writing is not deterministic and RGB -> YUV is lossy
    # so I have no good ideas how to do serious assertions on the file
    assert mp4_bytes is not None


def test_metadata(test_images: Path):
    with iio.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        if IS_AV_10_0_0:
            with warnings.catch_warnings(record=True):
                meta = plugin.metadata()
        else:
            meta = plugin.metadata()

        assert meta["profile"] == "High 4:4:4 Predictive"
        assert meta["codec"] == "h264"
        assert meta["encoder"] == "Lavf56.4.101"
        assert meta["duration"] == 14
        assert meta["fps"] == 20.0

        if IS_AV_10_0_0:
            with warnings.catch_warnings(record=True):
                meta = plugin.metadata(index=4)
        else:
            meta = plugin.metadata(index=4)

        assert meta["time"] == 0.2
        assert meta["key_frame"] is False


def test_properties(test_images: Path):
    with iio.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        with pytest.raises(IOError):
            # subsampled format
            plugin.properties(format="yuv420p")

        with pytest.raises(IOError):
            # components per channel differs
            plugin.properties(format="nv24")

        props = plugin.properties()
        assert props.shape == (280, 720, 1280, 3)
        assert props.dtype == np.uint8
        assert props.n_images == 280
        assert props.is_batch is True

        props = plugin.properties(index=4, format="rgb48")
        assert props.shape == (720, 1280, 3)
        assert props.dtype == np.uint16
        assert props.n_images is None
        assert props.is_batch is False

        props = plugin.properties(index=5)
        assert props.shape == (720, 1280, 3)
        assert props.dtype == np.uint8
        assert props.n_images is None
        assert props.is_batch is False


def test_video_format_to_dtype():
    # technically not fake, but mostly hwaccel formats which are unsupported in
    # pyAV at the time of writing (2022/03/06). PyAV can instantiate them, but
    # they have no components. Therefore we can't deduce an appropriate dtype
    # from these so we have to raise instead.
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
        "vaapi",
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
        plugin="pyav",
        filter_sequence=[
            ("drawgrid", "w=iw/3:h=ih/3:t=2:c=white@0.5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
            ("tpad", "start=3"),
        ],
    )

    assert frames.shape == (283, 480, 640, 3)

    frames = iio.imread(
        test_images / "cockatoo.mp4",
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )

    assert frames.shape == (56, 480, 640, 3)


def test_filter_graph(test_images):
    frames = iio.imread(
        test_images / "cockatoo.mp4",
        plugin="pyav",
        filter_graph=(
            {
                "step": ("framestep", "5"),
                "scale": ("scale", {"size": "vga", "flags": "lanczos"}),
            },
            [
                ("video_in", "step", 0, 0),
                ("step", "scale", 0, 0),
                ("scale", "video_out", 0, 0),
            ],
        ),
    )

    assert frames.shape == (56, 480, 640, 3)


def test_write_bytes(test_images):
    img = iio.imread(
        test_images / "cockatoo.mp4",
        plugin="pyav",
        filter_sequence=[
            ("framestep", "5"),
            ("scale", {"size": "vga", "flags": "lanczos"}),
        ],
    )
    img_bytes = iio.imwrite(
        "<bytes>",
        img,
        extension=".mp4",
        plugin="pyav",
        codec="libx264",
    )

    assert img_bytes is not None


def test_read_png(test_images):
    img_expected = iio.imread(test_images / "chelsea.png", plugin="pillow")
    img_actual = iio.imread(test_images / "chelsea.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_write_png(test_images, tmp_path):
    img_expected = iio.imread(test_images / "chelsea.png", plugin="pyav", index=0)
    iio.imwrite(
        tmp_path / "out.png",
        img_expected,
        plugin="pyav",
        codec="png",
        is_batch=False,
        out_pixel_format="rgb24",
    )
    img_actual = iio.imread(tmp_path / "out.png", plugin="pyav")

    assert np.allclose(img_actual, img_expected)


def test_gif_write(test_images, tmp_path):
    frames_expected = iio.imread(
        test_images / "newtonscradle.gif", plugin="pyav", format="gray"
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
    frames_actual = iio.imread(tmp_path / "test.gif", plugin="pyav", format="gray")
    assert np.allclose(frames_actual, frames_expected)

    # with iio.v3.imopen("test2.gif", "w", plugin="pyav", container_format="gif", legacy_mode=False) as file:
    #     file.write(frames, codec="gif", out_pixel_format="gray", in_pixel_format="gray")


def test_raises_exception_when_shapes_mismatch(test_images, tmp_path):
    frame_list = [
        np.ones((200, 150), dtype=np.uint8),
        np.ones((256, 256), dtype=np.uint8),
    ]

    with pytest.raises(ValueError):
        iio.imwrite(
            tmp_path / "test.gif",
            frame_list,
            plugin="pyav",
            codec="gif",
            out_pixel_format="gray",
            in_pixel_format="gray",
        )


def test_gif_gen(test_images, tmp_path):
    frames = iio.imread(
        test_images / "realshort.mp4",
        plugin="pyav",
        format="rgb24",
        filter_sequence=[
            ("fps", "50"),
            ("scale", "320:-1:flags=lanczos"),
        ],
    )

    iio.imwrite(
        tmp_path / "test.gif",
        frames,
        plugin="pyav",
        codec="gif",
        fps=50,
        out_pixel_format="pal8",
        filter_graph=(
            {  # Nodes
                "split": ("split", ""),
                "palettegen": ("palettegen", ""),
                "paletteuse": ("paletteuse", ""),
            },
            [  # Edges
                ("video_in", "split", 0, 0),
                ("split", "palettegen", 0, 0),
                ("split", "paletteuse", 1, 0),
                ("palettegen", "paletteuse", 0, 1),
                ("paletteuse", "video_out", 0, 0),
            ],
        ),
    )


def test_variable_fps_seek(test_images):
    with iio.imopen(test_images / "cockatoo.mp4", "r", plugin="pyav") as file:
        expected = iio.imread(test_images / "cockatoo.mp4", index=15, plugin="pyav")
        actual = file.read(index=15, constant_framerate=False)
        assert np.allclose(actual, expected)

        expected = iio.imread(test_images / "cockatoo.mp4", index=3, plugin="pyav")
        actual = file.read(index=3, constant_framerate=False)

        assert np.allclose(actual, expected)

    meta = iio.immeta(
        test_images / "cockatoo.mp4", index=3, plugin="pyav", constant_framerate=False
    )
    assert meta["interlaced_frame"] is False


def test_multiple_writes(test_images):
    # Note: when opening videos via imopen prefer using the additional API for
    # writing (see eg. test_procedual_writing)
    out_buffer = io.BytesIO()
    with iio.imopen(out_buffer, "w", plugin="pyav", extension=".mp4") as file:
        for frame in iio.imiter(
            test_images / "newtonscradle.gif",
            plugin="pyav",
            format="rgba",
        ):
            file.write(frame, is_batch=False, codec="libx264", in_pixel_format="rgba")

    actual = out_buffer.getvalue()
    assert actual is not None


def test_exceptions(tmp_path):
    with pytest.raises(IOError):
        iio.imopen(io.BytesIO(), "w", plugin="pyav", legacy_mode=False)

    with pytest.raises(IOError):
        iio.imopen(b"nonsense", "r", plugin="pyav", legacy_mode=False)

    foo_file = tmp_path / "faulty.mp4"
    foo_file.write_bytes(b"nonsense")
    with pytest.raises(IOError):
        iio.imopen(foo_file, "r", plugin="pyav", legacy_mode=False)


def test_native_pixformat_reading(test_images):
    frames = iio.imread(
        test_images / "cockatoo.mp4",
        index=5,
        plugin="pyav",
        format=None,
    )

    # cockatoo.mp4 uses YUV444p
    assert frames.shape == (3, 720, 1280)


def test_invalid_resource(tmp_path):
    img = np.zeros((100, 100, 3))

    with pytest.raises(IOError):
        iio.imwrite(tmp_path / "foo.abc", img, plugin="pyav")


def test_bayer_write():
    image_shape = (128, 128)
    image = np.zeros(image_shape, dtype="uint8")
    buffer = io.BytesIO()

    with iio.imopen(buffer, "w", plugin="pyav", extension=".mp4") as file:
        image[...] = 0
        for i in range(256):
            image[::2, ::2] = i
            file.write(
                image, is_batch=False, codec="h264", in_pixel_format="bayer_rggb8"
            )

        image[...] = 0
        for i in range(256):
            image[0::2, 1::2] = i
            image[1::2, 0::2] = i
            file.write(
                image, is_batch=False, codec="h264", in_pixel_format="bayer_rggb8"
            )

        image[...] = 0
        for i in range(256):
            image[1::2, 1::2] = i
            file.write(
                image, is_batch=False, codec="h264", in_pixel_format="bayer_rggb8"
            )

    buffer.seek(0)
    img = iio.imread(buffer, plugin="pyav")
    assert img.shape == (768, 128, 128, 3)


def test_sequential_reading(test_images):
    expected_imgs = [
        iio.imread(test_images / "cockatoo.mp4", index=1),
        iio.imread(test_images / "cockatoo.mp4", index=5),
    ]

    with iio.imopen(test_images / "cockatoo.mp4", "r", plugin="pyav") as img_file:
        first_read = img_file.read(index=1, thread_type="FRAME", thread_count=2)
        second_read = img_file.read(index=5)
        actual_imgs = [first_read, second_read]

    assert np.allclose(actual_imgs, expected_imgs)


def test_uri_reading(test_images):
    uri = "https://dash.akamaized.net/dash264/TestCases/2c/qualcomm/1/MultiResMPEG2.mpd"

    with av.open(uri) as container:
        for idx, frame in enumerate(container.decode(video=0)):
            if idx < 250:
                continue

            expected = frame.to_ndarray(format="rgb24")
            break

    actual = iio.imread(uri, plugin="pyav", index=250)

    assert np.allclose(actual, expected)


def test_seek_vs_iter(test_images):
    img_path = test_images / "cockatoo.mp4"
    n_frames = iio.improps(img_path, plugin="pyav").shape[0]
    test_indices = [30, 31, 32, 76, 158, n_frames - 1]

    with iio.imopen(img_path, "r", plugin="pyav") as file:
        for idx, expected in enumerate(
            iio.imiter(img_path, plugin="pyav", thread_type="FRAME")
        ):
            if idx not in test_indices:
                continue

            actual = file.read(index=idx, thread_type="FRAME")
            assert np.allclose(actual, expected)

            actual = iio.imread(img_path, plugin="pyav", index=idx)
            assert np.allclose(actual, expected)


def test_procedual_writing(test_images):
    buffer = io.BytesIO()
    with iio.imopen(buffer, "w", plugin="pyav", extension=".mp4") as file:
        file.init_video_stream("h264")
        for frame in iio.imiter(test_images / "cockatoo.mp4", plugin="pyav"):
            file.write_frame(frame)

    buffer.seek(0)
    actual = iio.imread(buffer, plugin="pyav", extension=".mp4")

    assert actual.shape == (280, 720, 1280, 3)


def test_procedual_writing_with_filter(test_images):
    buffer = io.BytesIO()
    with iio.imopen(buffer, "w", plugin="pyav", extension=".mp4") as file:
        file.init_video_stream("h264", fps=30)
        file.set_video_filter(
            filter_sequence=[
                ("scale", {"size": "vga", "flags": "lanczos"}),
            ]
        )
        for frame in iio.imiter(
            test_images / "cockatoo.mp4", plugin="pyav", format="yuv444p"
        ):
            file.write_frame(frame, pixel_format="yuv444p")

    buffer.seek(0)
    actual = iio.imread(buffer, plugin="pyav", extension=".mp4")

    assert actual.shape == (280, 480, 640, 3)


def test_rotation_flag_metadata(test_images, tmp_path):
    with iio.imopen(tmp_path / "test.mp4", "w", plugin="pyav") as file:
        file.init_video_stream("libx264")
        file.container_metadata["comment"] = "This video has a rotation flag."
        file.video_stream_metadata["rotate"] = "90"

        for _ in range(5):
            for frame in iio.imiter(test_images / "newtonscradle.gif"):
                file.write_frame(frame)

    if IS_AV_10_0_0:
        with warnings.catch_warnings(record=True) as warns:
            meta = iio.immeta(tmp_path / "test.mp4", plugin="pyav")
            assert len(warns) == 1
        pytest.xfail("PyAV 10.0.0 doesn't extract the rotation flag.")
    else:
        meta = iio.immeta(tmp_path / "test.mp4", plugin="pyav")
        assert meta["comment"] == "This video has a rotation flag."
        assert meta["rotate"] == "90"


def test_read_filter(test_images):
    image = iio.imread(
        test_images / "cockatoo.mp4",
        index=5,
        plugin="pyav",
        filter_sequence=[("scale", {"size": "vga", "flags": "lanczos"})],
    )

    assert image.shape == (480, 640, 3)


def test_write_float_fps(test_images):
    fps = 3.5
    frames = iio.imread(test_images / "cockatoo.mp4", plugin="pyav")
    buffer = iio.imwrite(
        "<bytes>", frames, extension=".mp4", codec="h264", plugin="pyav", fps=fps
    )

    assert iio.immeta(buffer, plugin="pyav")["fps"] == fps


def test_keyframe_intervals(test_images):
    buffer = io.BytesIO()
    with ExitStack() as ctx:
        in_file = ctx.enter_context(
            iio.imopen(test_images / "cockatoo.mp4", "r", plugin="pyav")
        )
        out_file = ctx.enter_context(
            iio.imopen(buffer, "w", plugin="pyav", extension=".mp4")
        )

        out_file.init_video_stream(
            "libx264", max_keyframe_interval=5, force_keyframes=True
        )

        for idx in range(50):
            frame = in_file.read(index=idx)
            out_file.write_frame(frame)

    buffer.seek(0)
    key_dist = [0]
    i_dist = [0]
    with iio.imopen(buffer, "r", plugin="pyav") as file:
        n_frames = file.properties().shape[0]
        for idx in range(1, n_frames):
            medatada = file.metadata(index=idx)
            if medatada["frame_type"] == "I":
                i_dist.append(idx)
            if medatada["key_frame"]:
                key_dist.append(idx)

    assert np.max(np.diff(i_dist)) <= 5
    assert np.max(np.diff(key_dist)) <= 5


# the maintainer of pyAV hasn't responded to my bug reports in over 4 months so
# I am disabling this test on pypy to stay sane.
@pytest.mark.skipif(
    IS_PYPY and IS_MACOS,
    reason="Using filters in pyAV sometimes causes segfaults when run on Pypy.",
)
def test_trim_filter(test_images):
    # this is a regression test for:
    # https://github.com/imageio/imageio/issues/951
    frames = iio.imread(
        "imageio:cockatoo.mp4",
        plugin="pyav",
        filter_sequence=[("trim", {"start": "00:00:01", "end": "00:00:02"})],
    )

    assert frames.shape == (20, 720, 1280, 3)
