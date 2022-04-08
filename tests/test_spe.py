from datetime import datetime

import numpy as np
import pytest

import imageio.v2 as iio
from imageio.plugins import spe
from conftest import deprecated_test


@deprecated_test
def test_spe_format():
    for name in ("spe", ".spe"):
        fmt = iio.formats[name]
        assert isinstance(fmt, spe.SpeFormat)


def test_spe_reading(test_images):
    fname = test_images / "test_000_.SPE"

    fr1 = np.zeros((32, 32), np.uint16)
    fr2 = np.ones_like(fr1)

    # Test imread
    im = iio.imread(fname)
    ims = iio.mimread(fname)

    np.testing.assert_equal(im, fr1)
    np.testing.assert_equal(ims, [fr1, fr2])

    # Test volread
    vol = iio.volread(fname)
    vols = iio.mvolread(fname)

    np.testing.assert_equal(vol, [fr1, fr2])
    np.testing.assert_equal(vols, [[fr1, fr2]])

    # Test get_reader
    r = iio.get_reader(fname, sdt_meta=False)

    np.testing.assert_equal(r.get_data(1), fr2)
    np.testing.assert_equal(list(r), [fr1, fr2])
    pytest.raises(IndexError, r.get_data, -1)
    pytest.raises(IndexError, r.get_data, 2)

    # check metadata
    md = r.get_meta_data()
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
    np.testing.assert_equal(md["frame_shape"], fr1.shape)

    # Check reading SDT-control metadata
    with iio.get_reader(fname) as r2:
        sdt_meta = r2.get_meta_data()

    assert sdt_meta["delay_shutter"] == pytest.approx(0.001)
    assert sdt_meta["delay_macro"] == pytest.approx(0.048)
    assert sdt_meta["exposure_time"] == pytest.approx(0.002)
    assert sdt_meta["comment"] == "OD 1.0 in r, g"
    assert sdt_meta["datetime"] == datetime(2018, 7, 2, 9, 46, 15)
    assert sdt_meta["sdt_major_version"] == 2
    assert sdt_meta["sdt_minor_version"] == 18
    assert isinstance(sdt_meta["modulation_script"], str)
    assert sdt_meta["sequence_type"] == "standard"
