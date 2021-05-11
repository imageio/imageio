""" Test gdal plugin functionality.
"""
import pytest
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio.core import get_remote_file

test_dir = get_test_dir()


try:
    from osgeo import gdal
except ImportError:
    gdal = None


@pytest.mark.skipif("gdal is None")
def test_gdal_reading():
    """Test reading gdal"""
    need_internet()

    filename = get_remote_file("images/geotiff.tif")

    im = imageio.imread(filename, "gdal")
    assert im.shape == (929, 699)

    R = imageio.read(filename, "gdal")
    assert R.format.name == "GDAL"
    meta_data = R.get_meta_data()
    assert "TIFFTAG_XRESOLUTION" in meta_data

    # Fail
    raises = pytest.raises
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)


run_tests_if_main()
