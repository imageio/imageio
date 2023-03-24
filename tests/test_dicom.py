""" Test DICOM functionality.
"""

from zipfile import ZipFile

import numpy as np

import pytest

import imageio.v2 as iio
import imageio.v3 as iio3
from imageio import core
import imageio.plugins.dicom
from conftest import deprecated_test


@pytest.fixture(scope="module")
def examples(test_images, tmp_path_factory):
    """Create two dirs, one with one dataset and one with two datasets"""

    workdir = tmp_path_factory.getbasetemp() / "test_dicom"

    # Prepare sources
    fname1 = test_images / "dicom_sample1.zip"
    fname2 = test_images / "dicom_sample2.zip"
    dname1 = workdir / "dicom_sample1"
    dname2 = workdir / "dicom_sample2"

    # folder 1
    ZipFile(fname1).extractall(dname1)

    # folder 2
    ZipFile(fname1).extractall(dname2)
    ZipFile(fname2).extractall(dname2)

    # a file from each folder
    # tests expect this to be a string
    fname1 = str(next(dname1.iterdir()))
    fname2 = str(next(dname2.iterdir()))

    yield dname1, dname2, fname1, fname2


@deprecated_test
def test_read_empty_dir(tmp_path):
    # Test that no format is found, but no error is raised
    request = core.Request(tmp_path, "ri")
    assert iio.formats.search_read_format(request) is None


def test_dcmtk():
    # This should not crach, we make no assumptions on whether its
    # available or not
    imageio.plugins.dicom.get_dcmdjpeg_exe()


@deprecated_test
def test_selection(test_images, tmp_path, examples):
    dname1, dname2, fname1, fname2 = examples

    # Test that DICOM can examine file
    F = iio.formats.search_read_format(core.Request(fname1, "ri"))
    assert F.name == "DICOM"
    assert isinstance(F, type(iio.formats["DICOM"]))

    # Test that we cannot save
    request = core.Request(tmp_path / "test.dcm", "wi")
    assert not F.can_write(request)

    # Test fail on wrong file
    fname2 = fname1 + ".fake"
    bb = open(fname1, "rb").read()
    bb = bb[:128] + b"XXXX" + bb[132:]
    open(fname2, "wb").write(bb)
    with pytest.raises(Exception):
        F.get_reader(core.Request(fname2, "ri"))

    # Test special files with other formats
    im = iio.imread(test_images / "dicom_file01.dcm")
    assert im.shape == (512, 512)
    im = iio.imread(test_images / "dicom_file03.dcm")
    assert im.shape == (512, 512)
    im = iio.imread(test_images / "dicom_file04.dcm")
    assert im.shape == (512, 512)

    # Expected fails
    fname = test_images / "dicom_file90.dcm"
    with pytest.raises(RuntimeError):
        iio.imread(fname)  # 1.2.840.10008.1.2.4.91
    fname = test_images / "dicom_file91.dcm"
    with pytest.raises(RuntimeError):
        iio.imread(fname)  # not pixel data

    # This one *should* work, but does not, see issue #18
    try:
        iio.imread(test_images / "dicom_file02.dcm")
    except Exception:
        pass


def test_progress(examples):
    dname1, dname2, fname1, fname2 = examples

    iio.imread(fname1, progress=True)
    iio.imread(fname1, progress=core.StdoutProgressIndicator("test"))
    iio.imread(fname1, progress=None)
    with pytest.raises(ValueError):
        iio.imread(fname1, progress=3)


def test_different_read_modes(examples):
    dname1, dname2, fname1, fname2 = examples

    for fname, dname, n in [(fname1, dname1, 1), (fname2, dname2, 2)]:
        # Test imread()
        im = iio.imread(fname)
        assert isinstance(im, np.ndarray)
        assert im.shape == (512, 512)

        # Test mimread()
        ims = iio.mimread(fname)
        assert isinstance(ims, list)
        assert ims[0].shape == im.shape
        assert len(ims) > 1
        #
        ims2 = iio.mimread(dname, format="DICOM")
        assert len(ims) == len(ims2)

        # Test volread()
        vol = iio.volread(dname, format="DICOM")
        assert vol.ndim == 3
        assert vol.shape[0] > 10
        assert vol.shape[1:] == (512, 512)
        #
        vol2 = iio.volread(fname)  # fname works as well
        assert (vol == vol2).all()

        # Test mvolread()
        vols = iio.mvolread(dname, format="DICOM")
        assert isinstance(vols, list)
        assert len(vols) == n
        assert vols[0].shape == vol.shape
        assert sum([v.shape[0] for v in vols]) == len(ims)


def test_different_read_modes_with_readers(examples):
    dname1, dname2, fname1, fname2 = examples

    for fname, dname, n in [(fname1, dname1, 1), (fname2, dname2, 2)]:
        # Test imread()
        R = iio.read(fname, "DICOM", "i")
        assert len(R) == 1
        assert isinstance(R.get_meta_data(), dict)
        assert isinstance(R.get_meta_data(0), dict)

        # Test mimread()
        R = iio.read(fname, "DICOM", "I")
        if n == 1:
            assert len(R) > 10
        else:
            assert len(R) == 20 + 25
        assert isinstance(R.get_meta_data(), dict)
        assert isinstance(R.get_meta_data(0), dict)

        # Test volread()
        R = iio.read(fname, "DICOM", "v")
        assert len(R) == n  # we ask for one, but get an honest number
        assert isinstance(R.get_meta_data(), dict)
        assert isinstance(R.get_meta_data(0), dict)

        # Test mvolread()
        R = iio.read(fname, "DICOM", "V")
        assert len(R) == n
        assert isinstance(R.get_meta_data(), dict)
        assert isinstance(R.get_meta_data(0), dict)

        # Touch DicomSeries objects
        assert repr(R._series[0])
        assert R._series[0].description
        assert len(R._series[0].sampling) == 3

        R = iio.read(fname, "DICOM", "?")
        with pytest.raises(RuntimeError):
            R.get_length()


def test_v3_reading(test_images):
    # this is a regression test for
    # https://github.com/imageio/imageio/issues/862
    expected = iio.imread(test_images / "dicom_file01.dcm")
    actual = iio3.imread(test_images / "dicom_file01.dcm")

    assert np.allclose(actual, expected)
