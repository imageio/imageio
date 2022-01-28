""" Test tifffile plugin functionality.
"""

import datetime
import numpy as np
import pytest

import imageio
import imageio as iio

tifffile = pytest.importorskip("tifffile", reason="tifffile is not installed")


def test_tifffile_format():
    # Test selection
    for name in ["tiff", ".tif"]:
        format = imageio.formats[name]
        assert format.name == "TIFF"


def test_tifffile_reading_writing(test_images, tmp_path):
    """Test reading and saving tiff"""

    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = tmp_path / "test_tiff.tiff"

    # One image
    imageio.imsave(filename1, im2)
    im = imageio.imread(filename1)
    ims = imageio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    imageio.mimsave(filename1, [im2, im2, im2])
    im = imageio.imread(filename1)
    ims = imageio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()  # note: this does not imply that the shape match!
    assert len(ims) == 3
    for i in range(3):
        assert ims[i].shape == im2.shape
        assert (ims[i] == im2).all()

    # volumetric data
    imageio.volwrite(filename1, np.tile(im2, (3, 1, 1, 1)))
    vol = imageio.volread(filename1)
    vols = imageio.mvolread(filename1)
    assert vol.shape == (3,) + im2.shape
    assert len(vols) == 1 and vol.shape == vols[0].shape
    for i in range(3):
        assert (vol[i] == im2).all()

    # remote channel-first volume rgb (2, 3, 10, 10)
    filename2 = test_images / "multipage_rgb.tif"
    img = imageio.mimread(filename2)
    assert len(img) == 2
    assert img[0].shape == (3, 10, 10)

    # Mixed
    W = imageio.save(filename1)
    W.set_meta_data({"planarconfig": "SEPARATE"})  # was "planar"
    assert W.format.name == "TIFF"
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = imageio.read(filename1)
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
    im1 = imageio.imread(filename1)
    imageio.imwrite(filename3, im1)
    im3 = imageio.imread(filename3)
    assert im1.ndim == 3
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Ensure imread + imwrite works round trip - volume like
    filename3 = tmp_path / "test_tiff2.tiff"
    im1 = np.stack(imageio.mimread(filename1))
    imageio.volwrite(filename3, im1)
    im3 = imageio.volread(filename3)
    assert im1.ndim == 4
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Read metadata
    md = imageio.get_reader(filename2).get_meta_data()
    assert md["is_imagej"] is None
    assert md["description"] == "shape=(2,3,10,10)"
    assert md["description1"] == ""
    assert md["datetime"] == datetime.datetime(2015, 5, 9, 9, 8, 29)
    assert md["software"] == "tifffile.py"

    # Write metadata
    dt = datetime.datetime(2018, 8, 6, 15, 35, 5)
    with imageio.get_writer(filename1, software="testsoftware") as w:
        w.append_data(
            np.zeros((10, 10)), meta={"description": "test desc", "datetime": dt}
        )
        w.append_data(np.zeros((10, 10)), meta={"description": "another desc"})
    with imageio.get_reader(filename1) as r:
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
        ((100, 200), (100, 200, "INCH")),
        ((0.5, 0.5), (0.5, 0.5, "INCH")),
        (((1, 3), (1, 3)), (1 / 3, 1 / 3, "INCH")),
    ],
)
def test_resolution_metadata(tmp_path, dpi, expected_resolution):
    data = np.zeros((200, 100), dtype=np.uint8)

    writer = imageio.get_writer(tmp_path / "test.tif")
    writer.append_data(data, dict(resolution=dpi))
    writer.close()

    read_image = iio.imread(tmp_path / "test.tif")

    assert read_image.meta["resolution"] == expected_resolution
    assert read_image.meta["resolution_unit"] == 2


def test_read_bytes(tmp_path):
    # regression test for: https://github.com/imageio/imageio/issues/703

    some_bytes = iio.imwrite("<bytes>", [[0]], format="tiff")
    assert some_bytes is not None
