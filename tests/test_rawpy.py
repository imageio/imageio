"""Tests for rawpy plugin
"""

import imageio.v3 as iio

import pytest
import rawpy
import numpy as np


@pytest.mark.parametrize(
    "im_in",
    [
       ("Nikon_uncompressed.nef"),
       ("Blackmagic.dng"), 
    ],
)
def test_im_remote(test_images, im_in):
    """Test for reading .nef file from .test_images dir.
    """
    # Construct image path
    im_path = test_images / im_in

    # Test if plugin's content mathces rawpy content
    actual = iio.imread(im_path, index=..., plugin="rawpy")
    expected = rawpy.imread(str(im_path)).postprocess()
    assert np.allclose(actual, expected)


@pytest.mark.parametrize(
    "im_in",
    [
       ("camera.png"),
       ("bricks.jpg"), 
    ],
)
def test_unsupported_image_type(test_images, im_in):
    """Test for unsupported image file.
    """
    # Construct image path
    im_path = test_images / im_in

    with pytest.raises(Exception):
        iio.imread(im_path, index=..., plugin="rawpy")


def test_write(test_images, tmp_path):
    """Test for writing .nef file from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "Blackmagic.dng"

    # the base image as numpy array
    im_actual = iio.imread(im_path, index=..., plugin="rawpy")
    iio_file = tmp_path / "test.png"
    with pytest.raises(NotImplementedError):
        iio.imwrite(iio_file, im_actual, plugin="rawpy")


def test_iter(test_images):
    """Test for the iter function of rawpy plugin.
    """

    # Construct image path
    im_path = test_images / "Blackmagic.dng"

    assert iio.imiter(im_path, plugin="rawpy")


def test_properties(test_images):
    """Test for reading properties of a raw image from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "Nikon_uncompressed.nef"

    # Test properties of a .nef image
    properties = iio.improps(im_path, plugin="rawpy")
    assert properties.shape == (593, 869)
    assert properties.dtype == np.uint16


def test_metadata(test_images):
    """Test for reading metadata of a raw image from .test_images dir.
    """
    # Construct image path
    im_path = test_images / "Nikon_uncompressed.nef"

    # Test metadata of a .nef image
    metadata = iio.immeta(im_path, plugin="rawpy")
    assert metadata["width"] == 869
    assert metadata["height"] == 593
    assert metadata["dtype"] == np.uint16
    assert metadata["raw_width"] == 869
    assert metadata["raw_height"] == 593
    assert metadata["raw_shape"] == (593, 869, 4)

    #TO DO: Find out what needs to be asserted here.
