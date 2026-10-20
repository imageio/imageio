"""Test gdal plugin functionality."""

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


def test_gdal_rejects_vrt(tmp_path):
    """A VRT disguised as a .tif must not be opened (no file disclosure/SSRF)."""

    secret = tmp_path / "secret.txt"
    secret.write_bytes(b"TOP-SECRET-CONTENTS-0123456789\n")

    evil = tmp_path / "evil.tif"
    evil.write_text(
        '<VRTDataset rasterXSize="31" rasterYSize="1">'
        '<VRTRasterBand dataType="Byte" band="1" subClass="VRTRawRasterBand">'
        f'<SourceFilename relativetoVRT="0">{secret}</SourceFilename>'
        "<ImageOffset>0</ImageOffset><PixelOffset>1</PixelOffset>"
        "<LineOffset>31</LineOffset></VRTRasterBand></VRTDataset>"
    )

    with pytest.raises(RuntimeError):
        imageio.imread(evil, "gdal")
