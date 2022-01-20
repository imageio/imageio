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
        iio.imread(b"This will not be reported.")
    except BytesWarning:
        pytest.fail("raw bytes used in string.")
    except ValueError as e:
        assert "This will not be reported." not in str(e)
        assert "<bytes>" in str(e)
