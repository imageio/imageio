""" Test fits plugin functionality.
"""
import pytest
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio.core import get_remote_file, Request, IS_PYPY

test_dir = get_test_dir()

try:
    import astropy
except ImportError:
    astropy = None


def setup_module():
    # During this test, pretend that FITS is the default format
    imageio.formats.sort('FITS')


def teardown_module():
    # Set back to normal
    imageio.formats.sort()


@pytest.mark.skipif('astropy is None')
def test_fits_format():
    need_internet()  # We keep the fits files in the imageio-binary repo 

    # Test selection
    for name in ['fits', '.fits']:
        format = imageio.formats['fits']
        assert format.name == 'FITS'
        assert format.__module__.endswith('.fits')

    # Test cannot read
    png = get_remote_file('images/chelsea.png')
    assert not format.can_read(Request(png, 'ri'))
    assert not format.can_write(Request(png, 'wi'))


@pytest.mark.skipif('astropy is None')
def test_fits_reading():
    """ Test reading fits """
    
    need_internet()  # We keep the fits files in the imageio-binary repo 
    
    if IS_PYPY:
        return  # no support for fits format :(

    simple = get_remote_file('images/simple.fits')
    multi = get_remote_file('images/multi.fits')

    # One image
    im = imageio.imread(simple)
    ims = imageio.mimread(simple)
    assert (im == ims[0]).all()
    assert len(ims) == 1

    # Multiple images
    ims = imageio.mimread(multi)
    assert len(ims) == 3

    R = imageio.read(multi)
    assert R.format.name == 'FITS'
    ims = list(R)  # == [im for im in R]
    assert len(ims) == 3

    # Fail
    raises = pytest.raises
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)
    raises(RuntimeError, R.get_meta_data, None)  # no meta data support
    raises(RuntimeError, R.get_meta_data, 0)  # no meta data support


run_tests_if_main()
