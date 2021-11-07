import sys

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main

import imageio
import imageio.plugins.grab


def test_grab_plugin_load():
    imageio.plugins.grab.BaseGrabFormat._ImageGrab = FakeImageGrab
    imageio.plugins.grab.BaseGrabFormat._pillow_imported = True
    _plat = sys.platform
    sys.platform = "win32"

    try:

        reader = imageio.get_reader("<screen>")
        assert reader.format.name == "SCREENGRAB"

        reader = imageio.get_reader("<clipboard>")
        assert reader.format.name == "CLIPBOARDGRAB"

        with raises(ValueError):
            imageio.get_writer("<clipboard>")
        with raises(ValueError):
            imageio.get_writer("<screen>")

    finally:
        sys.platform = _plat
        imageio.plugins.grab.BaseGrabFormat._ImageGrab = None
        imageio.plugins.grab.BaseGrabFormat._pillow_imported = False


class FakeImageGrab:

    has_clipboard = True

    @classmethod
    def grab(cls):
        return np.zeros((8, 8, 3), np.uint8)

    @classmethod
    def grabclipboard(cls):
        if cls.has_clipboard:
            return np.zeros((9, 9, 3), np.uint8)
        else:
            return None


def test_grab_simulated():
    # Hard to test for real, if only because its only fully suppored on
    # Windows, but we can monkey patch so we can test all the imageio bits.

    imageio.plugins.grab.BaseGrabFormat._ImageGrab = FakeImageGrab
    imageio.plugins.grab.BaseGrabFormat._pillow_imported = True
    _plat = sys.platform
    sys.platform = "win32"

    try:

        im = imageio.imread("<screen>")
        assert im.shape == (8, 8, 3)

        reader = imageio.get_reader("<screen>")
        im1 = reader.get_data(0)
        im2 = reader.get_data(0)
        im3 = reader.get_data(1)
        assert im1.shape == (8, 8, 3)
        assert im2.shape == (8, 8, 3)
        assert im3.shape == (8, 8, 3)

        im = imageio.imread("<clipboard>")
        assert im.shape == (9, 9, 3)

        reader = imageio.get_reader("<clipboard>")
        im1 = reader.get_data(0)
        im2 = reader.get_data(0)
        im3 = reader.get_data(1)
        assert im1.shape == (9, 9, 3)
        assert im2.shape == (9, 9, 3)
        assert im3.shape == (9, 9, 3)

        # Grabbing from clipboard can fail if there is no image data to grab
        FakeImageGrab.has_clipboard = False
        with raises(RuntimeError):
            im = imageio.imread("<clipboard>")

    finally:
        sys.platform = _plat
        imageio.plugins.grab.BaseGrabFormat._ImageGrab = None
        imageio.plugins.grab.BaseGrabFormat._pillow_imported = False
        FakeImageGrab.has_clipboard = True


run_tests_if_main()
