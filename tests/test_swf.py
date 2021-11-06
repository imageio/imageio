""" Tests for the shockwave flash plugin
"""

import os

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import get_remote_file, IS_PYPY


test_dir = get_test_dir()


def mean(x):
    return x.sum() / x.size  # pypy-compat mean


# We use need_internet; don't ship the swf image: its rather big and a
# rather specific format


def test_format_selection():

    need_internet()

    fname1 = get_remote_file("images/stent.swf", test_dir)
    fname2 = fname1[:-4] + ".out.swf"

    F = imageio.formats["swf"]
    assert F.name == "SWF"
    assert type(imageio.formats[".swf"]) is type(F)

    assert type(imageio.read(fname1).format) is type(F)
    assert type(imageio.save(fname2).format) is type(F)


def test_reading_saving():

    need_internet()

    fname1 = get_remote_file("images/stent.swf", test_dir)
    fname2 = fname1[:-4] + ".out.swf"
    fname3 = fname1[:-4] + ".compressed.swf"
    fname4 = fname1[:-4] + ".out2.swf"

    # Read
    R = imageio.read(fname1)
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
    raises(IndexError, R.get_data, -1)  # No negative index
    raises(IndexError, R.get_data, 10)  # Out of bounds
    R.close()

    # Test loop
    R = imageio.read(fname1, loop=True)
    assert (R.get_data(10) == ims1[0]).all()

    # setting meta data is ignored
    W = imageio.save(fname2)
    W.set_meta_data({"foo": 3})
    W.close()

    # Just make sure mimread works
    assert len(imageio.mimread(fname1)) == 10

    # I'm not sure why, but the below does not work on pypy, which is weird,
    # because the file *is* closed, but somehow it's not flushed? Ah well ...
    if IS_PYPY:
        return

    # Write and re-read, now without loop, and with html page
    imageio.mimsave(fname2, ims1, loop=False, html=True)
    ims2 = imageio.mimread(fname2)

    # Check images. We can expect exact match, since
    # SWF is lossless.
    assert len(ims1) == len(ims2)
    for im1, im2 in zip(ims1, ims2):
        assert (im1 == im2).all()

    # Test compressed
    imageio.mimsave(fname3, ims2, compress=True)
    ims3 = imageio.mimread(fname3)
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

    with open(os.path.join(test_dir, "test_swf.html"), "wb") as f:
        for line in html.splitlines():
            f.write(line.strip().encode("utf-8") + b"\n")


def test_read_from_url():

    need_internet()

    burl = "https://raw.githubusercontent.com/imageio/imageio-binaries/master/"
    url = burl + "images/stent.swf"

    ims = imageio.mimread(url)
    assert len(ims) == 10


def test_invalid():

    need_internet()

    fname1 = get_remote_file("images/stent.swf", test_dir)
    fname2 = fname1[:-4] + ".invalid.swf"

    # Empty file
    with open(fname2, "wb"):
        pass
    assert not imageio.formats.search_read_format(core.Request(fname2, "rI"))
    raises(RuntimeError, imageio.mimread, fname2, "swf")

    # File with BS data
    with open(fname2, "wb") as f:
        f.write(b"x" * 100)
    assert not imageio.formats.search_read_format(core.Request(fname2, "rI"))
    raises(RuntimeError, imageio.mimread, fname2, "swf")


def test_lowlevel():

    need_internet()

    # Some tests from low level implementation that is not covered
    # by using the plugin itself.
    _swf = imageio.plugins.swf.load_lib()
    tag = _swf.Tag()
    raises(NotImplementedError, tag.process_tag)
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


def test_types():

    need_internet()

    fname1 = get_remote_file("images/stent.swf", test_dir)
    fname2 = fname1[:-4] + ".out3.swf"

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
            imageio.mimsave(fname2, [im1], "swf")
            im2 = imageio.mimread(fname2, "swf")[0]
            assert im2.shape == (100, 100, 4)
            assert im2.dtype == np.uint8
            if len(shape) == 3 and dtype == np.uint8:
                assert (im1[:, :, 0] == im2[:, :, 0]).all()


run_tests_if_main()
