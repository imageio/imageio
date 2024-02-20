"""Tests for rawpy plugin
"""

import os
import rawpy
import imageio.v3 as iio


def test_nef_local(test_images):
    """Test for reading .nef file from .test_images dir.
    """
    # Check image path
    im_path = str(test_images / "Nikon.nef")
    assert os.path.exists(im_path)

    # Test if plugin's content mathces rawpy content
    im_plugin = iio.imread(im_path)
    im_rawpy = rawpy.imread(im_path)
    assert im_plugin.all() == im_rawpy.raw_image.all()

