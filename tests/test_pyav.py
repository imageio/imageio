import pytest
import imageio as iio
from pathlib import Path
import numpy as np
from imageio.plugins.pyav import _video_format_to_dtype

av = pytest.importorskip("av")

from av.video.format import names as video_format_names


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

    expected = frame.to_ndarray(format="rgb24")

    result = iio.v3.imread(test_images / "cockatoo.mp4", index=42, plugin="pyav")
    np.allclose(result, expected)

    result = iio.v3.imread(
        test_images / "cockatoo.mp4", index=42, plugin="pyav", constant_framerate=False
    )
    np.allclose(result, expected)


def test_realshort(test_images: Path):
    result = iio.v3.imread(test_images / "realshort.mp4", index=10, plugin="pyav")
    print("")


def test_mp4_writing(tmp_path, video_array):
    # shamelessly based on the pyav example

    with av.open(str(tmp_path / "expected.mp4"), mode="w") as container:
        stream = container.add_stream("mpeg4", rate=24)
        stream.width = 480
        stream.height = 320
        stream.pix_fmt = "yuv420p"

        for frame in video_array:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            for packet in stream.encode(av_frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)

    iio.v3.imwrite(tmp_path / "foo.mp4", video_array, plugin="pyav")

    expected = Path(tmp_path / "expected.mp4").read_bytes()
    result = Path(tmp_path / "foo.mp4").read_bytes()

    assert expected == result


def test_metadata(test_images: Path):
    with iio.v3.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        meta = plugin.metadata()
        meta2 = plugin.metadata(index=4)


def test_properties(test_images: Path):
    with iio.v3.imopen(str(test_images / "cockatoo.mp4"), "r", plugin="pyav") as plugin:
        props = plugin.properties()
        props2 = plugin.properties(index=4)


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
                dtype = _video_format_to_dtype(format)
        else:
            # should succseed
            dtype = _video_format_to_dtype(format)
