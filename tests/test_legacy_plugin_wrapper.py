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


def test_exclude_applied(test_images):
    with pytest.raises(ValueError):
        iio.v3.immeta(
            test_images / "chelsea.png", exclude_applied=True, plugin="PNG-PIL"
        )


def test_ellipsis_index(test_images):
    img = iio.v3.imread(test_images / "chelsea.png", plugin="PNG-FI", index=...)
    assert img.shape == (1, 300, 451, 3)

    props = iio.v3.improps(
        test_images / "chelsea.png",
        plugin="PNG-FI",
        index=...,
    )
    assert props.shape == (1, 300, 451, 3)

    metadata = iio.v3.immeta(
        test_images / "chelsea.png", plugin="PNG-FI", index=0, exclude_applied=False
    )
    assert metadata == {}
