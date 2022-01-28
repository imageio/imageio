""" Test gdal plugin functionality.
"""
import pytest
import imageio

pytest.importorskip("osgeo", reason="gdal is not installed")


def test_gdal_reading(test_images):
    """Test reading gdal"""

    filename = test_images / "geotiff.tif"

    im = imageio.imread(filename, "gdal")
    assert im.shape == (929, 699)

    R = imageio.read(filename, "gdal")
    assert R.format.name == "GDAL"
    meta_data = R.get_meta_data()
    assert "TIFFTAG_XRESOLUTION" in meta_data

    # Fail
    with pytest.raises(IndexError):
        R.get_data(-1)
    with pytest.raises(IndexError):
        R.get_data(3)
