""" Test simpleitk plugin functionality.
"""

import os

import numpy as np

import pytest
from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio

test_dir = get_test_dir()


try:
    import SimpleITK as sitk
except ImportError:
    sitk = None


@pytest.mark.skipif('sitk is None')
def test_simpleitk_reading_writing():
    """ Test reading and saveing tiff """
    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = os.path.join(test_dir, 'test_tiff.tiff')

    # One image
    imageio.imsave(filename1, im2, 'simpleitk')
    im = imageio.imread(filename1, 'simpleitk')
    ims = imageio.mimread(filename1, 'simpleitk')
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    imageio.mimsave(filename1, [im2, im2, im2], 'simpleitk')
    im = imageio.imread(filename1, 'simpleitk')
    ims = imageio.mimread(filename1, 'simpleitk')
    assert (im == im2).all()
    assert len(ims) == 3, ims[0].shape

    # Mixed
    W = imageio.save(filename1, 'simpleitk')
    raises(RuntimeError, W.set_metadata, 1)
    assert W.format.name == 'SIMPLEITK'
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = imageio.read(filename1, 'simpleitk')
    assert R.format.name == 'SIMPLEITK'
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    meta = R.get_meta_data()
    assert meta['is_rgb']
    # Fail
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)

run_tests_if_main()
