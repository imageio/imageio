""" Test fits plugin functionality.
"""
import pytest

import imageio.v2 as iio
from imageio.core import Request

import numpy as np
from conftest import deprecated_test

fits = pytest.importorskip("astropy.io.fits", reason="astropy is not installed")


@deprecated_test
def setup_module():
    # During this test, pretend that FITS is the default format
    iio.formats.sort("FITS")


@deprecated_test
def teardown_module():
    # Set back to normal
    iio.formats.sort()


@pytest.fixture
def normal_plugin_order():
    # Use fixture to temporarily set context of normal plugin order for
    # tests and return to module setup afterwards
    teardown_module()
    yield
    setup_module()


@deprecated_test
def test_fits_format(test_images):
    # Test selection
    for name in ["fits", ".fits"]:
        format = iio.formats["fits"]
        assert format.name == "FITS"
        assert format.__module__.endswith(".fits")

    # Test cannot read
    png = test_images / "chelsea.png"
    assert not format.can_read(Request(png, "ri"))
    assert not format.can_write(Request(png, "wi"))


def test_fits_reading(test_images):
    """Test reading fits"""

    simple = test_images / "simple.fits"
    multi = test_images / "multi.fits"
    compressed = test_images / "compressed.fits.fz"

    # One image
    im = iio.imread(simple, format="fits")
    ims = iio.mimread(simple, format="fits")
    assert (im == ims[0]).all()
    assert len(ims) == 1

    # Multiple images
    ims = iio.mimread(multi, format="fits")
    assert len(ims) == 3

    R = iio.read(multi, format="fits")
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
    im = iio.imread(compressed, format="fits")
    assert im.shape == (2042, 3054)


def test_fits_get_reader(normal_plugin_order, tmp_path):
    """Test reading fits with get_reader method
    This is a regression test that closes GitHub issue #636
    """

    sigma = 10
    xx, yy = np.meshgrid(np.arange(512), np.arange(512))
    z = (1 / (2 * np.pi * (sigma**2))) * np.exp(
        -((xx**2) + (yy**2)) / (2 * (sigma**2))
    )
    img = np.log(z, where=z != 0, out=np.zeros_like(z))
    phdu = fits.PrimaryHDU()
    ihdu = fits.ImageHDU(img)
    hdul = fits.HDUList([phdu, ihdu])
    hdul.writeto(tmp_path / "test.fits")
    iio.get_reader(tmp_path / "test.fits", format="fits")
