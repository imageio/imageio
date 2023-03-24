""" Test BSDF plugin.
"""


import numpy as np

from pytest import raises
from imageio import core

import imageio.v2 as iio
from imageio.plugins import _bsdf as bsdf

import pytest
import sys
from conftest import deprecated_test

xfail_big_endian = pytest.mark.xfail(
    sys.byteorder == "big", reason="expected failure on big-endian"
)


@deprecated_test
def test_select(test_images):
    F = iio.formats["BSDF"]
    assert F.name == "BSDF"

    fname1 = test_images / "chelsea.bsdf"

    assert F.can_read(core.Request(fname1, "rI"))
    assert F.can_write(core.Request(fname1, "wI"))
    assert F.can_read(core.Request(fname1, "ri"))
    assert F.can_read(core.Request(fname1, "rv"))

    assert type(iio.formats[".bsdf"]) is type(F)
    assert type(iio.formats.search_write_format(core.Request(fname1, "wi"))) is type(F)
    assert type(iio.formats.search_read_format(core.Request(fname1, "ri"))) is type(F)
    assert type(iio.formats.search_write_format(core.Request(fname1, "wI"))) is type(F)
    assert type(iio.formats.search_read_format(core.Request(fname1, "rI"))) is type(F)


def test_not_an_image(tmp_path):
    fname = str(tmp_path / "notanimage.bsdf")

    # Not an image not a list
    bsdf.save(fname, 1)
    with raises(RuntimeError):
        iio.imread(fname)

    # A list with non-images
    bsdf.save(fname, [1])
    with raises(RuntimeError):
        iio.imread(fname)

    # An empty list could work though
    bsdf.save(fname, [])
    with raises(IndexError):
        iio.imread(fname)
    assert iio.mimread(fname) == []


@xfail_big_endian
def test_singleton(test_images, tmp_path):
    im1 = iio.imread(test_images / "chelsea.png")

    fname = str(tmp_path / "chelsea.bsdf")
    iio.imsave(fname, im1)

    # Does it look alright if we open it in bsdf without extensions?
    raw = bsdf.load(fname, [])
    assert isinstance(raw, dict)
    assert set(raw.keys()) == set(["meta", "array"])
    assert isinstance(raw["meta"], dict)
    assert isinstance(raw["array"], dict)
    assert raw["array"]["shape"] == list(im1.shape)
    assert isinstance(raw["array"]["data"], bytes)

    # Read singleton image as singleton
    im2 = iio.imread(fname)
    assert np.all(im1 == im2)

    # Read singleton image as series
    ims = iio.mimread(fname)
    assert len(ims) == 1 and np.all(im1 == ims[0])

    # Read + write back without image extensions
    bsdf.save(fname, bsdf.load(fname))
    im3 = iio.mimread(fname)
    assert np.all(im1 == im3)


@xfail_big_endian
def test_series(test_images, tmp_path):
    im1 = iio.imread(test_images / "chelsea.png")

    ims1 = [im1, im1 * 0.8, im1 * 0.5]

    fname = str(tmp_path / "chelseam.bsdf")
    iio.mimsave(fname, ims1)

    # Does it look alright if we open it in bsdf without extensions?
    raw = bsdf.load(fname, [])
    assert isinstance(raw, list) and len(raw) == 3
    for r in raw:
        assert set(r.keys()) == set(["meta", "array"])
        assert isinstance(r["meta"], dict)
        assert isinstance(r["array"], dict)
        assert r["array"]["shape"] == list(im1.shape)
        assert isinstance(r["array"]["data"], bytes)

    # Read multi-image as singleton
    im2 = iio.imread(fname)
    assert np.all(im1 == im2)

    # Read multi-image as series
    ims2 = iio.mimread(fname)
    assert len(ims2) == 3 and all(np.all(ims1[i] == ims2[i]) for i in range(3))

    # Read + write back without image extensions
    bsdf.save(fname, bsdf.load(fname))
    ims3 = iio.mimread(fname)
    assert len(ims3) == 3 and all(np.all(ims1[i] == ims3[i]) for i in range(3))


@xfail_big_endian
def test_series_unclosed(test_images, tmp_path):
    im1 = iio.imread(test_images / "chelsea.png")
    ims1 = [im1, im1 * 0.8, im1 * 0.5]

    fname = tmp_path / "chelseam.bsdf"
    w = iio.get_writer(fname)
    for im in ims1:
        w.append_data(im)
    w._close = lambda: None  # nope, leave stream open
    w.close()

    # read non-streaming, reads all frames on opening (but skips over blobs
    r = iio.get_reader(fname)
    assert r.get_length() == 3  # not np.inf because not streaming

    # read streaming and get all
    r = iio.get_reader(fname, random_access=False)
    assert r.get_length() == np.inf
    #
    ims2 = [im for im in r]
    assert len(ims2) == 3 and all(np.all(ims1[i] == ims2[i]) for i in range(3))

    # read streaming and read one
    r = iio.get_reader(fname, random_access=False)
    assert r.get_length() == np.inf
    #
    assert np.all(ims1[2] == r.get_data(2))


@xfail_big_endian
def test_random_access(test_images, tmp_path):
    im1 = iio.imread(test_images / "chelsea.png")
    ims1 = [im1, im1 * 0.8, im1 * 0.5]

    fname = tmp_path / "chelseam.bsdf"
    iio.mimsave(fname, ims1)

    r = iio.get_reader(fname)

    for i in (1, 0, 2, 0, 1, 2):
        assert np.all(ims1[i] == r.get_data(i))
    # Note that if we would not get the data of one image in the series,
    # these bytes are never read.


@xfail_big_endian
def test_volume(test_images, tmp_path):
    fname1 = test_images / "stent.npz"
    vol1 = iio.volread(fname1)
    assert vol1.shape == (256, 128, 128)

    fname = tmp_path / "stent.bsdf"
    iio.volsave(fname, vol1)

    vol2 = iio.volread(fname)
    assert vol1.shape == vol2.shape
    assert np.all(vol1 == vol2)


@pytest.mark.needs_internet
def test_from_url(test_images):
    im = iio.imread(
        "https://raw.githubusercontent.com/imageio/"
        + "imageio-binaries/master/images/chelsea.bsdf"
    )
    assert im.shape == (300, 451, 3)

    r = iio.get_reader(
        "https://raw.githubusercontent.com/imageio/"
        + "imageio-binaries/master/images/newtonscradle.bsdf"
    )
    # Can read, as long as its forward
    r.get_data(0)
    r.get_data(10)

    # No rewinding, because we read in streaming mode
    with raises(IndexError):
        r.get_data(9)
