from pytest import raises
import pytest
from imageio.testing import run_tests_if_main, get_test_dir

import os
import gc
import shutil

import numpy as np

import imageio
import imageio as iio
from imageio.core import Format, FormatManager, Request
from imageio.core import get_remote_file


test_dir = get_test_dir()


def setup_module():
    imageio.formats.sort()


def teardown_module():
    imageio.formats.sort()


class MyFormat(Format):
    """TEST DOCS"""

    _closed = []

    def _can_read(self, request):
        return request.filename.lower().endswith(self.extensions + (".haha",))

    def _can_write(self, request):
        return request.filename.lower().endswith(self.extensions + (".haha",))

    class Reader(Format.Reader):
        _failmode = False
        _stream_mode = False

        def _open(self):
            self._read_frames = 0

        def _close(self):
            self.format._closed.append(id(self))

        def _get_length(self):
            if self._stream_mode:
                return np.inf
            return 3

        def _get_data(self, index):
            if self._failmode == 2:
                raise IndexError()
            elif self._failmode:
                return "not an array", {}
            elif self._stream_mode and self._read_frames >= 5:
                raise IndexError()  # Mark end of stream
            else:
                self._read_frames += 1
                return np.ones((10, 10)) * index, self._get_meta_data(index)

        def _get_meta_data(self, index):
            if self._failmode:
                return "not a dict"
            return {"index": index}

    class Writer(Format.Writer):
        def _open(self):
            self._written_data = []
            self._written_meta = []
            self._meta = None

        def _close(self):
            self.format._closed.append(id(self))

        def _append_data(self, im, meta):
            self._written_data.append(im)
            self._written_meta.append(meta)

        def _set_meta_data(self, meta):
            self._meta = meta


def test_format():
    """Test the working of the Format class"""

    filename1 = get_remote_file("images/chelsea.png", test_dir)
    filename2 = filename1 + ".out"

    # Test basic format creation
    F = Format("testname", "test description", "foo bar spam")
    assert F.name == "TESTNAME"
    assert F.description == "test description"
    assert F.name in repr(F)
    assert F.name in F.doc
    assert str(F) == F.doc
    assert set(F.extensions) == {".foo", ".bar", ".spam"}

    # Test setting extensions
    F1 = Format("test", "", "foo bar spam")
    F2 = Format("test", "", "foo, bar,spam")
    F3 = Format("test", "", ["foo", "bar", "spam"])
    F4 = Format("test", "", ".foo .bar .spam")
    for F in (F1, F2, F3, F4):
        assert set(F.extensions) == {".foo", ".bar", ".spam"}
    # Fail
    raises(ValueError, Format, "test", "", 3)  # not valid ext
    raises(ValueError, Format, "test", "", "", 3)  # not valid mode
    raises(ValueError, Format, "test", "", "", "x")  # not valid mode

    # Test subclassing
    F = MyFormat("test", "", modes="i")
    assert "TEST DOCS" in F.doc

    # Get and check reader and write classes
    R = F.get_reader(Request(filename1, "ri"))
    W = F.get_writer(Request(filename2, "wi"))
    assert isinstance(R, MyFormat.Reader)
    assert isinstance(W, MyFormat.Writer)
    assert R.format is F
    assert W.format is F
    assert R.request.filename == filename1
    assert W.request.filename == filename2
    # Fail
    raises(RuntimeError, F.get_reader, Request(filename1, "rI"))
    raises(RuntimeError, F.get_writer, Request(filename2, "wI"))

    # Use as context manager
    with R:
        pass
    with W:
        pass
    # Objects are now closed, cannot be used
    assert R.closed
    assert W.closed
    #
    raises(RuntimeError, R.__enter__)
    raises(RuntimeError, W.__enter__)
    #
    raises(RuntimeError, R.get_data, 0)
    raises(RuntimeError, W.append_data, np.zeros((10, 10)))

    # Test __del__
    R = F.get_reader(Request(filename1, "ri"))
    W = F.get_writer(Request(filename2, "wi"))
    ids = id(R), id(W)
    F._closed[:] = []
    del R
    del W
    gc.collect()  # Invoke __del__
    assert set(ids) == set(F._closed)


def test_reader_and_writer():

    # Prepare
    filename1 = get_remote_file("images/chelsea.png", test_dir)
    filename2 = filename1 + ".out"
    F = MyFormat("test", "", modes="i")

    # Test using reader
    n = 3
    R = F.get_reader(Request(filename1, "ri"))
    assert len(R) == n
    ims = [im for im in R]
    assert len(ims) == n
    for i in range(3):
        assert ims[i][0, 0] == i
        assert ims[i].meta["index"] == i
    for i in range(3):
        assert R.get_meta_data(i)["index"] == i
    # Read next
    assert R.get_data(0)[0, 0] == 0
    assert R.get_next_data()[0, 0] == 1
    assert R.get_next_data()[0, 0] == 2
    # Fail
    R._failmode = 1
    raises(ValueError, R.get_data, 0)
    raises(ValueError, R.get_meta_data, 0)
    R._failmode = 2
    with raises(IndexError):
        [im for im in R]

    # Test writer no format
    raises(ValueError, imageio.get_writer, "foo.unknownext")

    # Test streaming reader
    R = F.get_reader(Request(filename1, "ri"))
    R._stream_mode = True
    assert R.get_length() == np.inf
    ims = [im for im in R]
    assert len(ims) == 5

    # Test using writer
    im1 = np.zeros((10, 10))
    im2 = imageio.core.Image(im1, {"foo": 1})
    W = F.get_writer(Request(filename2, "wi"))
    W.append_data(im1)
    W.append_data(im2)
    W.append_data(im1, {"bar": 1})
    W.append_data(im2, {"bar": 1})
    # Test that no data is copies (but may be different views)
    assert len(W._written_data) == 4
    for im in W._written_data:
        assert (im == im1).all()
    im1[2, 2] == 99
    for im in W._written_data:
        assert (im == im1).all()
    # Test meta
    assert W._written_meta[0] == {}
    assert W._written_meta[1] == {"foo": 1}
    assert W._written_meta[2] == {"bar": 1}
    assert W._written_meta[3] == {"foo": 1, "bar": 1}
    #
    W.set_meta_data({"spam": 1})
    assert W._meta == {"spam": 1}
    # Fail
    raises(ValueError, W.append_data, "not an array")
    raises(ValueError, W.append_data, im, "not a dict")
    raises(ValueError, W.set_meta_data, "not a dict")


def test_default_can_read_and_can_write():

    F = imageio.plugins.example.DummyFormat("test", "", "foo bar", "v")

    # Prepare files
    filename1 = os.path.join(test_dir, "test")
    open(filename1 + ".foo", "wb")
    open(filename1 + ".bar", "wb")
    open(filename1 + ".spam", "wb")

    # Test _can_read()
    assert F.can_read(Request(filename1 + ".foo", "rv"))
    assert F.can_read(Request(filename1 + ".bar", "r?"))
    assert not F.can_read(Request(filename1 + ".spam", "r?"))
    assert not F.can_read(Request(filename1 + ".foo", "ri"))

    # Test _can_write()
    assert F.can_write(Request(filename1 + ".foo", "wv"))
    assert F.can_write(Request(filename1 + ".bar", "w?"))
    assert not F.can_write(Request(filename1 + ".spam", "w?"))
    assert not F.can_write(Request(filename1 + ".foo", "wi"))


def test_format_selection():

    formats = imageio.formats
    fname1 = get_remote_file("images/chelsea.png", test_dir)
    fname2 = os.path.join(test_dir, "test.selectext1")
    fname3 = os.path.join(test_dir, "test.haha")
    open(fname2, "wb")
    open(fname3, "wb")

    # Test searchinhg for read / write format
    F = formats.search_read_format(Request(fname1, "ri"))
    assert isinstance(F, type(formats["PNG"]))
    F = formats.search_write_format(Request(fname1, "wi"))
    assert isinstance(F, type(formats["PNG"]))

    # Now with custom format
    format = MyFormat("test_selection", "xx", "selectext1", "i")
    formats.add_format(format)

    # Select this format for files it said it could handle in extensions
    assert ".selectext1" in fname2
    F = formats.search_read_format(Request(fname2, "ri"))
    assert type(F) is type(format)
    F = formats.search_write_format(Request(fname2, "ri"))
    assert type(F) is type(format)

    # But this custom format also can deal with .haha files
    assert ".haha" in fname3
    F = formats.search_read_format(Request(fname3, "ri"))
    assert type(F) is type(format)
    F = formats.search_write_format(Request(fname3, "ri"))
    assert type(F) is type(format)


# Format manager


def test_format_manager():
    """Test working of the format manager"""

    formats = imageio.formats

    # Test basics of FormatManager
    assert isinstance(formats, FormatManager)
    assert len(formats) > 0
    assert "FormatManager" in repr(formats)

    # Get docs
    smalldocs = str(formats)
    # fulldocs = formats.create_docs_for_all_formats()

    # Check each format ...
    for format in formats:
        #  That each format is indeed a Format
        assert isinstance(format, Format)
        # That they are mentioned
        assert format.name in smalldocs
        # assert format.name in fulldocs

    fname = get_remote_file("images/chelsea.png", test_dir)
    fname2 = fname[:-3] + "noext"
    shutil.copy(fname, fname2)

    # Check getting
    F1 = formats["PNG"]
    F2 = formats[".png"]
    F3 = formats[fname2]  # will look in file itself
    assert type(F1) is type(F2)
    assert type(F1) is type(F3)
    # Check getting
    F1 = formats["DICOM"]
    F2 = formats[".dcm"]
    F3 = formats["dcm"]  # If omitting dot, format is smart enough to try with
    assert type(F1) is type(F2)
    assert type(F1) is type(F3)
    # Fail
    raises(ValueError, formats.__getitem__, 678)  # must be str
    raises(IndexError, formats.__getitem__, ".nonexistentformat")

    # Adding a format
    myformat = Format("test", "test description", "testext1 testext2")
    formats.add_format(myformat)
    assert type(myformat) in [type(f) for f in formats]
    assert type(formats["testext1"]) is type(myformat)
    assert type(formats["testext2"]) is type(myformat)
    # Fail
    raises(ValueError, formats.add_format, 678)  # must be Format
    raises(ValueError, formats.add_format, myformat)  # cannot add twice

    # Adding a format with the same name
    myformat2 = Format("test", "other description", "foo bar")
    raises(ValueError, formats.add_format, myformat2)  # same name
    formats.add_format(myformat2, True)  # overwrite
    assert formats["test"].name is not myformat.name
    assert type(formats["test"]) is type(myformat2)

    # Test show (we assume it shows correctly)
    formats.show()


#   # Potential
#   bytes = b'x' * 300
#   F = formats.search_read_format(Request(bytes, 'r?', dummy_potential=1))
#   assert F is formats['DUMMY']


def test_sorting_errors():

    with raises(TypeError):
        imageio.formats.sort(3)
    with raises(ValueError):
        imageio.formats.sort("foo,bar")
    with raises(ValueError):
        imageio.formats.sort("foo.png")


def test_default_order():

    assert imageio.formats[".tiff"].name == "TIFF"
    assert imageio.formats[".png"].name == "PNG-PIL"
    assert imageio.formats[".pfm"].name == "PFM-FI"


def test_preferring_fi():

    # Prefer FI all the way
    imageio.formats.sort("-FI")

    assert imageio.formats[".tiff"].name == "TIFF-FI"
    assert imageio.formats[".png"].name == "PNG-FI"
    assert imageio.formats[".pfm"].name == "PFM-FI"

    # This would be better
    imageio.formats.sort("TIFF", "-FI")
    assert imageio.formats[".tiff"].name == "TIFF"
    assert imageio.formats[".png"].name == "PNG-FI"
    assert imageio.formats[".pfm"].name == "PFM-FI"


def test_preferring_arbitrary():

    # Normally, these exotic formats are somewhere in the back
    imageio.formats.sort()
    names = [f.name for f in imageio.formats]
    assert "DICOM" not in names[:10]
    assert "FFMPEG" not in names[:10]
    assert "NPZ" not in names[:10]

    # But we can move them forward
    imageio.formats.sort("DICOM", "FFMPEG", "NPZ")
    names = [f.name for f in imageio.formats]
    assert names[0] == "DICOM"
    assert names[1] == "FFMPEG"
    assert names[2] == "NPZ"

    # And back to normal ..
    imageio.formats.sort()
    names = [f.name for f in imageio.formats]
    assert "DICOM" not in names[:10]
    assert "FFMPEG" not in names[:10]
    assert "NPZ" not in names[:10]


def test_bad_formats(tmp_path):
    # test looking up a read format from file
    bogus_file = tmp_path / "bogus.fil"
    bogus_file.write_text("abcdefg")

    with pytest.raises(IndexError):
        iio.formats[str(bogus_file)]

    # test empty format
    with pytest.raises(ValueError):
        iio.formats[""]


def test_write_format_search_fail(tmp_path):
    req = iio.core.Request(tmp_path / "foo.bogus", "w")
    assert iio.formats.search_write_format(req) is None


def test_format_by_filename():
    iio.formats["test.jpg"]


run_tests_if_main()
