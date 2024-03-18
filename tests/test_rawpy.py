"""Tests for rawpy plugin
"""

import rawpy
import imageio.v3 as iio
import numpy as np


def test_nef_local(test_images):
    """Test for reading .nef file from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "infrared.nef"

    # Test if plugin's content mathces rawpy content
    actual = iio.imread(im_path, index=..., plugin="rawpy")
    expected = rawpy.imread(im_path).postprocess()
    assert np.allclose(actual, expected)


def test_properties(test_images):
    """Test for reading properties of a raw image from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "infrared.nef"

    # Test properties of a .nef image
    properties = iio.improps(im_path, plugin="rawpy")
    assert properties.shape == (2014, 3039)
    assert properties.dtype == np.uint16


def test_metadata(test_images):
    """Test for reading metadata of a raw image from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "infrared.nef"

    # Test metadata of a .nef image
    metadata = iio.immeta(im_path, plugin="rawpy")
    assert metadata["width"] == 3039
    assert metadata["height"] == 2014
    assert metadata["dtype"] == np.uint16
    assert metadata["raw_width"] == 3040
    assert metadata["raw_height"] == 2014
    assert metadata["raw_shape"] == (2014, 3040)

    #TO DO: Find out what needs to be asserted here.
