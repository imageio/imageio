import imageio as iio
import pytest
from pathlib import Path


def test_exception_message_bytes():
    # regression test for: https://github.com/imageio/imageio/issues/694
    # test via `python -bb -m pytest .\tests\test_legacy_plugin_wrapper.py::test_exception_message_bytes`
    try:
        iio.v3.imread(b"")
    except BytesWarning:
        pytest.fail("raw bytes used in string.")
    except IOError:
        pass  # expected in v3

    try:
        iio.imread(b"")
    except BytesWarning:
        pytest.fail("raw bytes used in string.")
    except ValueError:
        pass  # expected in v3
