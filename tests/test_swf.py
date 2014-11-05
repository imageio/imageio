
import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio
from imageio import core
from imageio.core import get_remote_file


test_dir = get_test_dir()


def test_format_selection():
    
    fname1 = get_remote_file('images/stent.swf', test_dir)
    fname2 = fname1[:-4] + '.out.swf'
    
    F = imageio.formats['swf']
    assert F.name == 'SWF'
    assert imageio.formats['.swf'] is F
    
    assert imageio.read(fname1).format is F
    assert imageio.save(fname2).format is F


def test_reading_saving():
    
    fname1 = get_remote_file('images/stent.swf', test_dir)
    fname2 = fname1[:-4] + '.out.swf'
    
    # Read
    R = imageio.read(fname1)
    ims1 = []
    for im in R:
        assert im.shape == (657, 451, 4)
        assert im.mean() > 0
        ims1.append(im)
    R.close()
    
    # Write
    imageio.mimsave(fname2, ims1)
    
    # Read again
    R = imageio.read(fname2)
    ims2 = []
    for im in R:
        assert im.shape == (657, 451, 4)
        assert im.mean() > 0
        ims2.append(im)
    R.close()
    
    # Check images. We can expect exact match, since
    # SWF is lossless.
    for im1, im2 in zip(ims1, ims2):
        assert (im1 == im2).all()


run_tests_if_main()
