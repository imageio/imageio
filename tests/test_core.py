""" Test imageio core functionality.
"""

import time
import sys
import os
import shutil
import ctypes.util
from zipfile import ZipFile
from io import BytesIO

import numpy as np

from pytest import raises, skip
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import Request
from imageio.core import get_remote_file, IS_PYPY

test_dir = get_test_dir()


def test_fetching():
    """ Test fetching of files """
    
    need_internet()
    
    # Clear image files
    if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)   
    
    # This should download the file (force download, because local cache)
    fname1 = get_remote_file('images/chelsea.png', test_dir, True)
    mtime1 = os.path.getmtime(fname1)
    # This should reuse it
    fname2 = get_remote_file('images/chelsea.png', test_dir)
    mtime2 = os.path.getmtime(fname2)
    # This should overwrite
    fname3 = get_remote_file('images/chelsea.png', test_dir, True)
    mtime3 = os.path.getmtime(fname3)
    # This should too (update this if imageio is still around in 1000 years)
    fname4 = get_remote_file('images/chelsea.png', test_dir, '3014-01-01')
    mtime4 = os.path.getmtime(fname4)
    # This should not
    fname5 = get_remote_file('images/chelsea.png', test_dir, '2014-01-01')
    mtime5 = os.path.getmtime(fname4)
    # 
    assert os.path.isfile(fname1)
    assert fname1 == fname2
    assert fname1 == fname3
    assert fname1 == fname4
    assert fname1 == fname5
    if not sys.platform.startswith('darwin'):
        # weird, but these often fail on my osx VM
        assert mtime1 == mtime2
        assert mtime1 < mtime3
        assert mtime3 < mtime4  
        assert mtime4 == mtime5
    
    # Test failures
    _urlopen = core.fetching.urlopen
    _chunk_read = core.fetching._chunk_read
    #
    raises(IOError, get_remote_file, 'this_does_not_exist', test_dir)
    #
    try:
        core.fetching.urlopen = None
        raises(IOError, get_remote_file, 'images/chelsea.png', None, True)
    finally:
        core.fetching.urlopen = _urlopen
    #
    try:
        core.fetching._chunk_read = None
        raises(IOError, get_remote_file, 'images/chelsea.png', None, True)
    finally:
        core.fetching._chunk_read = _chunk_read
    #
    try:
        os.environ['IMAGEIO_NO_INTERNET'] = '1'
        raises(IOError, get_remote_file, 'images/chelsea.png', None, True)
    finally:
        del os.environ['IMAGEIO_NO_INTERNET']
    # Coverage miss
    assert '0 bytes' == core.fetching._sizeof_fmt(0)


def test_findlib1():
    
    # Lib name would need to be "libc.so.5", or "libc.so.6", or ...
    # Meh, just skip
    skip('always skip, is tested implicitly anyway')
    
    if not sys.platform.startswith('linux'):
        skip('test on linux only')
    
    # Candidate libs for common lib (note, this runs only on linux)
    dirs, paths = core.findlib.generate_candidate_libs(['libc'])
    assert paths


def test_findlib2():
    
    if not sys.platform.startswith('linux'):
        skip('test on linux only')
    
    need_internet()  # need our own version of FI to test this bit
    
    # Candidate libs for common freeimage
    fi_dir = os.path.join(core.appdata_dir('imageio'), 'freeimage')
    if not os.path.isdir(fi_dir):
        os.mkdir(fi_dir)
    dirs, paths = core.findlib.generate_candidate_libs(['libfreeimage'], 
                                                       [fi_dir])
    #assert fi_dir in dirs -> Cannot test: lib may not exist
    assert paths
    
    open(os.path.join(fi_dir, 'notalib.test.so'), 'wb')
    
    # Loading libs
    gllib = ctypes.util.find_library('GL')
    core.load_lib([gllib], [])
    core.load_lib([], ['libfreeimage'], [fi_dir])
    # Fail
    raises(ValueError, core.load_lib, [], [])  # Nothing given
    raises(ValueError, core.load_lib, ['', None], [])  # Nothing given
    raises(OSError, core.load_lib, ['thislibdoesnotexist_foobar'], [])
    raises(OSError, core.load_lib, [], ['notalib'], [fi_dir])


def test_request():
    """ Test request object """
    
    # Check uri-type, this is not a public property, so we test the private
    R = Request('http://example.com', 'ri')
    assert R._uri_type == core.request.URI_HTTP
    R = Request('ftp://example.com', 'ri')
    assert R._uri_type == core.request.URI_FTP
    R = Request('file://~/foo.png', 'wi')
    assert R._uri_type == core.request.URI_FILENAME
    R = Request('<video0>', 'rI')
    assert R._uri_type == core.request.URI_BYTES
    R = Request(imageio.RETURN_BYTES, 'wi')
    assert R._uri_type == core.request.URI_BYTES
    #
    fname = get_remote_file('images/chelsea.png', test_dir)
    R = Request(fname, 'ri')
    assert R._uri_type == core.request.URI_FILENAME
    R = Request('~/filethatdoesnotexist', 'wi')
    assert R._uri_type == core.request.URI_FILENAME  # Too short to be bytes
    R = Request(b'x'*600, 'ri')
    assert R._uri_type == core.request.URI_BYTES
    R = Request(sys.stdin, 'ri')
    assert R._uri_type == core.request.URI_FILE
    R = Request(sys.stdout, 'wi')
    assert R._uri_type == core.request.URI_FILE
    # exapand user dir
    R = Request('~/foo', 'wi')
    assert R.filename == os.path.expanduser('~/foo').replace('/', os.path.sep)
    # zip file
    R = Request('~/bar.zip/spam.png', 'wi')
    assert R._uri_type == core.request.URI_ZIPPED
    
    # Test failing inits
    raises(ValueError, Request, '/some/file', None)  # mode must be str
    raises(ValueError, Request, '/some/file', 3)  # mode must be str
    raises(ValueError, Request, '/some/file', '')  # mode must be len 2
    raises(ValueError, Request, '/some/file', 'r')  # mode must be len 2
    raises(ValueError, Request, '/some/file', 'rii')  # mode must be len 2
    raises(ValueError, Request, '/some/file', 'xi')  # mode[0] must be in rw
    raises(ValueError, Request, '/some/file', 'rx')  # mode[1] must be in iIvV?
    #
    raises(IOError, Request, ['invalid', 'uri'] * 10, 'ri')  # invalid uri
    raises(IOError, Request, 4, 'ri')  # invalid uri
    raises(IOError, Request, '/does/not/exist', 'ri')  # reading nonexistent
    raises(IOError, Request, '/does/not/exist.zip/spam.png', 'ri')  # dito
    raises(IOError, Request, 'http://example.com', 'wi')  # no writing here
    raises(IOError, Request, '/does/not/exist.png', 'wi')  # write dir nonexist
    
    # Test auto-download
    R = Request('imageio:chelsea.png', 'ri')
    assert R.filename == get_remote_file('images/chelsea.png')
    #
    R = Request('imageio:chelsea.zip/chelsea.png', 'ri')
    assert R._filename_zip[0] == get_remote_file('images/chelsea.zip')
    assert R.filename == get_remote_file('images/chelsea.zip') + '/chelsea.png'


def test_request_read_sources():
    
    # Make an image available in many ways
    fname = 'images/chelsea.png'
    filename = get_remote_file(fname, test_dir)
    bytes = open(filename, 'rb').read()
    #
    burl = 'https://raw.githubusercontent.com/imageio/imageio-binaries/master/'
    z = ZipFile(os.path.join(test_dir, 'test.zip'), 'w')
    z.writestr(fname, bytes)
    z.close()
    
    has_inet = os.getenv('IMAGEIO_NO_INTERNET', '') not in ('1', 'yes', 'true')
    
    # Read that image from these different sources. Read data from file
    # and from local file (the two main plugin-facing functions)
    for X in range(2):
        
        # Define uris to test. Define inside loop, since we need fresh files
        uris = [filename,
                os.path.join(test_dir, 'test.zip', fname),
                bytes,
                open(filename, 'rb')]
        if has_inet:
            uris.append(burl + fname)
        
        for uri in uris:
            R = Request(uri, 'ri')
            first_bytes = R.firstbytes
            if X == 0:
                all_bytes = R.get_file().read()
            else:
                f = open(R.get_local_filename(), 'rb')
                all_bytes = f.read()
            R.finish()
            # Test
            assert len(first_bytes) > 0
            assert all_bytes.startswith(first_bytes)
            assert bytes == all_bytes


def test_request_save_sources():
    
    # Prepare desinations
    fname = 'images/chelsea.png'
    filename = get_remote_file(fname, test_dir)
    bytes = open(filename, 'rb').read()
    #
    fname2 = fname + '.out'
    filename2 = os.path.join(test_dir, fname2)
    zipfilename2 = os.path.join(test_dir, 'test.zip')
    file2 = BytesIO()
    
    # Write an image into many different destinations
    # Do once via file and ones via local filename
    for i in range(2):
        # Clear
        for xx in (filename2, zipfilename2):
            if os.path.isfile(xx):
                os.remove(xx)
        # Write to three destinations
        for uri in (filename2, 
                    os.path.join(zipfilename2, fname2),
                    file2,
                    imageio.RETURN_BYTES  # This one last to fill `res`
                    ):
            R = Request(uri, 'wi')
            if i == 0:
                R.get_file().write(bytes)  # via file
            else:
                open(R.get_local_filename(), 'wb').write(bytes)  # via local
            R.finish()
            res = R.get_result()
        # Test three results
        assert open(filename2, 'rb').read() == bytes
        assert ZipFile(zipfilename2, 'r').open(fname2).read() == bytes
        assert res == bytes


def test_request_file_no_seek():
    
    class File():
        
        def read(self, n):
            return b'\x00' * n
            
        def seek(self, i):
            raise IOError('Not supported')
        
        def tell(self):
            raise Exception('Not supported')
        
        def close(self):
            pass
    
    R = Request(File(), 'ri')
    with raises(IOError):
        R.firstbytes


def test_util_imagelist():
    meta = {'foo': 3, 'bar': {'spam': 1, 'eggs': 2}}
    
    # Image list
    L = core.util.ImageList(meta)
    assert isinstance(L, list)
    assert L.meta == meta
    # Fail
    raises(ValueError, core.util.ImageList, 3)  # not a dict


def test_util_image():
    meta = {'foo': 3, 'bar': {'spam': 1, 'eggs': 2}}
    # Image 
    a = np.zeros((10, 10))
    im = core.util.Image(a, meta)
    isinstance(im, np.ndarray)
    isinstance(im.meta, dict)
    assert str(im) == str(a)
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
    #assert '2D image' in repr(core.util.Image(np.zeros((10, 10))))
    #assert '2D image' in repr(core.util.Image(np.zeros((10, 10, 3))))
    #assert '3D image' in repr(core.util.Image(np.zeros((10, 10, 10))))
    # Fail
    raises(ValueError, core.util.Image, 3)  # not a ndarray
    raises(ValueError, core.util.Image, a, 3)  # not a dict


def test_util_dict():
    # Dict class
    D = core.Dict()
    D['foo'] = 1
    D['bar'] = 2
    D['spam'] = 3
    assert list(D.values()) == [1, 2, 3]
    #
    assert D.spam == 3
    D.spam = 4
    assert D['spam'] == 4
    # Can still use copy etc.
    assert D.copy() == D
    assert 'spam' in D.keys()
    # Can also insert non-identifiers
    D[3] = 'not an identifier'
    D['34a'] = 'not an identifier'
    D[None] = 'not an identifier'
    # dir
    names = dir(D)
    assert 'foo' in names
    assert 'spam' in names
    assert 3 not in names
    assert '34a' not in names
    # Fail
    raises(AttributeError, D.__setattr__, 'copy', False)  # reserved
    raises(AttributeError, D.__getattribute__, 'notinD')


def test_util_get_platform():
    # Test get_platform
    platforms = 'win32', 'win64', 'linux32', 'linux64', 'osx32', 'osx64'
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
    """ Test the progress bar """
    # This test can also be run on itself to *see* the result
    
    # Progress bar
    for Progress in (core.StdoutProgressIndicator, core.BaseProgressIndicator):
        B = Progress('test')
        assert B.status() == 0
        B.start(max=20)
        assert B.status() == 1
        B.start('Run to 10', max=10)  # Restart
        for i in range(8):
            time.sleep(sleep)
            B.set_progress(i)
            assert B._progress == i
        B.increase_progress(1)
        assert B._progress == i + 1
        B.finish()  
        assert B.status() == 2
        # Without max
        B.start('Run without max int')
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(i)
        B.start('Run without float')
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(i+0.1)
        B.start('Run without progress')
        for i in range(15):
            time.sleep(sleep)
            B.set_progress(0)
        B.write('some message')
        B.fail('arg')
        assert B.status() == 3
        # Perc
        B.start('Run percentage', unit='%', max=100)  # Restart
        for i in range(0, 101, 5):
            time.sleep(sleep)
            B.set_progress(i)
        B.finish('Done')
        if sleep:
            return


def test_util_image_as_uint():
    ''' Tests the various type conversions when writing to uint'''
    raises(ValueError, core.image_as_uint, 4)
    raises(ValueError, core.image_as_uint, "not an image")
    raises(ValueError, core.image_as_uint, np.array([0, 1]), bitdepth=13)
    raises(ValueError, core.image_as_uint, np.array([2.0, 2.0], 'float32'))
    raises(ValueError, core.image_as_uint, np.array([0.0, np.inf], 'float32'))
    raises(ValueError, core.image_as_uint, np.array([-np.inf, 0.0], 'float32'))

    test_arrays = (  # (input, output bitdepth, expected output)
        # No bitdepth specified, assumed to be 8-bit
        (np.array([0, 2 ** 8 - 1], 'uint8'), None, np.uint8([0, 255])),
        (np.array([0, 2 ** 16 - 1], 'uint16'), None, np.uint8([0, 255])),
        (np.array([0, 2 ** 32 - 1], 'uint32'), None, np.uint8([0, 255])),
        (np.array([0, 2 ** 64 - 1], 'uint64'), None, np.uint8([0, 255])),
        (np.array([-2, 2], 'int8'), None, np.uint8([0, 255])),
        (np.array([-2, 2], 'int16'), None, np.uint8([0, 255])),
        (np.array([-2, 2], 'int32'), None, np.uint8([0, 255])),
        (np.array([-2, 2], 'int64'), None, np.uint8([0, 255])),
        (np.array([0, 1], 'float16'), None, np.uint8([0, 255])),
        (np.array([0, 1], 'float32'), None, np.uint8([0, 255])),
        (np.array([0, 1], 'float64'), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float16'), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float32'), None, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float64'), None, np.uint8([0, 255])),
        # 8-bit output
        (np.array([0, 2 ** 8 - 1], 'uint8'), 8, np.uint8([0, 255])),
        (np.array([0, 2 ** 16 - 1], 'uint16'), 8, np.uint8([0, 255])),
        (np.array([0, 2 ** 32 - 1], 'uint32'), 8, np.uint8([0, 255])),
        (np.array([0, 2 ** 64 - 1], 'uint64'), 8, np.uint8([0, 255])),
        (np.array([-2, 2], 'int8'), 8, np.uint8([0, 255])),
        (np.array([-2, 2], 'int16'), 8, np.uint8([0, 255])),
        (np.array([-2, 2], 'int32'), 8, np.uint8([0, 255])),
        (np.array([-2, 2], 'int64'), 8, np.uint8([0, 255])),
        (np.array([0, 1], 'float16'), 8, np.uint8([0, 255])),
        (np.array([0, 1], 'float32'), 8, np.uint8([0, 255])),
        (np.array([0, 1], 'float64'), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float16'), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float32'), 8, np.uint8([0, 255])),
        (np.array([-1.0, 1.0], 'float64'), 8, np.uint8([0, 255])),
        # 16-bit output
        (np.array([0, 2 ** 8 - 1], 'uint8'), 16, np.uint16([0, 65535])),
        (np.array([0, 2 ** 16 - 1], 'uint16'), 16, np.uint16([0, 65535])),
        (np.array([0, 2 ** 32 - 1], 'uint32'), 16, np.uint16([0, 65535])),
        (np.array([0, 2 ** 64 - 1], 'uint64'), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], 'int8'), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], 'int16'), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], 'int32'), 16, np.uint16([0, 65535])),
        (np.array([-2, 2], 'int64'), 16, np.uint16([0, 65535])),
        (np.array([0, 1], 'float16'), 16, np.uint16([0, 65535])),
        (np.array([0, 1], 'float32'), 16, np.uint16([0, 65535])),
        (np.array([0, 1], 'float64'), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], 'float16'), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], 'float32'), 16, np.uint16([0, 65535])),
        (np.array([-1.0, 1.0], 'float64'), 16, np.uint16([0, 65535])),)

    for tup in test_arrays:
        res = core.image_as_uint(tup[0], bitdepth=tup[1])
        assert res[0] == tup[2][0] and res[1] == tup[2][1]


def test_util_has_has_module():
    
    assert not core.has_module('this_module_does_not_exist')
    assert core.has_module('sys')


def test_functions():
    """ Test the user-facing API functions """
    
    # Test help(), it prints stuff, so we just check whether that goes ok
    imageio.help()  # should print overview
    imageio.help('PNG')  # should print about PNG
    
    fname1 = get_remote_file('images/chelsea.png', test_dir)
    fname2 = fname1[:-3] + 'jpg'
    fname3 = fname1[:-3] + 'notavalidext'
    open(fname3, 'wb')
    
    # Test read()
    R1 = imageio.read(fname1)
    R2 = imageio.read(fname1, 'png')
    assert R1.format is R2.format
    # Fail
    raises(ValueError, imageio.read, fname3)  # existing but not readable
    raises(IOError, imageio.read, 'notexisting.barf')
    raises(IndexError, imageio.read, fname1, 'notexistingformat')
    
    # Test save()
    W1 = imageio.save(fname2)
    W2 = imageio.save(fname2, 'JPG')
    W1.close()
    W2.close()
    assert W1.format is W2.format
    # Fail
    raises(IOError, imageio.save, '~/dirdoesnotexist/wtf.notexistingfile')
    
    # Test imread()
    im1 = imageio.imread(fname1)
    im2 = imageio.imread(fname1, 'png')
    assert im1.shape[2] == 3
    assert np.all(im1 == im2)
    
    # Test imsave()
    if os.path.isfile(fname2):
        os.remove(fname2)
    assert not os.path.isfile(fname2)
    imageio.imsave(fname2, im1[:, :, 0])
    imageio.imsave(fname2, im1)
    assert os.path.isfile(fname2)
    
    # Test mimread()
    fname3 = get_remote_file('images/newtonscradle.gif', test_dir)
    ims = imageio.mimread(fname3)
    assert isinstance(ims, list)
    assert len(ims) > 1
    assert ims[0].ndim == 3
    assert ims[0].shape[2] in (1, 3, 4)
    # Test protection
    with raises(RuntimeError):
        imageio.mimread('imageio:chelsea.png', 'dummy', length=np.inf)
    
    if IS_PYPY:
        return  # no support for npz format :(
    
    # Test mimsave()
    fname5 = fname3[:-4] + '2.npz'
    if os.path.isfile(fname5):
        os.remove(fname5)
    assert not os.path.isfile(fname5)
    imageio.mimsave(fname5, [im[:, :, 0] for im in ims])
    imageio.mimsave(fname5, ims)
    assert os.path.isfile(fname5)
    
    # Test volread()
    fname4 = get_remote_file('images/stent.npz', test_dir)
    vol = imageio.volread(fname4)
    assert vol.ndim == 3
    assert vol.shape[0] == 256
    assert vol.shape[1] == 128
    assert vol.shape[2] == 128
    
    # Test volsave()
    volc = np.zeros((10, 10, 10, 3), np.uint8)  # color volume
    fname6 = os.path.join(test_dir, 'images', 'stent2.npz')
    if os.path.isfile(fname6):
        os.remove(fname6)
    assert not os.path.isfile(fname6)
    imageio.volsave(fname6, volc)
    imageio.volsave(fname6, vol)
    assert os.path.isfile(fname6)
    
    # Test mvolread()
    vols = imageio.mvolread(fname4)
    assert isinstance(vols, list)
    assert len(vols) == 1
    assert vols[0].shape == vol.shape
    
    # Test mvolsave()
    if os.path.isfile(fname6):
        os.remove(fname6)
    assert not os.path.isfile(fname6)
    imageio.mvolsave(fname6, [volc, volc])
    imageio.mvolsave(fname6, vols)
    assert os.path.isfile(fname6)
    
    # Fail for save functions
    raises(ValueError, imageio.imsave, fname2, np.zeros((100, 100, 5)))
    raises(ValueError, imageio.imsave, fname2, 42)
    raises(ValueError, imageio.mimsave, fname5, [np.zeros((100, 100, 5))])
    raises(ValueError, imageio.mimsave, fname5, [42])
    raises(ValueError, imageio.volsave, fname6, np.zeros((100, 100, 100, 40)))
    raises(ValueError, imageio.volsave, fname6, 42)
    raises(ValueError, imageio.mvolsave, fname6, [np.zeros((90, 90, 90, 40))])
    raises(ValueError, imageio.mvolsave, fname6, [42])


def test_example_plugin():
    """ Test the example plugin """
    
    fname = os.path.join(test_dir, 'out.png')
    r = Request('imageio:chelsea.png', 'r?')
    R = imageio.formats['dummy'].get_reader(r)
    W = imageio.formats['dummy'].get_writer(Request(fname, 'w?'))
    #
    assert len(R) == 1
    assert R.get_data(0).ndim
    raises(IndexError, R.get_data, 1)
    #raises(RuntimeError, R.get_meta_data)
    assert R.get_meta_data() == {}
    R.close()
    #
    raises(RuntimeError, W.append_data, np.zeros((10, 10)))
    raises(RuntimeError, W.set_meta_data, {})
    W.close()


run_tests_if_main()
