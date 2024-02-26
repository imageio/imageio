"""Tests for rawpy plugin
"""

import rawpy
import imageio.v3 as iio
import numpy as np


def test_nef_local(test_images):
    """Test for reading .nef file from .test_images dir.
    """
    # Check image path
    im_path = str(test_images / "Nikon.nef")

    # Test if plugin's content mathces rawpy content
    actual = iio.imread(im_path)
    expected = rawpy.imread(im_path)
    assert np.allclose(actual, expected)

