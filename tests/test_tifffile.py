""" Test tifffile plugin functionality.
"""

import os
import datetime

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir, need_internet
from imageio.core import get_remote_file

import imageio

test_dir = get_test_dir()


def test_tifffile_format():
    # Test selection
    for name in ["tiff", ".tif"]:
        format = imageio.formats[name]
        assert format.name == "TIFF"


def test_tifffile_reading_writing():
    """Test reading and saving tiff"""

    need_internet()  # We keep a test image in the imageio-binary repo

    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = os.path.join(test_dir, "test_tiff.tiff")

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

    # Read all planes as one array - we call it a volume for clarity
    vol = imageio.volread(filename1)
    vols = imageio.mvolread(filename1)
    assert vol.shape == (3,) + im2.shape
    assert len(vols) == 1 and vol.shape == vols[0].shape
    for i in range(3):
        assert (vol[i] == im2).all()

    # remote multipage rgb file
    filename2 = get_remote_file("images/multipage_rgb.tif")
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
    raises(IndexError, R.get_data, -1)
    raises(IndexError, R.get_data, 3)

    # Ensure imread + imwrite works round trip
    filename3 = os.path.join(test_dir, "test_tiff2.tiff")
    im1 = imageio.imread(filename1)
    imageio.imwrite(filename3, im1)
    im3 = imageio.imread(filename3)
    assert im1.ndim == 3
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Ensure imread + imwrite works round trip - volume like
    filename3 = os.path.join(test_dir, "test_tiff2.tiff")
    im1 = imageio.volread(filename1)
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


run_tests_if_main()
