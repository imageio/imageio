""" Tests for the shockwave flash plugin
"""

import numpy as np

import pytest

import imageio.v2 as iio
import imageio.plugins
from imageio import core
from imageio.core import IS_PYPY
from conftest import deprecated_test


def mean(x):
    return x.sum() / x.size  # pypy-compat mean


@deprecated_test
def test_format_selection(test_images, tmp_path):
    fname1 = test_images / "stent.swf"
    fname2 = tmp_path / "stent.out.swf"

    F = iio.formats["swf"]
    assert F.name == "SWF"
    assert type(iio.formats[".swf"]) is type(F)

    assert type(iio.read(fname1).format) is type(F)
    assert type(iio.save(fname2).format) is type(F)


def test_reading_saving(test_images, tmp_path):
    fname1 = test_images / "stent.swf"
    fname2 = tmp_path / "stent.out.swf"
    fname3 = tmp_path / "stent.compressed.swf"
    fname4 = tmp_path / "stent.out2.swf"

    # Read
    R = iio.read(fname1)
    assert len(R) == 10
    assert R.get_meta_data() == {}  # always empty dict
    ims1 = []
    for im in R:
        assert im.shape == (657, 451, 4)
        assert mean(im) > 0
        ims1.append(im)
    # Seek
    assert (R.get_data(3) == ims1[3]).all()
    # Fails
    with pytest.raises(IndexError):
        R.get_data(-1)  # No negative index

    with pytest.raises(IndexError):
        R.get_data(10)  # Out of bounds
    R.close()

    # Test loop
    R = iio.read(fname1, loop=True)
    assert (R.get_data(10) == ims1[0]).all()

    # setting meta data is ignored
    W = iio.save(fname2)
    W.set_meta_data({"foo": 3})
    W.close()

    # Just make sure mimread works
    assert len(iio.mimread(fname1)) == 10

    # I'm not sure why, but the below does not work on pypy, which is weird,
    # because the file *is* closed, but somehow it's not flushed? Ah well ...
    if IS_PYPY:
        return

    # Write and re-read, now without loop, and with html page
    iio.mimsave(fname2, ims1, loop=False, html=True)
    ims2 = iio.mimread(fname2)

    # Check images. We can expect exact match, since
    # SWF is lossless.
    assert len(ims1) == len(ims2)
    for im1, im2 in zip(ims1, ims2):
        assert (im1 == im2).all()

    # Test compressed
    iio.mimsave(fname3, ims2, compress=True)
    ims3 = iio.mimread(fname3)
    assert len(ims1) == len(ims3)
    for im1, im3 in zip(ims1, ims3):
        assert (im1 == im3).all()

    # Test conventional, Bonus, we don't officially support this.
    _swf = imageio.plugins.swf.load_lib()
    _swf.write_swf(fname4, ims1)
    ims4 = _swf.read_swf(fname4)
    assert len(ims1) == len(ims4)
    for im1, im4 in zip(ims1, ims4):
        assert (im1 == im4).all()

    # We want to manually validate that this file plays in 3d party tools
    # So we write a small HTML5 doc that we can load
    html = """<!DOCTYPE html>
            <html>
            <body>
            Original:
            <embed src="%s">
            <br ><br >
            Written:
            <embed src="%s">
            <br ><br >
            Compressed:
            <embed src="%s">
            <br ><br >
            Written 2:
            <embed src="%s">
            </body>
            </html>
            """ % (
        fname1,
        fname2,
        fname3,
        fname4,
    )

    with open(tmp_path / "test_swf.html", "wb") as f:
        for line in html.splitlines():
            f.write(line.strip().encode("utf-8") + b"\n")


@pytest.mark.needs_internet
def test_read_from_url():
    burl = "https://raw.githubusercontent.com/imageio/imageio-binaries/master/"
    url = burl + "images/stent.swf"

    ims = iio.mimread(url)
    assert len(ims) == 10


@deprecated_test
def test_invalid(test_images, tmp_path):
    fname2 = tmp_path / "stent.invalid.swf"

    # Empty file
    with open(fname2, "wb"):
        pass
    assert not iio.formats.search_read_format(core.Request(fname2, "rI"))
    with pytest.raises(RuntimeError):
        iio.mimread(fname2, "swf")

    # File with BS data
    with open(fname2, "wb") as f:
        f.write(b"x" * 100)
    assert not iio.formats.search_read_format(core.Request(fname2, "rI"))
    with pytest.raises(RuntimeError):
        iio.mimread(fname2, "swf")


@pytest.mark.needs_internet
def test_lowlevel():
    # Some tests from low level implementation that is not covered
    # by using the plugin itself.
    _swf = imageio.plugins.swf.load_lib()
    tag = _swf.Tag()
    with pytest.raises(NotImplementedError):
        tag.process_tag()
    assert tag.make_matrix_record() == "00000000"
    assert tag.make_matrix_record(scale_xy=(1, 1))
    assert tag.make_matrix_record(rot_xy=(1, 1))
    assert tag.make_matrix_record(trans_xy=(1, 1))

    SetBackgroundTag = _swf.SetBackgroundTag
    assert SetBackgroundTag(1, 2, 3).rgb == SetBackgroundTag((1, 2, 3)).rgb

    tag = _swf.ShapeTag(0, (0, 0), (1, 1))
    assert tag.make_style_change_record(1, 1, (1, 1))
    assert tag.make_style_change_record()
    assert (
        tag.make_straight_edge_record(2, 3).tobytes()
        == tag.make_straight_edge_record((2, 3)).tobytes()
    )


def test_types(test_images, tmp_path):
    fname2 = tmp_path / "stent.out3.swf"

    for dtype in [
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.float16,
        np.float32,
        np.float64,
    ]:
        for shape in [(100, 1), (100, 3)]:
            # Repeats an identity matrix, just for testing
            im1 = np.dstack((np.identity(shape[0], dtype=dtype),) * shape[1])
            iio.mimsave(fname2, [im1], "swf")
            im2 = iio.mimread(fname2, "swf")[0]
            assert im2.shape == (100, 100, 4)
            assert im2.dtype == np.uint8
            if len(shape) == 3 and dtype == np.uint8:
                assert (im1[:, :, 0] == im2[:, :, 0]).all()
