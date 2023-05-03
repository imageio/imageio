from datetime import datetime
import os
import shutil
import struct

import numpy as np
import pytest

import imageio.v3 as iio
from imageio.plugins import spe


frame0 = np.zeros((32, 32), np.uint16)
frame1 = np.ones_like(frame0)


def test_imopen(test_images, tmp_path):
    with iio.imopen(test_images / "test_000_.SPE", "r") as img:
        assert isinstance(img, spe.SpePlugin)

    with pytest.raises(OSError):
        iio.imopen(tmp_path / "test.spe", "w", plugin="SPE")

    with open(tmp_path / "stub.spe", "wb") as f:
        f.write(b"\x00\x01\x02\x03")
    with pytest.raises(OSError):
        iio.imopen(tmp_path / "stub.spe", "r", plugin="SPE")


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
    for actual, desired in zip(
        iio.imiter(test_images / "test_000_.SPE"), (frame0, frame1)
    ):
        np.testing.assert_equal(actual, desired)


def test_metadata(test_images, tmp_path):
    fname = test_images / "test_000_.SPE"
    meta = iio.immeta(fname, sdt_control=False)
    with pytest.deprecated_call():
        meta2 = iio.imopen(fname, "r", sdt_meta=False).metadata()
    for md in (meta, meta2):
        assert md.get("ROIs") == [
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
        assert md.get("comments") == cmt
        assert md.get("geometric") == []
        assert md.get("type", "") is None
        assert md.get("readout_mode", "") is None

    sdt_meta = iio.immeta(fname, sdt_control=True)
    with pytest.deprecated_call():
        sdt_meta2 = iio.imopen(fname, "r", sdt_meta=True).metadata()
    for md in (sdt_meta, sdt_meta2):
        assert md.get("delay_shutter") == pytest.approx(0.001)
        assert md.get("delay_macro") == pytest.approx(0.048)
        assert md.get("exposure_time") == pytest.approx(0.002)
        assert md.get("comment") == "OD 1.0 in r, g"
        assert md.get("datetime") == datetime(2018, 7, 2, 9, 46, 15)
        assert md.get("sdt_major_version") == 2
        assert md.get("sdt_minor_version") == 18
        assert isinstance(md.get("modulation_script"), str)
        assert md.get("sequence_type") == "standard"

    patched = tmp_path / fname.name
    shutil.copy(fname, patched)
    with patched.open("r+b") as f:
        # Set SDT-control comment version to 0400. In this case, comments
        # should not be parsed.
        f.seek(597)
        f.write(b"4")
        # Add something to `geometric`
        f.seek(600)
        f.write(struct.pack("<H", 7))
        # Set `type`
        f.seek(704)
        f.write(struct.pack("<h", 1))
        # Set `readout_mode`
        f.seek(1480)
        f.write(struct.pack("<H", 2))

    patched_cmt = cmt.copy()
    patched_cmt[4] = patched_cmt[4].replace("COMVER0500", "COMVER0400")

    patched_meta = iio.immeta(patched, sdt_control=True)
    # Parsing any SDT-control metadata should fail
    assert patched_meta.get("comments") == patched_cmt
    assert "delay_shutter" not in patched_meta
    assert patched_meta.get("geometric") == ["rotate", "reverse", "flip"]
    assert patched_meta.get("type", "") == "new120 (Type II)"
    assert patched_meta.get("readout_mode", "") == "frame transfer"

    shutil.copy(fname, patched)
    with patched.open("r+b") as f:
        # Set SDT-control sequence type to something invalid.
        f.seek(526)
        f.write(b"INVA")
        # Change date to something invalid.
        f.seek(20)
        f.write(b"02Inv2018")
        # Add non-ASCII character to laser modulation script
        f.seek(745)
        f.write(b"\xff")
        # Add non-ASCII character to `sw_version`
        f.seek(690)
        f.write(b"\xff")

    patched_meta = iio.immeta(patched, sdt_control=True, char_encoding="ascii")
    # Decoding `sequence_type` should fail
    assert patched_meta.get("sequence_type", "") is None
    # Decoding `date` and `time_local` into `datetime` should fail
    assert patched_meta.get("date") == "02Inv2018"
    assert "datetime" not in patched_meta
    # Decoding `spare_4` into `modulation_script` should fail
    assert "modulation_script" not in patched_meta
    assert isinstance(patched_meta.get("spare_4"), bytes)
    # Decoding `sw_version` should fail
    assert isinstance(patched_meta.get("sw_version"), bytes)

    with pytest.deprecated_call():
        patched_meta2 = iio.imopen(
            patched, "r", sdt_meta=True, char_encoding="ascii"
        ).metadata()
    assert patched_meta2.get("sequence_type", "") is None

    shutil.copy(fname, patched)
    with patched.open("r+b") as f:
        # Create a fake SPE v3 file
        f.seek(1992)
        f.write(struct.pack("<f", 3.0))
        f.seek(0, os.SEEK_END)
        sz = f.tell()
        f.write(b"Here could be your XML.")
        f.seek(678)
        f.write(struct.pack("<Q", sz))

    patched_meta = iio.immeta(patched)
    assert patched_meta == {"__xml": b"Here could be your XML."}


def test_properties(test_images, tmp_path):
    fname = test_images / "test_000_.SPE"
    props0 = iio.improps(fname, index=0)
    assert props0.shape == (32, 32)
    assert props0.dtype == np.uint16
    assert props0.n_images is None
    assert not props0.is_batch

    props = iio.improps(fname, index=...)
    assert props.shape == (2, 32, 32)
    assert props.dtype == np.uint16
    assert props.n_images == 2
    assert props.is_batch

    patched = tmp_path / fname.name
    shutil.copy(fname, patched)
    with patched.open("r+b") as f:
        # Set incorrect number of images
        f.seek(1446)
        f.write(struct.pack("<i", 3))

    # Test `check_filesize`
    with iio.imopen(patched, "r", check_filesize=False) as img:
        assert (
            img.properties(
                index=...,
            ).n_images
            == 3
        )
    with iio.imopen(patched, "r", check_filesize=True) as img:
        assert (
            img.properties(
                index=...,
            ).n_images
            == 2
        )
