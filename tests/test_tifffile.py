""" Test tifffile plugin functionality.
"""

import os

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio

test_dir = get_test_dir()


def test_tifffile_format():
    
    # Test selection
    for name in ['tiff', '.tif']:
        format = imageio.formats['tiff']
        assert format.name == 'TIFF'


def test_tifffile_reading_writing():
    """ Test reading and saveing tiff """
    im2 = np.ones((10, 10), np.uint8) * 2

    filename1 = os.path.join(test_dir, 'test_tiff.tiff')

    # One image
    imageio.imsave(filename1, im2)
    im = imageio.imread(filename1)
    ims = imageio.mimread(filename1)
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    imageio.mimsave(filename1, [im2, im2, im2])
    im = imageio.imread(filename1)
    ims = imageio.mimread(filename1)
    assert (im == im2).all()
    assert len(ims) == 3, ims[0].shape

    # Mixed
    W = imageio.save(filename1)
    assert W.format.name == 'TIFF'
    W.append_data(im2)
    W.append_data(im2)
    raises(RuntimeError, W.set_meta_data, {})  # no meta data support
    W.close()
    #
    R = imageio.read(filename1)
    assert R.format.name == 'TIFF'
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    # Fail
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)
    raises(RuntimeError, R.get_meta_data, None)  # no meta data support
    raises(RuntimeError, R.get_meta_data, 0)  # no meta data support

run_tests_if_main()
