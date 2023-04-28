""" Test imageio core functionality.
"""

import os
import sys
import time
import shutil
import random
import tempfile
import ctypes.util
from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pytest

from pytest import raises, skip
from imageio.config import FileExtension

import imageio
import imageio as iio
import imageio.core.imopen as imopen_module
from imageio import core
from imageio.core import Request
from imageio.core import IS_PYPY, get_remote_file
from imageio.core.request import Mode, InitializationError
from imageio.config.plugins import PluginConfig

from conftest import deprecated_test

from pathlib import Path


class UselessDummyPlugin:
    """A dummy plugin to test plugin resultion and dynamic loading"""

    def __init__(self, request):
        raise InitializationError("Can not read anything")


class EpicDummyPlugin:
    def __init__(self, request):
        """Can read anything"""


class BrokenDummyPlugin:
    def __init__(self, request):
        """Breaks during initialization"""

        raise ValueError("Something went wrong.")


@pytest.mark.needs_internet
def test_fetching(tmp_path):
    """Test fetching of files"""

    # This should download the file (force download, because local cache)
    fname1 = get_remote_file("images/chelsea.png", tmp_path, True)
    mtime1 = os.path.getmtime(fname1)
    # This should reuse it
    fname2 = get_remote_file("images/chelsea.png", tmp_path)
    mtime2 = os.path.getmtime(fname2)
    # This should overwrite
    fname3 = get_remote_file("images/chelsea.png", tmp_path, True)
    mtime3 = os.path.getmtime(fname3)
    # This should too (update this if imageio is still around in 1000 years)
    fname4 = get_remote_file("images/chelsea.png", tmp_path, "3014-01-01")
    mtime4 = os.path.getmtime(fname4)
    # This should not
    fname5 = get_remote_file("images/chelsea.png", tmp_path, "2014-01-01")
    mtime5 = os.path.getmtime(fname4)
    #
    assert os.path.isfile(fname1)
    assert fname1 == fname2
    assert fname1 == fname3
    assert fname1 == fname4
    assert fname1 == fname5
    if not sys.platform.startswith("darwin"):
        # weird, but these often fail on my osx VM
        assert mtime1 == mtime2
        assert mtime1 < mtime3
        assert mtime3 < mtime4
        assert mtime4 == mtime5

    # Test failures
    _urlopen = core.fetching.urlopen
    _chunk_read = core.fetching._chunk_read
    #
    with pytest.raises(IOError):
        get_remote_file("this_does_not_exist", tmp_path)
    #
    try:
        core.fetching.urlopen = None
        raises(IOError, get_remote_file, "images/chelsea.png", None, True)
    finally:
        core.fetching.urlopen = _urlopen
    #
    try:
        core.fetching._chunk_read = None
        raises(IOError, get_remote_file, "images/chelsea.png", None, True)
    finally:
        core.fetching._chunk_read = _chunk_read
    #
    try:
        os.environ["IMAGEIO_NO_INTERNET"] = "1"
        raises(IOError, get_remote_file, "images/chelsea.png", None, True)
    finally:
        del os.environ["IMAGEIO_NO_INTERNET"]
    # Coverage miss
    assert "0 bytes" == core.fetching._sizeof_fmt(0)


def test_findlib2():
    if not sys.platform.startswith("linux"):
        skip("test on linux only")

    # Candidate libs for common freeimage
    fi_dir = os.path.join(core.appdata_dir("imageio"), "freeimage")
    if not os.path.isdir(fi_dir):
        os.mkdir(fi_dir)
    dirs, paths = core.findlib.generate_candidate_libs(["libfreeimage"], [fi_dir])
    # assert fi_dir in dirs -> Cannot test: lib may not exist

    open(os.path.join(fi_dir, "notalib.test.so"), "wb")

    # Loading libs
    gllib = ctypes.util.find_library("GL")
    core.load_lib([gllib], [])
    # Fail
    raises(ValueError, core.load_lib, [], [])  # Nothing given
    raises(ValueError, core.load_lib, ["", None], [])  # Nothing given
    raises(OSError, core.load_lib, ["thislibdoesnotexist_foobar"], [])
    raises(OSError, core.load_lib, [], ["notalib"], [fi_dir])


@pytest.mark.needs_internet
def test_request(test_images, tmp_userdir):
    """Test request object"""

    # Check uri-type, this is not a public property, so we test the private
    R = Request("http://example.com", "ri")
    assert R._uri_type == core.request.URI_HTTP
    R = Request("ftp://example.com", "ri")
    assert R._uri_type == core.request.URI_FTP
    R = Request("file://~/foo.png", "wi")
    assert R._uri_type == core.request.URI_FILENAME
    R = Request("<video0>", "rI")
    assert R._uri_type == core.request.URI_BYTES
    R = Request(iio.RETURN_BYTES, "wi")
    assert R._uri_type == core.request.URI_BYTES
    #
    fname = test_images / "chelsea.png"
    R = Request(fname, "ri")
    assert R._uri_type == core.request.URI_FILENAME
    R = Request("~/filethatdoesnotexist", "wi")
    assert R._uri_type == core.request.URI_FILENAME  # Too short to be bytes
    R = Request(b"x" * 600, "ri")
    assert R._uri_type == core.request.URI_BYTES
    R = Request(sys.stdin, "ri")
    assert R._uri_type == core.request.URI_FILE
    R = Request(sys.stdout, "wi")
    assert R._uri_type == core.request.URI_FILE
    # exapand user dir
    R = Request("~/foo", "wi")
    assert R.filename == os.path.expanduser("~/foo").replace("/", os.path.sep)
    # zip file
    R = Request("~/bar.zip/spam.png", "wi")
    assert R._uri_type == core.request.URI_ZIPPED

    R = Request(b"x", "r")
    assert R._mode == "r?"

    R = Request("~/bar.zip/spam.png", "w")
    assert R._mode == "w?"

    # Test failing inits
    raises(ValueError, Request, "/some/file", None)  # mode must be str
    raises(ValueError, Request, "/some/file", 3)  # mode must be str
    raises(ValueError, Request, "/some/file", "")  # mode must be len 2
    raises(ValueError, Request, "/some/file", "rii")  # mode must be len 2
    raises(ValueError, Request, "/some/file", "xi")  # mode[0] must be in rw
    #
    raises(IOError, Request, ["invalid", "uri"] * 10, "ri")  # invalid uri
    raises(IOError, Request, 4, "ri")  # invalid uri
    # nonexistent reads
    raises(FileNotFoundError, Request, "/does/not/exist", "ri")
    raises(FileNotFoundError, Request, "/does/not/exist.zip/spam.png", "ri")
    if Path is not None:
        raises(FileNotFoundError, Request, Path("/does/not/exist"), "ri")
    raises(IOError, Request, "http://example.com", "wi")  # no writing here
    # write dir nonexist
    raises(FileNotFoundError, Request, "/does/not/exist.png", "wi")
    if Path is not None:
        raises(FileNotFoundError, Request, Path("/does/not/exist.png"), "wi")

    # Test auto-download
    R = Request("imageio:chelsea.png", "ri")
    assert R.filename == get_remote_file("images/chelsea.png")
    #
    R = Request("imageio:chelsea.zip/chelsea.png", "ri")
    assert R._filename_zip[0] == get_remote_file("images/chelsea.zip")
    assert R.filename == get_remote_file("images/chelsea.zip") + "/chelsea.png"

    # Test zip false-positive detection
    with tempfile.TemporaryDirectory() as tmp_path:
        bait_zip = os.path.join(tmp_path, "test.zip")
        os.mkdir(bait_zip)
        file_path = os.path.join(bait_zip, "foo.jpg")
        chelsia = get_remote_file("images/chelsea.png")
        shutil.copy(chelsia, file_path)

        R = Request(file_path, "ri")
        assert R._uri_type == core.request.URI_FILENAME


@pytest.mark.needs_internet
def test_request_read_sources(test_images, tmp_userdir):
    # Make an image available in many ways
    fname = "chelsea.png"
    filename = test_images / fname
    bytes = open(str(filename), "rb").read()
    #
    burl = "https://raw.githubusercontent.com/imageio/test_images/master/"
    zipfilename = tmp_userdir / "test1.zip"
    with ZipFile(zipfilename, "w") as zf:
        zf.writestr(fname, bytes)

    # Read that image from these different sources. Read data from file
    # and from local file (the two main plugin-facing functions)
    for file_or_filename in range(2):
        for check_first_bytes in range(2):
            # Define uris to test. Define inside loop, since we need fresh files
            uris = [
                filename,
                os.path.join(zipfilename, fname),
                bytes,
                memoryview(bytes),
                open(filename, "rb"),
            ]
            uris.append(burl + fname)

            for uri in uris:
                R = Request(uri, "ri")
                if check_first_bytes:
                    first_bytes = R.firstbytes
                if file_or_filename == 0:
                    all_bytes = R.get_file().read()
                else:
                    with open(R.get_local_filename(), "rb") as f:
                        all_bytes = f.read()
                R.finish()
                assert bytes == all_bytes
                if check_first_bytes:
                    assert len(first_bytes) > 0
                    assert all_bytes.startswith(first_bytes)


def test_request_save_sources(test_images, tmp_path):
    # Get test data
    filename = test_images / "chelsea.png"
    with open(filename, "rb") as f:
        bytes = f.read()
    assert len(bytes) > 0

    # Prepare destinations
    fname2 = filename.with_suffix(".out").name
    filename2 = tmp_path / fname2
    zipfilename2 = tmp_path / "test2.zip"
    file2 = None

    # Write an image into many different destinations
    # Do once via file and ones via local filename
    for file_or_filename in range(2):
        # Clear destinations
        for xx in (filename2, zipfilename2):
            if os.path.isfile(xx):
                os.remove(xx)
        file2 = BytesIO()
        # Write to four destinations
        for uri in (
            filename2,
            os.path.join(zipfilename2, fname2),
            file2,
            iio.RETURN_BYTES,  # This one last to fill `res`
        ):
            R = Request(uri, "wi")
            if file_or_filename == 0:
                R.get_file().write(bytes)  # via file
            else:
                with open(R.get_local_filename(), "wb") as f:
                    f.write(bytes)  # via local
            R.finish()
            res = R.get_result()
        # Test four results
        with open(filename2, "rb") as f:
            assert f.read() == bytes
        with ZipFile(zipfilename2, "r") as zf:
            assert zf.open(fname2).read() == bytes
        assert file2.getvalue() == bytes
        assert res == bytes


def test_request_seekable_file_object():
    SeekableFileObject = imageio.core.request.SeekableFileObject
    data = bytes([int(random.uniform(0, 255)) for i in range(100)])
    f1 = BytesIO(data)
    f2 = SeekableFileObject(f1)

    # Test all kinds of seeks, reads and tells
    resses = []
    for f in (f1, f2):
        (f1.seek(0), f2.seek(0))
        res = [
            f.read(8),
            f.tell(),
            f.seek(0),
            f.tell(),
            f.read(8),
            f.read(),
            f.seek(20, 1),
            f.read(8),
            f.seek(10, 2),
            f.read(8),
            f.seek(-10, 2),
            f.read(8),
            f.seek(-20, 2),
            f.tell(),
            f.read(8),
            f.read(0),
            f.read(-1),
        ]
        resses.append(res)
    assert resses[0] == resses[1]

    # Test out of bounds
    for f in (f1, f2):
        # Align them
        (f1.seek(0), f2.seek(0))
        f.seek(3)
        assert f.tell() == 3
        with raises(ValueError):
            f.seek(-10)
        assert f.tell() == 3
        f.seek(-10, 1)  # no raise!
        assert f.tell() == 0
        f.seek(-10, 2)
        assert f.tell() == 90
        f.seek(10, 2)
        assert f.tell() == 110
        assert f.read(1) == b""
        f.seek(20, 1)
        assert f.tell() == 130
        f.seek(150)
        assert f.tell() == 150


def test_request_file_no_seek():
    class File:
        def read(self, n):
            return b"\x00" * n

        def seek(self, i):
            raise IOError("Not supported")

        def tell(self):
            raise Exception("Not supported")

        def close(self):
            pass

    R = Request(File(), "ri")
    with raises(IOError):
        R.firstbytes


def test_util_image():
    meta = {"foo": 3, "bar": {"spam": 1, "eggs": 2}}
    # Image
    a = np.zeros((10, 10))
    im = core.util.Image(a, meta)
    isinstance(im, np.ndarray)
    isinstance(im.meta, dict)
    assert str(im) == str(a)
    # Preserve after copy
    im2 = core.util.Image(im)
    assert isinstance(im2, core.util.Image)
    assert im2.meta == im.meta
    # Preserve after action
    im2 = im + 1
    assert isinstance(im2, core.util.Image)
    assert im2.meta == im.meta
    # Turn to normal array / scalar if shape none
    im2 = im.sum(0)
    if not IS_PYPY:  # known fail on Pypy
        assert not isinstance(im2, core.util.Image)
    s = im.sum()
    assert not isinstance(s, core.util.Image)
    # Repr !! no more
    # assert '2D image' in repr(core.util.Image(np.zeros((10, 10))))
    # assert '2D image' in repr(core.util.Image(np.zeros((10, 10, 3))))
    # assert '3D image' in repr(core.util.Image(np.zeros((10, 10, 10))))
    # Fail
    raises(ValueError, core.util.Image, 3)  # not a ndarray
    raises(ValueError, core.util.Image, a, 3)  # not a dict


def test_util_dict():
    # Dict class
    D = core.Dict()
    D["foo"] = 1
    D["bar"] = 2
    D["spam"] = 3
    assert list(D.values()) == [1, 2, 3]
    #
    assert D.spam == 3
    D.spam = 4
    assert D["spam"] == 4
    # Can still use copy etc.
    assert D.copy() == D
    assert "spam" in D.keys()
    # Can also insert non-identifiers
    D[3] = "not an identifier"
    D["34a"] = "not an identifier"
    D[None] = "not an identifier"
    # dir
    names = dir(D)
    assert "foo" in names
    assert "spam" in names
    assert 3 not in names
    assert "34a" not in names
    # Fail
    raises(AttributeError, D.__setattr__, "copy", False)  # reserved
    raises(AttributeError, D.__getattribute__, "notinD")


def test_util_get_platform():
    # Test get_platform
    platforms = "win32", "win64", "linux32", "linux64", "osx32", "osx64"
    assert core.get_platform() in platforms


def test_util_asarray():
    # Test asarray
    im1 = core.asarray([[1, 2, 3], [4, 5, 6]])
    im2 = im1.view(type=core.Image)
    im3 = core.asarray(im2)
    assert type(im2) != np.ndarray
    assert type(im3) == np.ndarray
    if not IS_PYPY:
        for i in (1, 2, 3):
            im1[0, 0] = i
            assert im2[0, 0] == i
            assert im3[0, 0] == i


def test_util_progres_bar(sleep=0):
    """Test the progress bar"""
    # This test can also be run on itself to *see* the result

    # Progress bar
    for Progress in (core.StdoutProgressIndicator, core.BaseProgressIndicator):
        B = Progress("test")
        assert B.status() == 0
        B.start(max=20)
        assert B.status() == 1
        B.start("Run to 10", max=10)  # Restart
        for i in range(8):
            time.sleep(sleep)
            B.set_progress(i)
            assert B._progress == i
        B.increase_progress(1)
        assert B._progress == i + 1
        B.finish()
        assert B.status() == 2
        # Without max
        B.start("Run without max int")
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(i)
        B.start("Run without float")
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(i + 0.1)
        B.start("Run without progress")
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(0)
        B.write("some message")
        B.fail("arg")
        assert B.status() == 3
        # Perc
        B.start("Run percentage", unit="%", max=100)  # Restart
        for i in range(0, 101, 5):
            time.sleep(sleep)
            B.set_progress(i)
        B.finish("Done")
        if sleep:
            return


def test_util_image_as_uint():
    """Tests the various type conversions when writing to uint"""
    raises(ValueError, core.image_as_uint, 4)
    raises(ValueError, core.image_as_uint, "not an image")
    raises(ValueError, core.image_as_uint, np.array([0, 1]), bitdepth=13)
    raises(ValueError, core.image_as_uint, np.array([0.0, np.inf], "float32"))
    raises(ValueError, core.image_as_uint, np.array([-np.inf, 0.0], "float32"))

    test_arrays = (  # (input, output bitdepth, expected output)
        # No bitdepth specified, assumed to be 8-bit
        (np.array([0, 2**8 - 1], "uint8"), None, np.uint8([0, 255])),
        (np.array([0, 2**16 - 1], "uint16"), None, np.uint8([0, 255])),
        (np.array([0, 2**32 - 1], "uint32"), None, np.uint8([0, 255])),
        (np.array([0, 2**64 - 1], "uint64"), None, np.uint8([0, 255])),
        (np.array([-2, 2], "int8"), None, np.uint8([0, 255])),
        (np.array([-2, 2], "int16"), None, np.uint8([0, 255])),
        (np.array([-2, 2], "int32"), None, np.uint8([0, 255])),
        (np.array([-2, 2], "int64"), None, np.uint8([0, 255])),
        (np.array([0, 1], "float16"), None, np.uint8([0, 255])),
        (np.array([0, 1], "float32"), None, np.uint8([0, 255])),
        (np.array([0, 1], "float64"), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float16"), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float32"), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float64"), None, np.uint8([0, 255])),
        # 8-bit output
        (np.array([0, 2**8 - 1], "uint8"), 8, np.uint8([0, 255])),
        (np.array([0, 2**16 - 1], "uint16"), 8, np.uint8([0, 255])),
        (np.array([0, 2**32 - 1], "uint32"), 8, np.uint8([0, 255])),
        (np.array([0, 2**64 - 1], "uint64"), 8, np.uint8([0, 255])),
        (np.array([-2, 2], "int8"), 8, np.uint8([0, 255])),
        (np.array([-2, 2], "int16"), 8, np.uint8([0, 255])),
        (np.array([-2, 2], "int32"), 8, np.uint8([0, 255])),
        (np.array([-2, 2], "int64"), 8, np.uint8([0, 255])),
        (np.array([0, 1], "float16"), 8, np.uint8([0, 255])),
        (np.array([0, 1], "float32"), 8, np.uint8([0, 255])),
        (np.array([0, 1], "float64"), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float16"), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float32"), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], "float64"), 8, np.uint8([0, 255])),
        # 16-bit output
        (np.array([0, 2**8 - 1], "uint8"), 16, np.uint16([0, 65535])),
        (np.array([0, 2**16 - 1], "uint16"), 16, np.uint16([0, 65535])),
        (np.array([0, 2**32 - 1], "uint32"), 16, np.uint16([0, 65535])),
        (np.array([0, 2**64 - 1], "uint64"), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], "int8"), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], "int16"), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], "int32"), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], "int64"), 16, np.uint16([0, 65535])),
        (np.array([0, 1], "float16"), 16, np.uint16([0, 65535])),
        (np.array([0, 1], "float32"), 16, np.uint16([0, 65535])),
        (np.array([0, 1], "float64"), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], "float16"), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], "float32"), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], "float64"), 16, np.uint16([0, 65535])),
        # Rounding
        (np.array([1.4 / 255, 1.6 / 255], "float32"), 8, np.uint8([1, 2])),
        (
            np.array([254.4 / 255, 254.6 / 255], "float32"),
            8,
            np.uint8([254, 255]),
        ),
        (
            np.array([1.4 / 65535, 1.6 / 65535], "float32"),
            16,
            np.uint16([1, 2]),
        ),
        (
            np.array([65534.4 / 65535, 65534.6 / 65535], "float32"),
            16,
            np.uint16([65534, 65535]),
        ),  # noqa
    )

    for tup in test_arrays:
        res = core.image_as_uint(tup[0], bitdepth=tup[1])
        assert res[0] == tup[2][0] and res[1] == tup[2][1]


def test_util_has_has_module():
    assert not core.has_module("this_module_does_not_exist")
    assert core.has_module("sys")


# TODO: update this test after deprecations are removed
@deprecated_test
def test_functions(test_images, tmp_path):
    """Test the user-facing API functions"""

    import imageio.plugins.example

    # Test help(), it prints stuff, so we just check whether that goes ok
    imageio.help()  # should print overview
    imageio.help("PNG")  # should print about PNG

    fname1 = test_images / "chelsea.png"
    fname2 = tmp_path / fname1.with_suffix(".jpg").name
    fname3 = tmp_path / fname1.with_suffix(".notavalidext").name
    open(fname3, "wb")

    # Test read()
    R1 = iio.read(fname1)
    R2 = iio.read(fname1, "png")

    # this tests if the highest priority png plugin and the highest
    # priority fallback plugin match.
    # Do we really what to enforce this?
    assert type(R1) is type(R2)

    raises(ValueError, iio.read, fname3)  # existing but not readable
    raises(IndexError, iio.read, fname1, "notexistingformat")

    # Note: This is actually a test of Requests. We should probably
    # migrate or remove it.
    raises(FileNotFoundError, iio.read, "notexisting.barf")

    # Test save()
    W1 = iio.save(fname2)
    W2 = iio.save(fname2, "JPG")
    W1.close()
    W2.close()
    assert type(W1) is type(W2)
    # Fail
    raises(FileNotFoundError, iio.save, "~/dirdoesnotexist/wtf.notexistingfile")

    # Test imread()
    im1 = iio.imread(fname1)
    im2 = iio.imread(fname1, "png")
    assert im1.shape[2] == 3
    assert np.all(im1 == im2)

    # Test imsave()
    if os.path.isfile(fname2):
        os.remove(fname2)
    assert not os.path.isfile(fname2)
    iio.imsave(fname2, im1[:, :, 0])
    iio.imsave(fname2, im1)
    assert os.path.isfile(fname2)

    # Test mimread()
    fname3 = test_images / "newtonscradle.gif"
    ims = iio.mimread(fname3)
    assert isinstance(ims, list)
    assert len(ims) > 1
    assert ims[0].ndim == 3
    assert ims[0].shape[2] in (1, 3, 4)
    # Test protection
    with raises(RuntimeError):
        iio.mimread(test_images / "chelsea.png", "dummy", length=np.inf)

    if IS_PYPY:
        return  # no support for npz format :(

    # Test mimsave()
    fname5 = tmp_path / "newtonscradle2.npz"
    if os.path.isfile(fname5):
        os.remove(fname5)
    assert not os.path.isfile(fname5)
    iio.mimsave(fname5, [im[:, :, 0] for im in ims])
    iio.mimsave(fname5, ims)
    assert os.path.isfile(fname5)

    # Test volread()
    fname4 = test_images / "stent.npz"
    vol = iio.volread(fname4)
    assert vol.ndim == 3
    assert vol.shape[0] == 256
    assert vol.shape[1] == 128
    assert vol.shape[2] == 128

    # Test volsave()
    volc = np.zeros((10, 10, 10, 3), np.uint8)  # color volume
    fname6 = tmp_path / "stent2.npz"
    if os.path.isfile(fname6):
        os.remove(fname6)
    assert not os.path.isfile(fname6)
    iio.volsave(fname6, volc)
    iio.volsave(fname6, vol)
    assert os.path.isfile(fname6)

    # Test mvolread()
    vols = iio.mvolread(fname4)
    assert isinstance(vols, list)
    assert len(vols) == 1
    assert vols[0].shape == vol.shape

    # Test mvolsave()
    if os.path.isfile(fname6):
        os.remove(fname6)
    assert not os.path.isfile(fname6)
    iio.mvolsave(fname6, [volc, volc])
    iio.mvolsave(fname6, vols)
    assert os.path.isfile(fname6)

    # Fail for save functions
    raises(ValueError, iio.imsave, fname2, 42)
    raises(ValueError, iio.mimsave, fname5, [42])
    raises(ValueError, iio.volsave, fname6, np.zeros((100, 100, 100, 40)))
    raises(ValueError, iio.volsave, fname6, 42)
    raises(ValueError, iio.mvolsave, fname6, [42])


@deprecated_test
def test_v2_format_resolution(test_images):
    img1 = iio.v2.imread(test_images / "chelsea.png", format=".png")
    assert img1.shape == (300, 451, 3)

    # I still don't understand why we allow "format" to be a file-path
    # but I am keeping it for backwards compatibility
    img2 = iio.v2.imread(
        test_images / "chelsea.png", format=test_images / "chelsea.png"
    )
    assert img2.shape == (300, 451, 3)


@pytest.mark.parametrize(
    "arg,expected",
    [
        (1, 1),
        ("1", 1),
        ("8B", 8),
        ("1MB", 1000**2),
        ("1M", 1000**2),
        ("1GiB", 1024**3),
        ("1.5TB", 1.5 * 1000**4),
    ],
)
def test_to_nbytes_correct(arg, expected):
    n = iio.v2.to_nbytes(arg)
    assert n == expected


@pytest.mark.parametrize("arg", ["1mb", "1Giib", "GB", "1.3.2TB", "8b"])
def test_to_nbytes_incorrect(arg):
    with raises(ValueError):
        iio.v2.to_nbytes(arg)


def test_memtest(test_images, tmp_path):
    fname3 = test_images / "newtonscradle.gif"
    iio.mimread(fname3)  # trivial case
    iio.mimread(fname3, memtest=1000**2 * 256)
    iio.mimread(fname3, memtest="256MB")
    iio.mimread(fname3, memtest="256M")
    iio.mimread(fname3, memtest="256MiB")

    # low limit should be hit
    with raises(RuntimeError):
        iio.mimread(fname3, memtest=10)
    with raises(RuntimeError):
        iio.mimread(fname3, memtest="64B")

    with raises(ValueError):
        iio.mimread(fname3, memtest="64b")


@deprecated_test
def test_example_plugin(test_images, tmp_path):
    """Test the example plugin"""

    import imageio.plugins.example  # noqa: F401

    fname = tmp_path / "out.png"
    r = Request(test_images / "chelsea.png", "r?")
    R = iio.formats["dummy"].get_reader(r)
    W = iio.formats["dummy"].get_writer(Request(fname, "w?"))
    #
    assert len(R) == 1
    assert R.get_data(0).ndim
    raises(IndexError, R.get_data, 1)
    # raises(RuntimeError, R.get_meta_data)
    assert R.get_meta_data() == {}
    R.close()
    #
    raises(RuntimeError, W.append_data, np.zeros((10, 10)))
    raises(RuntimeError, W.set_meta_data, {})
    W.close()


def test_imwrite_not_subclass(tmpdir):
    class Foo(object):
        def __init__(self):
            pass

        def __array__(self, dtype=None):
            return np.zeros((4, 4), dtype=np.uint8)

    filename = os.path.join(str(tmpdir), "foo.bmp")
    iio.v2.imwrite(filename, Foo())
    im = iio.v2.imread(filename)
    assert im.shape == (4, 4)


def test_imwrite_not_array_like():
    class Foo(object):
        def __init__(self):
            pass

    with raises(ValueError):
        iio.imwrite("foo.bmp", Foo())
    with raises(ValueError):
        iio.imwrite("foo.bmp", "asd")


def test_imwrite_symbol_name():
    # this is a regression test for https://github.com/imageio/imageio/issues/674
    if sys.platform == "linux":
        name = """#!~:@$%^&`-+{};',.()? []_=.jpg"""
    elif sys.platform == "win32":
        name = """#!~@$%^&`-+{};',.() []_=.jpg"""
    elif sys.platform == "darwin":
        name = """#!~@$%^&`-+{};',.()? []_=.jpg"""
    else:
        pytest.skip("Unknown OS.")
    tmp_request = imageio.core.Request(name, "w")
    assert tmp_request.extension == ".jpg"
    tmp_request.finish()


def test_legacy_empty_image():
    with pytest.raises(RuntimeError):
        with iio.imopen("foo.bmp", "wI", plugin="GIF-PIL", legacy_mode=True) as file:
            file.write([])


def test_imopen_unsupported_iomode():
    with pytest.raises(ValueError):
        iio.imopen("", "unknown_iomode")


def test_imopen_no_plugin_found(clear_plugins):
    with pytest.raises(IOError):
        iio.imopen("unknown.abcd", "r", search_legacy_only=False)


@pytest.mark.parametrize("invalid_file", [".jpg"], indirect=["invalid_file"])
def test_imopen_unregistered_plugin(clear_plugins, invalid_file):
    with pytest.raises(ValueError):
        iio.imopen(invalid_file, "r", plugin="unknown_plugin", legacy_mode=False)


def test_plugin_selection_failure(clear_plugins):
    imopen_module.known_plugins["plugin1"] = PluginConfig(
        name="plugin1", class_name="UselessDummyPlugin", module_name="test_core"
    )

    imopen_module.known_plugins["plugin2"] = PluginConfig(
        name="plugin2", class_name="UselessDummyPlugin", module_name="test_core"
    )

    with pytest.raises(IOError):
        iio.imopen("", "r", legacy_mode=False)


@pytest.mark.parametrize("invalid_file", [".jpg"], indirect=["invalid_file"])
def test_plugin_selection_success(clear_plugins, invalid_file):
    imopen_module.known_plugins["plugin"] = PluginConfig(
        name="plugin", class_name="EpicDummyPlugin", module_name="test_core"
    )

    instance = iio.imopen(invalid_file, "r", legacy_mode=False)

    assert isinstance(instance, EpicDummyPlugin)


def test_imopen_installable_plugin(clear_plugins):
    # test uninstalled plugin
    iio.config.known_plugins["plugin"] = PluginConfig(
        name="plugin", class_name="EpicDummyPlugin", module_name="non_existant"
    )

    with pytest.raises(IOError):
        iio.imopen("foo.bar", "w", legacy_mode=False)

    # register extension
    iio.config.known_extensions[".bar"] = [
        FileExtension(extension=".bar", priority=["plugin"])
    ]

    with pytest.raises(IOError):
        iio.imopen("foo.bar", "w", legacy_mode=False)


def test_legacy_object_image_writing(tmp_path):
    with pytest.raises(TypeError):
        # dtype=object should fail with type error
        iio.mimwrite(
            tmp_path / "foo.gif", np.array([[[0] * 6, [0] * 6]] * 4, dtype=object)
        )


def test_imiter(test_images):
    # maybe it would be better to load the image without using imageio, e.g.
    # numpy_im = np.load(test_images / "newtonscradle_rgb.npy")

    full_image = iio.v3.imread(
        test_images / "newtonscradle.gif",
        index=None,
        plugin="pillow",
        mode="RGB",
    )

    for idx, im in enumerate(
        iio.v3.imiter(
            test_images / "newtonscradle.gif",
            plugin="pillow",
            mode="RGB",
        )
    ):
        assert np.allclose(full_image[idx, ...], im)


def test_request_mode_backwards_compatibility():
    mode = Mode("ri")
    assert mode == "ri"
    assert mode[0] == "r"


def test_faulty_legacy_mode_access():
    mode = Mode("ri")
    with pytest.raises(IndexError):
        mode[3]  # has no third component


@pytest.mark.needs_internet
def test_mvolread_out_of_bytes(test_images):
    with pytest.raises(RuntimeError):
        iio.mvolread(
            "https://github.com/imageio/imageio-binaries/blob/master/images/multipage_rgb.tif?raw=true",
            memtest="1B",
        )


def test_invalid_explicit_plugin(clear_plugins):
    imopen_module.known_plugins["plugin1"] = PluginConfig(
        name="plugin1", class_name="UselessDummyPlugin", module_name="test_core"
    )

    with pytest.raises(IOError):
        iio.imopen("", "r", plugin="plugin1", legacy_mode=False)


def test_broken_plugin(clear_plugins):
    imopen_module.known_plugins["plugin1"] = PluginConfig(
        name="plugin1", class_name="BrokenDummyPlugin", module_name="test_core"
    )

    with pytest.raises(IOError):
        iio.imopen("", "r", plugin="plugin1", legacy_mode=False)


def test_volwrite_failure():
    not_image_data = np.array("Object Array.")

    with pytest.raises(ValueError):
        iio.volwrite("foo.jpg", not_image_data)


def test_memory_size(test_images):
    im = iio.mimread(test_images / "newtonscradle.gif", memtest=True)
    assert len(im) == 36

    im = iio.mimread(test_images / "newtonscradle.gif", memtest=None)
    assert len(im) == 36


def test_imopen_explicit_plugin_input(clear_plugins, tmp_path):
    with pytest.raises(OSError):
        iio.v3.imopen(tmp_path / "foo.tiff", "w", legacy_mode=False)

    from imageio.plugins.pillow import PillowPlugin

    with iio.v3.imopen(
        tmp_path / "foo.tiff", "w", legacy_mode=False, plugin=PillowPlugin
    ) as f:
        assert isinstance(f, PillowPlugin)


@deprecated_test
def test_sort_order_restore():
    # this is a proxy test; only test PNG instead of all formats
    # since that already reproduces the issue

    old_order = iio.config.known_extensions[".png"][0].priority.copy()
    iio.formats.sort()
    new_order = iio.config.known_extensions[".png"][0].priority.copy()

    assert old_order == new_order


def test_imopen_extension(image_files):
    image_bytes = Path(image_files / "chelsea.png").read_bytes()

    with iio.v3.imopen(image_bytes, "r", extension=".png") as resource:
        result = resource.read()

    expected = iio.v3.imread(image_files / "chelsea.png")

    assert np.allclose(result, expected)


@pytest.mark.parametrize("invalid_file", [".jpg"], indirect=["invalid_file"])
def test_imopen_extension_malformatted(invalid_file, test_images):
    with pytest.raises(ValueError):
        # extension should be ".png"
        iio.v3.imopen(invalid_file, "r", extension="PNG")

    with pytest.warns(UserWarning):
        # extension is invalid and should emit a warning
        iio.v3.imread(test_images / "chelsea.png", format_hint=".cap")


def test_writing_foreign_extension(test_images, tmp_path):
    expected = iio.v3.imread(test_images / "chelsea.png")

    iio.v3.imwrite(tmp_path / "test.png.part", expected, extension=".png")
    actual = iio.v3.imread(tmp_path / "test.png.part", extension=".png")
    np.allclose(actual, expected)

    iio.v2.imwrite(tmp_path / "test2.jpg.part", expected, format=".jpg")
    actual = iio.v3.imread(tmp_path / "test2.jpg.part", extension=".jpg")
    np.allclose(actual, expected)


@deprecated_test
def test_format_hint_malformatted(test_images):
    with pytest.raises(ValueError):
        iio.core.Request(test_images / "chelsea.png", "r", format_hint="PNG")


@deprecated_test
def test_format_hint(test_images):
    im_new = iio.v3.imread(test_images / "chelsea.png", format_hint=".png")

    with iio.v3.imopen(
        test_images / "chelsea.png", "r", format_hint=".png", legacy_mode=True
    ) as file:
        im_old = file.read()

    assert np.allclose(im_new, im_old)

    req = iio.core.Request(test_images / "bricks.jpg", "r", format_hint=".jpg")
    filename = req.get_local_filename()

    assert Path(filename).suffix == ".jpg"


def test_standard_images():
    im = np.ones((800, 600, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError):
        iio.v3.imwrite("imageio:chelsea.png", im)

    with pytest.raises(ValueError):
        iio.v3.imread("imageio:nonexistant_standard_image.png")
