""" Test npz plugin functionality.
"""

import pytest

import numpy as np

import imageio.v2 as iio
from imageio.core import Request, IS_PYPY
from conftest import deprecated_test


@deprecated_test
def test_npz_format(test_images):
    # Test selection
    for name in ["npz", ".npz"]:
        format = iio.formats["npz"]
        assert format.name == "NPZ"
        assert format.__module__.endswith(".npz")

    # Test cannot read
    png = test_images / "chelsea.png"
    assert not format.can_read(Request(png, "ri"))
    assert not format.can_write(Request(png, "wi"))


def test_npz_reading_writing(tmp_path):
    """Test reading and saveing npz"""

    if IS_PYPY:
        return  # no support for npz format :(

    im2 = np.ones((10, 10), np.uint8) * 2
    im3 = np.ones((10, 10, 10), np.uint8) * 3
    im4 = np.ones((10, 10, 10, 10), np.uint8) * 4

    filename1 = tmp_path / "test_npz.npz"

    # One image
    iio.imsave(filename1, im2)
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    iio.mimsave(filename1, [im2, im2, im2])
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert (im == im2).all()
    assert len(ims) == 3

    # Volumes
    iio.mvolsave(filename1, [im3, im3])
    im = iio.volread(filename1)
    ims = iio.mvolread(filename1)
    assert (im == im3).all()
    assert len(ims) == 2

    # Mixed
    W = iio.save(filename1)
    assert W.format.name == "NPZ"
    W.append_data(im2)
    W.append_data(im3)
    W.append_data(im4)
    pytest.raises(RuntimeError, W.set_meta_data, {})  # no meta data support
    W.close()
    #
    R = iio.read(filename1)
    assert R.format.name == "NPZ"
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    assert (ims[1] == im3).all()
    assert (ims[2] == im4).all()
    # Fail
    pytest.raises(IndexError, R.get_data, -1)
    pytest.raises(IndexError, R.get_data, 3)
    pytest.raises(RuntimeError, R.get_meta_data, None)  # no meta data support
    pytest.raises(RuntimeError, R.get_meta_data, 0)  # no meta data support
