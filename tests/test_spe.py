from datetime import datetime

import numpy as np
import pytest

import imageio.v3 as iio
from imageio.plugins import spe


frame0 = np.zeros((32, 32), np.uint16)
frame1 = np.ones_like(frame0)


def test_imopen(test_images):
    img = iio.imopen(test_images / "test_000_.SPE", "r")
    assert isinstance(img, spe.SpePlugin)


def test_read(test_images):
    fname = test_images / "test_000_.SPE"

    im = iio.imread(fname, index=0)
    np.testing.assert_equal(im, frame0)

    ims = iio.imread(fname, index=...)
    np.testing.assert_equal(ims, [frame0, frame1])

    with pytest.raises(IndexError):
        iio.imread(fname, index=-1)
    with pytest.raises(IndexError):
        iio.imread(fname, index=2)


def test_iter(test_images):
    for actual, desired in zip(iio.imiter(test_images / "test_000_.SPE"),
                               (frame0, frame1)):
        np.testing.assert_equal(actual, desired)


def test_metadata(test_images):
    fname = test_images / "test_000_.SPE"
    md = iio.immeta(fname, sdt_control=False)
    assert md["ROIs"] == [
        {"top_left": [238, 187], "bottom_right": [269, 218], "bin": [1, 1]}
    ]
    cmt = [
        "OD 1.0 in r, g                                                    "
        "              ",
        "000200000000000004800000000000000000000000000000000000000000000000"
        "0002000001000X",
        "                                                                  "
        "              ",
        "                                                                  "
        "              ",
        "ACCI2xSEQU-1---10000010001600300EA                              SW"
        "0218COMVER0500",
    ]
    assert md["comments"] == cmt

    sdt_meta = iio.immeta(fname, sdt_control=True)
    assert sdt_meta["delay_shutter"] == pytest.approx(0.001)
    assert sdt_meta["delay_macro"] == pytest.approx(0.048)
    assert sdt_meta["exposure_time"] == pytest.approx(0.002)
    assert sdt_meta["comment"] == "OD 1.0 in r, g"
    assert sdt_meta["datetime"] == datetime(2018, 7, 2, 9, 46, 15)
    assert sdt_meta["sdt_major_version"] == 2
    assert sdt_meta["sdt_minor_version"] == 18
    assert isinstance(sdt_meta["modulation_script"], str)
    assert sdt_meta["sequence_type"] == "standard"


def test_properties(test_images):
    fname = test_images / "test_000_.SPE"
    props0 = iio.improps(fname, index=0)
    assert props0.shape == (32, 32)
    assert props0.dtype == np.uint16
    assert props0.is_batch == False

    props = iio.improps(fname, index=...)
    assert props.shape == (2, 32, 32)
    assert props.dtype == np.uint16
    assert props.is_batch == True
