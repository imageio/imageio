""" Test tifffile plugin functionality.
"""

import datetime
import numpy as np
import pytest

import imageio.v2 as iio
from conftest import deprecated_test

tifffile = pytest.importorskip("tifffile", reason="tifffile is not installed")


@deprecated_test
def test_tifffile_format():
    # Test selection
    for name in ["tiff", ".tif"]:
        format = iio.formats[name]
        assert format.name == "TIFF"


def test_tifffile_reading_writing(test_images, tmp_path):
    """Test reading and saving tiff"""

    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = tmp_path / "test_tiff.tiff"

    # One image
    iio.imsave(filename1, im2)
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    iio.mimsave(filename1, [im2, im2, im2])
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()  # note: this does not imply that the shape match!
    assert len(ims) == 3
    for i in range(3):
        assert ims[i].shape == im2.shape
        assert (ims[i] == im2).all()

    # volumetric data
    iio.volwrite(filename1, np.tile(im2, (3, 1, 1, 1)))
    vol = iio.volread(filename1)
    vols = iio.mvolread(filename1)
    assert vol.shape == (3,) + im2.shape
    assert len(vols) == 1 and vol.shape == vols[0].shape
    for i in range(3):
        assert (vol[i] == im2).all()

    # remote channel-first volume rgb (2, 3, 10, 10)
    filename2 = test_images / "multipage_rgb.tif"
    img = iio.mimread(filename2)
    assert len(img) == 2
    assert img[0].shape == (3, 10, 10)

    # Mixed
    W = iio.save(filename1)
    W.set_meta_data({"planarconfig": "SEPARATE"})  # was "planar"
    assert W.format.name == "TIFF"
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = iio.read(filename1)
    assert R.format.name == "TIFF"
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    # meta = R.get_meta_data()
    # assert meta['orientation'] == 'top_left'  # not there in later version
    # Fail
    with pytest.raises(IndexError):
        R.get_data(-1)

    with pytest.raises(IndexError):
        R.get_data(3)

    # Ensure imread + imwrite works round trip
    filename3 = tmp_path / "test_tiff2.tiff"
    im1 = iio.imread(filename1)
    iio.imwrite(filename3, im1)
    im3 = iio.imread(filename3)
    assert im1.ndim == 3
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Ensure imread + imwrite works round trip - volume like
    filename3 = tmp_path / "test_tiff2.tiff"
    im1 = np.stack(iio.mimread(filename1))
    iio.volwrite(filename3, im1)
    im3 = iio.volread(filename3)
    assert im1.ndim == 4
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Read metadata
    md = iio.get_reader(filename2).get_meta_data()
    assert md["is_imagej"] is None
    assert md["description"] == "shape=(2,3,10,10)"
    assert md["description1"] == ""
    assert md["datetime"] == datetime.datetime(2015, 5, 9, 9, 8, 29)
    assert md["software"] == "tifffile.py"

    # Write metadata
    dt = datetime.datetime(2018, 8, 6, 15, 35, 5)
    with iio.get_writer(filename1, software="testsoftware") as w:
        w.append_data(
            np.zeros((10, 10)), meta={"description": "test desc", "datetime": dt}
        )
        w.append_data(np.zeros((10, 10)), meta={"description": "another desc"})
    with iio.get_reader(filename1) as r:
        for md in r.get_meta_data(), r.get_meta_data(0):
            assert "datetime" in md
            assert md["datetime"] == dt
            assert "software" in md
            assert md["software"] == "testsoftware"
            assert "description" in md
            assert md["description"] == "test desc"

        md = r.get_meta_data(1)
        assert "description" in md
        assert md["description"] == "another desc"


def test_imagej_hyperstack(tmp_path):
    # create artifical hyperstack

    tifffile.imwrite(
        tmp_path / "hyperstack.tiff",
        np.zeros((15, 2, 180, 183), dtype=np.uint8),
        imagej=True,
    )

    # test ImageIO plugin
    img = iio.volread(tmp_path / "hyperstack.tiff", format="TIFF")
    assert img.shape == (15, 2, 180, 183)


@pytest.mark.parametrize(
    "dpi,expected_resolution",
    [
        ((0, 1), (0, 1, "INCH")),
        ((0, 12), (0, 12, "INCH")),
        ((100, 200), (100, 200, "INCH")),
        ((0.5, 0.5), (0.5, 0.5, "INCH")),
        (((1, 3), (1, 3)), (1 / 3, 1 / 3, "INCH")),
    ],
)
def test_resolution_metadata(tmp_path, dpi, expected_resolution):
    data = np.zeros((200, 100), dtype=np.uint8)

    writer = iio.get_writer(tmp_path / "test.tif")
    writer.append_data(data, dict(resolution=dpi))
    writer.close()

    read_image = iio.imread(tmp_path / "test.tif")

    assert read_image.meta["resolution"] == expected_resolution
    assert read_image.meta["resolution_unit"] == 2


@pytest.mark.parametrize("resolution", [(1, 0), (0, 0)])
def test_invalid_resolution_metadata(tmp_path, resolution):
    data = np.zeros((200, 100), dtype=np.uint8)

    tif_path = tmp_path / "test.tif"

    writer = iio.get_writer(tif_path)
    writer.append_data(data)
    writer.close()
    # Overwrite low level metadata the exact way we want it
    # to avoid any re-interpretation of the metadata by imageio
    # For example, it seems that (0, 0) gets rewritten as (0, 1)
    with tifffile.TiffFile(tif_path, mode="r+b") as tif:
        tags = tif.pages[0].tags
        tags["XResolution"].overwrite(resolution)
        tags["YResolution"].overwrite(resolution)

    # Validate with low level library that the invalid metadata is written
    with tifffile.TiffFile(tif_path, mode="rb") as tif:
        tags = tif.pages[0].tags
        assert tags["XResolution"].value == resolution
        assert tags["YResolution"].value == resolution

    with pytest.warns(RuntimeWarning):
        read_image = iio.imread(tmp_path / "test.tif")

    assert "resolution" not in read_image.meta


def test_read_bytes(tmp_path):
    # regression test for: https://github.com/imageio/imageio/issues/703

    some_bytes = iio.imwrite("<bytes>", [[0]], format="tiff")
    assert some_bytes is not None
