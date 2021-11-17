""" Test ffmpeg

"""

from io import BytesIO
import os
import sys
import gc
import time
import threading
import platform
import psutil

import numpy as np

from pytest import raises, skip
from imageio.testing import run_tests_if_main, get_test_dir

import imageio
from imageio import core
from imageio.core import get_remote_file, IS_PYPY

test_dir = get_test_dir()


def get_ffmpeg_pids():
    pids = set()
    for p in psutil.process_iter():
        if "ffmpeg" in p.name().lower():
            pids.add(p.pid)
    return pids


def setup_module():
    pass


def test_get_exe_installed():
    if platform.machine() == "aarch64":
        skip("Skip for aarch64")
    else:
        import imageio_ffmpeg

        # backup any user-defined path
        if "IMAGEIO_FFMPEG_EXE" in os.environ:
            oldpath = os.environ["IMAGEIO_FFMPEG_EXE"]
        else:
            oldpath = ""
        # Test if download works
        os.environ["IMAGEIO_FFMPEG_EXE"] = ""
        path = imageio_ffmpeg.get_ffmpeg_exe()
        # cleanup
        os.environ.pop("IMAGEIO_FFMPEG_EXE")
        if oldpath:
            os.environ["IMAGEIO_FFMPEG_EXE"] = oldpath
        print(path)
        assert os.path.isfile(path)


def test_get_exe_env():
    import imageio_ffmpeg

    # backup any user-defined path
    if "IMAGEIO_FFMPEG_EXE" in os.environ:
        oldpath = os.environ["IMAGEIO_FFMPEG_EXE"]
    else:
        oldpath = ""
    # set manual path
    path = "invalid/path/to/my/ffmpeg"
    os.environ["IMAGEIO_FFMPEG_EXE"] = path
    try:
        path2 = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        path2 = "none"
        pass
    # cleanup
    os.environ.pop("IMAGEIO_FFMPEG_EXE")
    if oldpath:
        os.environ["IMAGEIO_FFMPEG_EXE"] = oldpath
    assert path == path2


def test_select():

    fname1 = get_remote_file("images/cockatoo.mp4", test_dir)

    F = imageio.formats["ffmpeg"]
    assert F.name == "FFMPEG"

    assert F.can_read(core.Request(fname1, "rI"))
    assert F.can_write(core.Request(fname1, "wI"))
    assert not F.can_read(core.Request(fname1, "ri"))
    assert not F.can_read(core.Request(fname1, "rv"))

    # ffmpeg is default
    assert type(imageio.formats[".mp4"]) is type(F)
    assert type(
        imageio.formats.search_write_format(core.Request(fname1, "wI"))
    ) is type(F)
    assert type(imageio.formats.search_read_format(core.Request(fname1, "rI"))) is type(
        F
    )


def test_integer_reader_length():
    # Avoid regression for #280
    r = imageio.get_reader("imageio:cockatoo.mp4")
    assert r.get_length() == float("inf")
    assert isinstance(len(r), int)
    assert len(r) == sys.maxsize
    assert bool(r)
    assert True if r else False


def test_read_and_write():

    R = imageio.read(get_remote_file("images/cockatoo.mp4"), "ffmpeg")
    assert isinstance(R.format, type(imageio.formats["ffmpeg"]))

    fname1 = get_remote_file("images/cockatoo.mp4", test_dir)
    fname2 = fname1[:-4] + ".out.mp4"

    frame1, frame2, frame3 = 41, 131, 227

    # Read
    ims1 = []
    with imageio.read(fname1, "ffmpeg") as R:
        for i in range(10):
            im = R.get_next_data()
            ims1.append(im)
            assert im.shape == (720, 1280, 3)
            assert (im.sum() / im.size) > 0  # pypy mean is broken
        assert im.sum() > 0

        # Seek to reference frames in steps. OUR code will skip steps
        im11 = R.get_data(frame1)
        im12 = R.get_data(frame2)
        im13 = R.get_data(frame3)

        # Now go backwards, seek will kick in
        R.get_next_data()
        im23 = R.get_data(frame3)
        im22 = R.get_data(frame2)
        im21 = R.get_data(frame1)

        # Also use set_image_index
        R.set_image_index(frame2)
        im32 = R.get_next_data()
        R.set_image_index(frame3)
        im33 = R.get_next_data()
        R.set_image_index(frame1)
        im31 = R.get_next_data()

        for im in (im11, im12, im13, im21, im22, im23, im31, im32, im33):
            assert im.shape == (720, 1280, 3)

        assert (im11 == im21).all() and (im11 == im31).all()
        assert (im12 == im22).all() and (im12 == im32).all()
        assert (im13 == im23).all() and (im13 == im33).all()

        assert not (im11 == im12).all()
        assert not (im11 == im13).all()

    # Save
    with imageio.save(fname2, "ffmpeg") as W:
        for im in ims1:
            W.append_data(im)

    # Read the result
    ims2 = imageio.mimread(fname2, "ffmpeg")
    assert len(ims1) == len(ims2)
    for im in ims2:
        assert im.shape == (720, 1280, 3)

    # Check
    for im1, im2 in zip(ims1, ims2):
        diff = np.abs(im1.astype(np.float32) - im2.astype(np.float32))
        if IS_PYPY:
            assert (diff.sum() / diff.size) < 100
        else:
            assert diff.mean() < 2.5


def test_write_not_contiguous():

    R = imageio.read(get_remote_file("images/cockatoo.mp4"), "ffmpeg")
    assert isinstance(R.format, type(imageio.formats["ffmpeg"]))

    fname1 = get_remote_file("images/cockatoo.mp4", test_dir)
    fname2 = fname1[:-4] + ".out.mp4"

    # Read
    ims1 = []
    with imageio.read(fname1, "ffmpeg") as R:
        for i in range(10):
            im = R.get_next_data()
            ims1.append(im)

    # Save non contiguous data
    with imageio.save(fname2, "ffmpeg") as W:
        for im in ims1:
            # DOn't slice the first dimension since it won't be
            # a multiple of 16. This will cause the writer to expand
            # the data to make it fit, we won't be able to compare
            # the difference between the saved and the original images.
            im = im[:, ::2]
            assert not im.flags.c_contiguous
            W.append_data(im)

    ims2 = imageio.mimread(fname2, "ffmpeg")

    # Check
    for im1, im2 in zip(ims1, ims2):
        diff = np.abs(im1[:, ::2].astype(np.float32) - im2.astype(np.float32))
        if IS_PYPY:
            assert (diff.sum() / diff.size) < 100
        else:
            assert diff.mean() < 2.5


def test_reader_more():

    fname1 = get_remote_file("images/cockatoo.mp4", test_dir)
    fname3 = fname1[:-4] + ".stub.mp4"

    # Get meta data
    R = imageio.read(fname1, "ffmpeg", loop=True)
    meta = R.get_meta_data()
    assert len(R) == 280
    assert isinstance(meta, dict)
    assert "fps" in meta
    R.close()

    # Test size argument
    im = imageio.read(fname1, "ffmpeg", size=(50, 50)).get_data(0)
    assert im.shape == (50, 50, 3)
    im = imageio.read(fname1, "ffmpeg", size="40x40").get_data(0)
    assert im.shape == (40, 40, 3)
    raises(ValueError, imageio.read, fname1, "ffmpeg", size=20)
    raises(ValueError, imageio.read, fname1, "ffmpeg", pixelformat=20)

    # Read all frames and test length
    R = imageio.read(get_remote_file("images/realshort.mp4"), "ffmpeg")
    count = 0
    while True:
        try:
            R.get_next_data()
        except IndexError:
            break
        else:
            count += 1
    assert count == R.count_frames()
    assert count in (35, 36)  # allow one frame off size that we know
    raises(IndexError, R.get_data, -1)  # Test index error -1

    # Now read beyond (simulate broken file)
    with raises(StopIteration):
        R._read_frame()  # ffmpeg seems to have an extra frame
        R._read_frame()

    # Set the image index to 0 and go again
    R.set_image_index(0)
    count2 = 0
    while True:
        try:
            R.get_next_data()
        except IndexError:
            break
        else:
            count2 += 1
    assert count2 == count
    raises(IndexError, R.get_data, -1)  # Test index error -1

    # Test loop
    R = imageio.read(get_remote_file("images/realshort.mp4"), "ffmpeg", loop=1)
    im1 = R.get_next_data()
    for i in range(1, len(R)):
        R.get_next_data()
    im2 = R.get_next_data()
    im3 = R.get_data(0)
    im4 = R.get_data(2)  # touch skipping frames
    assert (im1 == im2).all()
    assert (im1 == im3).all()
    assert not (im1 == im4).all()
    R.close()

    # Read invalid
    open(fname3, "wb")
    raises(IOError, imageio.read, fname3, "ffmpeg")

    # Read printing info
    imageio.read(fname1, "ffmpeg", print_info=True)


def test_writer_more():

    fname1 = get_remote_file("images/cockatoo.mp4", test_dir)
    fname2 = fname1[:-4] + ".out.mp4"

    W = imageio.save(fname2, "ffmpeg")
    with raises(ValueError):  # Invalid shape
        W.append_data(np.zeros((20, 20, 5), np.uint8))
    W.append_data(np.zeros((20, 20, 3), np.uint8))
    with raises(ValueError):  # Different shape from first image
        W.append_data(np.zeros((20, 19, 3), np.uint8))
    with raises(ValueError):  # Different depth from first image
        W.append_data(np.zeros((20, 20, 4), np.uint8))
    with raises(RuntimeError):  # No meta data
        W.set_meta_data({"foo": 3})
    W.close()


def test_writer_file_properly_closed(tmpdir):
    # Test to catch if file is correctly closed.
    # Otherwise it won't play in most players. This seems to occur on windows.
    tmpf = tmpdir.join("test.mp4")
    W = imageio.get_writer(str(tmpf))
    for i in range(12):
        W.append_data(np.zeros((100, 100, 3), np.uint8))
    W.close()
    W = imageio.get_reader(str(tmpf))
    # If Duration: N/A reported by ffmpeg, then the file was not
    # correctly closed.
    # This will cause the file to not be readable in many players.
    assert 1.1 < W._meta["duration"] < 1.3


def test_writer_pixelformat_size_verbose(tmpdir):
    # Check that video pixel format and size get written as expected.

    # Make sure verbose option works and that default pixelformat is yuv420p
    tmpf = tmpdir.join("test.mp4")
    W = imageio.get_writer(str(tmpf), ffmpeg_log_level="warning")
    nframes = 4  # Number of frames in video
    for i in range(nframes):
        # Use size divisible by 16 or it gets changed.
        W.append_data(np.zeros((64, 64, 3), np.uint8))
    W.close()

    # Check that video is correct size & default output video pixel format
    # is correct
    W = imageio.get_reader(str(tmpf))
    assert W.count_frames() == nframes
    assert W._meta["size"] == (64, 64)
    assert "yuv420p" == W._meta["pix_fmt"]

    # Now check that macroblock size gets turned off if requested
    W = imageio.get_writer(str(tmpf), macro_block_size=1, ffmpeg_log_level="warning")
    for i in range(nframes):
        W.append_data(np.zeros((100, 106, 3), np.uint8))
    W.close()
    W = imageio.get_reader(str(tmpf))
    assert W.count_frames() == nframes
    assert W._meta["size"] == (106, 100)
    assert "yuv420p" == W._meta["pix_fmt"]

    # Now double check values different than default work
    W = imageio.get_writer(str(tmpf), macro_block_size=4, ffmpeg_log_level="warning")
    for i in range(nframes):
        W.append_data(np.zeros((64, 65, 3), np.uint8))
    W.close()
    W = imageio.get_reader(str(tmpf))
    assert W.count_frames() == nframes
    assert W._meta["size"] == (68, 64)
    assert "yuv420p" == W._meta["pix_fmt"]

    # Now check that the macroblock works as expected for the default of 16
    W = imageio.get_writer(str(tmpf), ffmpeg_log_level="debug")
    for i in range(nframes):
        W.append_data(np.zeros((111, 140, 3), np.uint8))
    W.close()
    W = imageio.get_reader(str(tmpf))
    assert W.count_frames() == nframes
    # Check for warning message with macroblock
    assert W._meta["size"] == (144, 112)
    assert "yuv420p" == W._meta["pix_fmt"]


def test_writer_ffmpeg_params(tmpdir):
    # Test optional ffmpeg_params with a valid option
    # Also putting in an image size that is not divisible by macroblock size
    # To check that the -vf scale overwrites what it does.
    tmpf = tmpdir.join("test.mp4")
    W = imageio.get_writer(str(tmpf), ffmpeg_params=["-vf", "scale=320:240"])
    for i in range(10):
        W.append_data(np.zeros((100, 100, 3), np.uint8))
    W.close()
    W = imageio.get_reader(str(tmpf))
    # Check that the optional argument scaling worked.
    assert W._meta["size"] == (320, 240)


def test_writer_wmv(tmpdir):
    # WMV has different default codec, make sure it works.
    tmpf = tmpdir.join("test.wmv")
    W = imageio.get_writer(str(tmpf), ffmpeg_params=["-v", "info"])
    for i in range(10):
        W.append_data(np.zeros((100, 100, 3), np.uint8))
    W.close()

    W = imageio.get_reader(str(tmpf))
    # Check that default encoder is msmpeg4 for wmv
    assert W._meta["codec"].startswith("msmpeg4")


def test_framecatcher():
    class FakeGenerator:
        def __init__(self, nframebytes):
            self._f = BytesIO()
            self._n = nframebytes
            self._lock = threading.RLock()
            self._bb = b""

        def write_and_rewind(self, bb):
            with self._lock:
                t = self._f.tell()
                self._f.write(bb)
                self._f.seek(t)

        def __next__(self):
            while True:
                time.sleep(0.001)
                with self._lock:
                    if self._f.closed:
                        raise StopIteration()
                    self._bb += self._f.read(self._n)
                if len(self._bb) >= self._n:
                    bb = self._bb[: self._n]
                    self._bb = self._bb[self._n :]
                    return bb

        def close(self):
            with self._lock:
                self._f.close()

    # Test our class
    N = 100
    file = FakeGenerator(N)
    file.write_and_rewind(b"v" * N)
    assert file.__next__() == b"v" * N

    file = FakeGenerator(N)
    T = imageio.plugins.ffmpeg.FrameCatcher(file)  # the file looks like a generator

    # Init None
    time.sleep(0.1)
    assert T._frame is None  # get_frame() would stall

    # Read frame
    file.write_and_rewind(b"x" * (N - 20))
    time.sleep(0.2)  # Let it read a part
    assert T._frame is None  # get_frame() would stall
    file.write_and_rewind(b"x" * 20)
    time.sleep(0.2)  # Let it read the rest
    frame, is_new = T.get_frame()
    assert frame == b"x" * N
    assert is_new, "is_new should be True the first time a frame is retrieved"

    # Read frame that has not been updated
    frame, is_new = T.get_frame()
    assert frame == b"x" * N, "frame content should be the same as before"
    assert not is_new, "is_new should be False if the frame has already been retrieved"

    # Read frame when we pass plenty of data
    file.write_and_rewind(b"y" * N * 3)
    time.sleep(0.2)
    frame, is_new = T.get_frame()
    assert frame == b"y" * N
    assert is_new, "is_new should be True again if the frame has been updated"

    # Close
    file.close()


def test_webcam():
    good_paths = ["<video0>", "<video42>"]
    for path in good_paths:
        # regression test for https://github.com/imageio/imageio/issues/676
        tmp_request = imageio.core.Request(path, "rI")
        assert imageio.formats["ffmpeg"].can_read(tmp_request)
        tmp_request.finish()

        try:
            imageio.read(path, format="ffmpeg")
        except IndexError:
            # IndexError should be raised when
            # path string is good but camera doesnt exist
            continue

    bad_paths = ["<videof1>", "<video0x>", "<video>"]
    for path in bad_paths:
        with raises(ValueError):
            imageio.read(path)


def test_webcam_get_next_data():
    try:
        reader = imageio.get_reader("<video0>")
    except IndexError:
        skip("no webcam")

    # Get a number of frames and check for if they are new
    counter_new_frames = 0
    number_of_iterations = 100
    for i in range(number_of_iterations):
        frame = reader.get_next_data()
        if frame.meta["new"]:
            counter_new_frames += 1

    assert counter_new_frames < number_of_iterations, (
        "assuming the loop is faster than the webcam, the number of unique "
        "frames should be smaller than the number of iterations"
    )
    reader.close()


def test_process_termination():

    pids0 = get_ffmpeg_pids()

    r1 = imageio.get_reader("imageio:cockatoo.mp4")
    r2 = imageio.get_reader("imageio:cockatoo.mp4")

    assert len(get_ffmpeg_pids().difference(pids0)) == 2

    r1.close()
    r2.close()

    assert len(get_ffmpeg_pids().difference(pids0)) == 0

    r1 = imageio.get_reader("imageio:cockatoo.mp4")
    r2 = imageio.get_reader("imageio:cockatoo.mp4")

    assert len(get_ffmpeg_pids().difference(pids0)) == 2

    del r1
    del r2
    gc.collect()

    assert len(get_ffmpeg_pids().difference(pids0)) == 0


def test_webcam_process_termination():
    """
    Test for issue #343. Ensures that an ffmpeg process streaming from
    webcam is terminated properly when the reader is closed.

    """

    pids0 = get_ffmpeg_pids()

    try:
        # Open the first webcam found.
        with imageio.get_reader("<video0>") as reader:
            assert reader._read_gen is not None
            assert get_ffmpeg_pids().difference(pids0)
        # Ensure that the corresponding ffmpeg process has been terminated.
        assert reader._read_gen is None
        assert not get_ffmpeg_pids().difference(pids0)
    except IndexError:
        skip("no webcam")


def show_in_console():
    reader = imageio.read("imageio:cockatoo.mp4", "ffmpeg")
    # reader = imageio.read('<video0>')
    im = reader.get_next_data()
    while True:
        im = reader.get_next_data()
        print(
            "frame min/max/mean: %1.1f / %1.1f / %1.1f"
            % (im.min(), im.max(), (im.sum() / im.size))
        )


def show_in_visvis():
    # reader = imageio.read("imageio:cockatoo.mp4", "ffmpeg")
    reader = imageio.read("<video0>", fps=20)

    import visvis as vv

    im = reader.get_next_data()
    f = vv.clf()
    f.title = reader.format.name
    t = vv.imshow(im, clim=(0, 255))

    while not f._destroyed:
        im = reader.get_next_data()
        if im.meta["new"]:
            t.SetData(im)
        vv.processEvents()


def test_reverse_read(tmpdir):
    # Ensure we can read a file in reverse without error.

    tmpf = tmpdir.join("test_vid.mp4")
    W = imageio.get_writer(str(tmpf))
    for i in range(120):
        W.append_data(np.zeros((64, 64, 3), np.uint8))
    W.close()

    W = imageio.get_reader(str(tmpf))
    for i in range(W.count_frames() - 1, 0, -1):
        print("reading", i)
        W.get_data(i)
    W.close()


if __name__ == "__main__":
    run_tests_if_main()
    # reader = imageio.read('cockatoo.mp4', 'ffmpeg')
