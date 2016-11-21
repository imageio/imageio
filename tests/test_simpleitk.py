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
    import SimpleITK as itk
except ImportError:
    itk = None


@pytest.mark.skipif('itk is None')
def test_simpleitk_reading_writing():
    """ Test reading and saveing tiff """
    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = os.path.join(test_dir, 'test_tiff.tiff')

    # One image
    imageio.imsave(filename1, im2, 'itk')
    im = imageio.imread(filename1, 'itk')
    ims = imageio.mimread(filename1, 'itk')
    assert (im == im2).all()
    assert len(ims) == 1

    # Mixed
    W = imageio.save(filename1, 'itk')
    raises(RuntimeError, W.set_meta_data, 1)
    assert W.format.name == 'ITK'
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = imageio.read(filename1, 'itk')
    assert R.format.name == 'ITK'
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    # Fail
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)
    raises(RuntimeError, R.get_meta_data)


run_tests_if_main()
