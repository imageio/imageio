""" Test ffmpeg

"""

from io import BytesIO
import time
import threading

import numpy as np

from pytest import raises, skip
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import get_remote_file, IS_PYPY

test_dir = get_test_dir()


def test_select():
    
    fname1 = get_remote_file('images/cockatoo.mp4', test_dir)
    
    F = imageio.formats['ffmpeg']
    assert F.name == 'FFMPEG'
    
    assert F.can_read(core.Request(fname1, 'rI'))
    assert F.can_write(core.Request(fname1, 'wI'))
    assert not F.can_read(core.Request(fname1, 'ri'))
    assert not F.can_read(core.Request(fname1, 'rv'))

    # ffmpeg is default
    assert imageio.formats['.mp4'] is F
    assert imageio.formats.search_write_format(core.Request(fname1, 'wI')) is F
    assert imageio.formats.search_read_format(core.Request(fname1, 'rI')) is F

    
def test_read_and_write():
    need_internet()
    
    R = imageio.read(get_remote_file('images/cockatoo.mp4'), 'ffmpeg')
    assert R.format is imageio.formats['ffmpeg']
    
    fname1 = get_remote_file('images/cockatoo.mp4', test_dir)
    fname2 = fname1[:-4] + '.out.mp4'
    
    # Read
    ims1 = []
    with imageio.read(fname1, 'ffmpeg') as R:
        for i in range(10):
            im = R.get_next_data()
            ims1.append(im)
            assert im.shape == (720, 1280, 3)
            assert (im.sum() / im.size) > 0  # pypy mean is broken
        assert im.sum() > 0
    
        # Seek
        im = R.get_data(120)
        assert im.shape == (720, 1280, 3)
    
    # Save
    with imageio.save(fname2, 'ffmpeg') as W:
        for im in ims1:
            W.append_data(im)
    
    # Read the result
    ims2 = imageio.mimread(fname2, 'ffmpeg')
    assert len(ims1) == len(ims2)
    
    # Check
    for im1, im2 in zip(ims1, ims2):
        diff = np.abs(im1.astype(np.float32) - im2.astype(np.float32))
        if IS_PYPY:
            assert (diff.sum() / diff.size) < 100
        else:
            assert diff.mean() < 2.0


def test_reader_more():
    need_internet()
    
    fname1 = get_remote_file('images/cockatoo.mp4', test_dir)
    fname3 = fname1[:-4] + '.stub.mp4'
    
    # Get meta data
    R = imageio.read(fname1, 'ffmpeg', loop=True)
    meta = R.get_meta_data()
    assert len(R) == 280
    assert isinstance(meta, dict)
    assert 'fps' in meta
    R.close()
    
    # Test size argument
    im = imageio.read(fname1, 'ffmpeg', size=(50, 50)).get_data(0)
    assert im.shape == (50, 50, 3)
    im = imageio.read(fname1, 'ffmpeg', size='40x40').get_data(0)
    assert im.shape == (40, 40, 3)
    raises(ValueError, imageio.read, fname1, 'ffmpeg', size=20)
    raises(ValueError, imageio.read, fname1, 'ffmpeg', pixelformat=20)
    
    # Read all frames and test length
    R = imageio.read(get_remote_file('images/realshort.mp4'), 'ffmpeg')
    count = 0
    while True:
        try:
            R.get_next_data()
        except IndexError:
            break
        else:
            count += 1
    assert count == len(R)
    assert count in (35, 36)  # allow one frame off size that we know
    # Test index error -1
    raises(IndexError, R.get_data, -1)
    # Now read beyond (simulate broken file)
    with raises(RuntimeError):
        R._read_frame()  # ffmpeg seems to have an extra frame, avbin not?
        R._read_frame()
    
    # Test  loop
    R = imageio.read(get_remote_file('images/realshort.mp4'), 'ffmpeg', loop=1)
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
    open(fname3, 'wb')
    raises(IOError, imageio.read, fname3, 'ffmpeg')
    
    # Read printing info
    imageio.read(fname1, 'ffmpeg', print_info=True)


def test_writer_more():
    need_internet()
    
    fname1 = get_remote_file('images/cockatoo.mp4', test_dir)
    fname2 = fname1[:-4] + '.out.mp4'
    
    W = imageio.save(fname2, 'ffmpeg')
    with raises(ValueError):  # Invalid shape
        W.append_data(np.zeros((20, 20, 5), np.uint8))
    W.append_data(np.zeros((20, 20, 3), np.uint8))
    with raises(ValueError):  # Different shape from first image
        W.append_data(np.zeros((20, 19, 3), np.uint8))
    with raises(ValueError):  # Different depth from first image
        W.append_data(np.zeros((20, 20, 4), np.uint8))
    with raises(RuntimeError):  # No meta data
        W.set_meta_data({'foo': 3})
    W.close()


def test_cvsecs():
    
    cvsecs = imageio.plugins.ffmpeg.cvsecs
    assert cvsecs(20) == 20
    assert cvsecs(2, 20) == (2 * 60) + 20
    assert cvsecs(2, 3, 20) == (2 * 3600) + (3 * 60) + 20


def test_limit_lines():
    limit_lines = imageio.plugins.ffmpeg.limit_lines
    lines = ['foo'] * 10
    assert len(limit_lines(lines)) == 10
    lines = ['foo'] * 50
    assert len(limit_lines(lines)) == 50  # < 2 * N
    lines = ['foo'] * 70 + ['bar']
    lines2 = limit_lines(lines)
    assert len(lines2) == 33  # > 2 * N
    assert b'last few lines' in lines2[0]
    assert 'bar' == lines2[-1]


def test_framecatcher():
    
    class BlockingBytesIO(BytesIO):
        def __init__(self):
            BytesIO.__init__(self)
            self._lock = threading.RLock()
        
        def write_and_rewind(self, bb):
            with self._lock:
                t = self.tell()
                self.write(bb)
                self.seek(t)
        
        def read(self, n):
            if self.closed:
                return b''
            while True:
                time.sleep(0.001)
                with self._lock:
                    bb = BytesIO.read(self, n)
                if bb:
                    return bb
    
    # Test our class
    file = BlockingBytesIO()
    file.write_and_rewind(b'v')
    assert file.read(100) == b'v'
    
    file = BlockingBytesIO()
    N = 100
    T = imageio.plugins.ffmpeg.FrameCatcher(file, N)
    
    # Init None
    time.sleep(0.1)
    assert T._frame is None  # get_frame() would stall
    
    # Read frame
    file.write_and_rewind(b'x' * (N - 20))
    time.sleep(0.2)  # Let it read a part
    assert T._frame is None  # get_frame() would stall
    file.write_and_rewind(b'x' * 20)
    time.sleep(0.2)  # Let it read the rest
    assert T.get_frame() == b'x' * N
    # Read frame when we pass plenty of data
    file.write_and_rewind(b'y' * N * 3)
    time.sleep(0.2)
    assert T.get_frame() == b'y' * N
    # Close
    file.close()


def test_webcam():
    need_internet()
    
    try:
        imageio.read('<video2>')
    except Exception:
        skip('no web cam')


def show_in_console():
    reader = imageio.read('cockatoo.mp4', 'ffmpeg')
    #reader = imageio.read('<video0>')
    im = reader.get_next_data()
    while True:
        im = reader.get_next_data()
        print('frame min/max/mean: %1.1f / %1.1f / %1.1f' % 
              (im.min(), im.max(), (im.sum() / im.size)))


def show_in_visvis():
    reader = imageio.read('cockatoo.mp4', 'ffmpeg')
    #reader = imageio.read('<video0>')
    
    import visvis as vv
    im = reader.get_next_data()
    f = vv.clf()
    f.title = reader.format.name
    t = vv.imshow(im, clim=(0, 255))
    
    while not f._destroyed:
        t.SetData(reader.get_next_data())
        vv.processEvents()


if __name__ == '__main__':
    run_tests_if_main()
    #reader = imageio.read('cockatoo.mp4', 'ffmpeg')
