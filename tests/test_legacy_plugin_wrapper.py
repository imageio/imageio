from io import BytesIO

from PIL import Image
from PIL.PngImagePlugin import PngInfo

import imageio as iio
import pytest


def test_exception_message_bytes():
    # regression test for: https://github.com/imageio/imageio/issues/694
    # test via `python -bb -m pytest .\tests\test_legacy_plugin_wrapper.py::test_exception_message_bytes`
    # if run normally, whill check that bytes are not reported

    try:
        iio.v3.imread(b"This will not be reported.")
    except BytesWarning:
        pytest.fail("raw bytes used in string.")
    except IOError as e:
        assert "This will not be reported." not in str(e)
        assert "<bytes>" in str(e)

    try:
        iio.v2.imread(b"This will not be reported.")
    except BytesWarning:
        pytest.fail("raw bytes used in string.")
    except ValueError as e:
        assert "This will not be reported." not in str(e)
        assert "<bytes>" in str(e)


def test_ellipsis_index(test_images):
    img = iio.v3.imread(test_images / "chelsea.png", plugin="PNG-PIL", index=...)
    assert img.shape == (1, 300, 451, 3)

    props = iio.v3.improps(
        test_images / "chelsea.png",
        plugin="PNG-PIL",
        index=...,
    )
    assert props.shape == (1, 300, 451, 3)

    metadata = iio.v3.immeta(
        test_images / "chelsea.png", plugin="PNG-PIL", index=0, exclude_applied=False
    )
    assert metadata == {}


def test_properties(test_images):
    p = iio.v3.improps(test_images / "newtonscradle.gif", plugin="GIF-PIL", index=...)
    assert p.shape == (36, 150, 200, 4)
    assert p.n_images == 36
    assert p.is_batch

    p = iio.v3.improps(test_images / "newtonscradle.gif", plugin="GIF-PIL", index=0)
    assert p.shape == (150, 200, 4)
    assert p.n_images is None
    assert not p.is_batch


@pytest.mark.parametrize("index", [None, 0, Ellipsis])
@pytest.mark.parametrize("as_stream", [False, True])
@pytest.mark.parametrize("plugin", ["PNG-PIL", "GIF-PIL"])
def test_global_metadata(plugin, index, as_stream):
    buffer = BytesIO()
    image = Image.new("RGB", (3, 2), "red")
    if plugin == "PNG-PIL":
        info = PngInfo()
        info.add_text("Description", "global metadata")
        image.save(buffer, format="PNG", pnginfo=info)
        expected = {"Description": "global metadata"}
    else:
        image.save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=[Image.new("RGB", (3, 2), "blue")],
            duration=[100, 300],
            loop=2,
        )
        expected = {"loop": 2, "duration": 100}
    data = buffer.getvalue()
    uri = BytesIO(data) if as_stream else data
    metadata = iio.v3.immeta(uri, plugin=plugin, index=index)
    for name, value in expected.items():
        assert metadata[name] == value
