""" Test gdal plugin functionality.
"""
import pytest
import imageio
from imageio.core import get_remote_file

pytest.importorskip("osgeo", reason="gdal is not installed")

@pytest.mark.needs_internet
def test_gdal_reading():
    """Test reading gdal"""

    from osgeo import gdal

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
