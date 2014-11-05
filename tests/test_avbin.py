""" Test imageio avbin functionality.
"""

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio
from imageio import core
from imageio.core import get_remote_file


test_dir = get_test_dir()


_prepared = None


def test_read():
    reader = imageio.read(get_remote_file('images/cockatoo.mp4', 
                                          force_download='2014-11-05'))
    assert reader.get_length() == 280
    assert 'fps' in reader.get_meta_data()
    assert not reader.format.can_save(core.Request('test.mp4', 'wI'))
    
    for i in range(10):
        im = reader.get_next_data()
        assert im.shape == (720, 1280, 3)
        if i > 5:
            # Weird, avbin seems to need some time to warm up?
            assert im.mean() > 0
    
    # We can rewind
    reader.get_next_data()
    
    # But not seek
    with raises(IndexError):    
        reader.get_data(1)


def test_reader_more():
    
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
    
    # Test  loop
    R = imageio.read(get_remote_file('images/realshort.mp4'), 'avbin', loop=1)
    im1 = R.get_next_data()
    for i in range(1, len(R)):
        R.get_next_data()
    im2 = R.get_next_data()
    im3 = R.get_data(0)
    assert (im1 == im2).all()
    assert (im1 == im3).all()
    R.close()
    
    # Read invalid
    open(fname3, 'wb')
    raises(IOError, imageio.read, fname3, 'avbin')


def test_read_format():
    reader = imageio.read(get_remote_file('images/cockatoo.mp4'), 
                          videoformat='mp4')
    for i in range(10):
        reader.get_next_data()
 
 
def test_stream():
    with raises(IOError):
        imageio.read(get_remote_file('images/cockatoo.mp4'), stream=5)
  
  
def test_invalidfile():
    filename = test_dir+'/empty.mp4'
    with open(filename, 'w'):
        pass
    
    with raises(IOError):
        imageio.read(filename)
    
    # Check AVbinResult
    imageio.plugins.avbin.AVbinResult(imageio.plugins.avbin.AVBIN_RESULT_OK)
    for i in (2, 3, 4):
        with raises(RuntimeError):
            imageio.plugins.avbin.AVbinResult(i)


def test_format_selection():
    # AVBIN is default format for reading video
    
    F = imageio.formats['AVBIN']
    assert F.name == 'AVBIN'
    
    R = imageio.read(get_remote_file('images/cockatoo.mp4'))
    assert R.format is F
    assert imageio.formats['.mp4'] is F


def show():
    reader = imageio.read('cockatoo.mp4')
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
