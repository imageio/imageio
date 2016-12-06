""" Test imageio avbin functionality.
"""

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import get_remote_file

# if IS_PYPY:
#     skip('AVBIn not supported on pypy')

test_dir = get_test_dir()

mean = lambda x: x.sum() / x.size  # pypy-compat mean


def setup_module():
    try:
        imageio.plugins.avbin.download()
    except imageio.core.InternetNotAllowedError:
        pass


def test_select():
    
    fname1 = get_remote_file('images/cockatoo.mp4', test_dir)
    
    F = imageio.formats['avbin']
    assert F.name == 'AVBIN'
    
    assert F.can_read(core.Request(fname1, 'rI'))
    assert not F.can_write(core.Request(fname1, 'wI'))
    assert not F.can_read(core.Request(fname1, 'ri'))
    assert not F.can_read(core.Request(fname1, 'rv'))
    
    # ffmpeg is default
    #formats = imageio.formats
    #assert formats['.mp4'] is F
    #assert formats.search_write_format(core.Request(fname1, 'wI')) is F
    #assert formats.search_read_format(core.Request(fname1, 'rI')) is F


def test_read():
    need_internet()
    
    R = imageio.read(get_remote_file('images/cockatoo.mp4'), 'avbin')
    assert R.format is imageio.formats['avbin']
    
    fname = get_remote_file('images/cockatoo.mp4', force_download='2014-11-05')
    reader = imageio.read(fname, 'avbin')
    assert reader.get_length() == 280
    assert 'fps' in reader.get_meta_data()
    raises(Exception, imageio.save, '~/foo.mp4', 'abin')
    #assert not reader.format.can_write(core.Request('test.mp4', 'wI'))
    
    for i in range(10):
        im = reader.get_next_data()
        assert im.shape == (720, 1280, 3)
        # todo: fix this
        #assert mean(im) > 100 and mean(im) < 115  KNOWN FAIL
    
    # We can rewind
    reader.get_data(0)
    
    # But not seek
    with raises(IndexError):    
        reader.get_data(4)


def test_reader_more():
    need_internet()
    
    fname1 = get_remote_file('images/cockatoo.mp4')
    fname3 = fname1[:-4] + '.stub.mp4'
    
    # Get meta data
    R = imageio.read(fname1, 'avbin', loop=True)
    meta = R.get_meta_data()
    assert isinstance(meta, dict)
    assert 'fps' in meta
    R.close()
    
    # Read all frames and test length
    R = imageio.read(get_remote_file('images/realshort.mp4'), 'avbin')
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
    
    # Test loop
    R = imageio.read(get_remote_file('images/realshort.mp4'), 'avbin', loop=1)
    im1 = R.get_next_data()
    for i in range(1, len(R)):
        R.get_next_data()
    im2 = R.get_next_data()
    im3 = R.get_data(0)
    assert (im1 == im2).all()
    assert (im1 == im3).all()
    R.close()
    
    # Test size when skipping empty frames, are there *any* valid frames?
    # todo: use mimread once 1) len(R) == inf, or 2) len(R) is correct
    R = imageio.read(get_remote_file('images/realshort.mp4'), 
                     'avbin', skipempty=True)
    ims = []
    with R:
        try: 
            while True:
                ims.append(R.get_next_data())
        except IndexError:
            pass
    assert len(ims) > 20  # todo: should be 35/36 but with skipempty ...
    
    # Read invalid
    open(fname3, 'wb')
    raises(IOError, imageio.read, fname3, 'avbin')


def test_read_format():
    need_internet()
    
    # Set videofomat
    # Also set skipempty, so we can test mean
    reader = imageio.read(get_remote_file('images/cockatoo.mp4'), 'avbin',
                          videoformat='mp4', skipempty=True)
    for i in range(10):
        im = reader.get_next_data()
        assert im.shape == (720, 1280, 3)
        assert mean(im) > 100 and mean(im) < 115


def test_stream():
    need_internet()
    
    with raises(IOError):
        imageio.read(get_remote_file('images/cockatoo.mp4'), 'avbin', stream=5)
  
  
def test_invalidfile():
    need_internet()
    
    filename = test_dir+'/empty.mp4'
    with open(filename, 'w'):
        pass
    
    with raises(IOError):
        imageio.read(filename, 'avbin')
    
    # Check AVbinResult
    imageio.plugins.avbin.AVbinResult(imageio.plugins.avbin.AVBIN_RESULT_OK)
    for i in (2, 3, 4):
        with raises(RuntimeError):
            imageio.plugins.avbin.AVbinResult(i)


def show_in_mpl():
    reader = imageio.read('cockatoo.mp4', 'avbin')
    for i in range(10):
        reader.get_next_data()
       
    import pylab
    pylab.ion()
    pylab.show(reader.get_next_data())


def show_in_visvis():
    reader = imageio.read('cockatoo.mp4', 'avbin')
    #reader = imageio.read('<video0>')
    
    import visvis as vv
    im = reader.get_next_data()
    f = vv.clf()
    f.title = reader.format.name
    t = vv.imshow(im, clim=(0, 255))
    
    while not f._destroyed:
        t.SetData(reader.get_next_data())
        vv.processEvents()
    

run_tests_if_main()
