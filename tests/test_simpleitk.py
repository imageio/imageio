""" Test simpleitk plugin functionality.
"""

import numpy as np

import pytest
from pytest import raises

import imageio

itk = None
try:
    import itk
except ImportError:
    pass
try:
    if not itk:
        import SimpleITK as itk
except ImportError:
    pass


@pytest.mark.skipif("itk is None")
def test_simpleitk_reading_writing(tmp_path):
    """Test reading and saveing tiff"""
    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = tmp_path / "test_tiff.tiff"

    # One image
    imageio.imsave(filename1, im2, "itk")
    im = imageio.imread(filename1, "itk")
    print(im.shape)
    ims = imageio.mimread(filename1, "itk")
    print(im2.shape)
    assert (im == im2).all()
    assert len(ims) == 1

    # Mixed
    W = imageio.save(filename1, "itk")
    raises(RuntimeError, W.set_meta_data, 1)
    assert W.format.name == "ITK"
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = imageio.read(filename1, "itk")
    assert R.format.name == "ITK"
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    # Fail
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)
    raises(RuntimeError, R.get_meta_data)
