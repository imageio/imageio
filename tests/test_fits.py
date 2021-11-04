""" Test fits plugin functionality.
"""
import pytest
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio.core import get_remote_file, Request, IS_PYPY

import numpy as np

test_dir = get_test_dir()

try:
    import astropy

    # io is not imported by default
    import astropy.io.fits
except ImportError:
    astropy = None


def setup_module():
    # During this test, pretend that FITS is the default format
    imageio.formats.sort("FITS")


def teardown_module():
    # Set back to normal
    imageio.formats.sort()


@pytest.fixture
def normal_plugin_order():
    # Use fixture to temporarily set context of normal plugin order for
    # tests and return to module setup afterwards
    teardown_module()
    yield
    setup_module()


@pytest.mark.skipif("astropy is None")
def test_fits_format():
    need_internet()  # We keep the fits files in the imageio-binary repo

    # Test selection
    for name in ["fits", ".fits"]:
        format = imageio.formats["fits"]
        assert format.name == "FITS"
        assert format.__module__.endswith(".fits")

    # Test cannot read
    png = get_remote_file("images/chelsea.png")
    assert not format.can_read(Request(png, "ri"))
    assert not format.can_write(Request(png, "wi"))


@pytest.mark.skipif("astropy is None")
def test_fits_reading():
    """Test reading fits"""

    need_internet()  # We keep the fits files in the imageio-binary repo

    if IS_PYPY:
        return  # no support for fits format :(

    simple = get_remote_file("images/simple.fits")
    multi = get_remote_file("images/multi.fits")
    compressed = get_remote_file("images/compressed.fits.fz")

    # One image
    im = imageio.imread(simple, format="fits")
    ims = imageio.mimread(simple, format="fits")
    assert (im == ims[0]).all()
    assert len(ims) == 1

    # Multiple images
    ims = imageio.mimread(multi, format="fits")
    assert len(ims) == 3

    R = imageio.read(multi, format="fits")
    assert R.format.name == "FITS"
    ims = list(R)  # == [im for im in R]
    assert len(ims) == 3

    # Fail
    raises = pytest.raises
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)
    raises(RuntimeError, R.get_meta_data, None)  # no meta data support
    raises(RuntimeError, R.get_meta_data, 0)  # no meta data support

    # Compressed image
    im = imageio.imread(compressed, format="fits")
    assert im.shape == (2042, 3054)


@pytest.mark.skipif("astropy is None")
@pytest.mark.skipif("IS_PYPY", reason="pypy doesn't support astropy.fits.")
def test_fits_get_reader(normal_plugin_order, tmp_path):
    """Test reading fits with get_reader method
    This is a regression test that closes GitHub issue #636
    """

    sigma = 10
    xx, yy = np.meshgrid(np.arange(512), np.arange(512))
    z = (1 / (2 * np.pi * (sigma ** 2))) * np.exp(
        -((xx ** 2) + (yy ** 2)) / (2 * (sigma ** 2))
    )
    img = np.log(z)
    phdu = astropy.io.fits.PrimaryHDU()
    ihdu = astropy.io.fits.ImageHDU(img)
    hdul = astropy.io.fits.HDUList([phdu, ihdu])
    hdul.writeto(tmp_path / "test.fits")
    imageio.get_reader(tmp_path / "test.fits", format="fits")


run_tests_if_main()
