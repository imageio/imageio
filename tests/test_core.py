""" Test imageio core functionality.
"""

import time
import sys
import os
import shutil
import ctypes.util
import zipfile

import numpy as np
from pytest import raises
from imageio.core.testing import run_tests_if_main

import imageio
from imageio import core
from imageio.core import Format, FormatManager, get_remote_file


def test_namespace():
    """ Test that all names from the public API are in the main namespace """
    
    has_names = dir(imageio)
    has_names = set([n for n in has_names if not n.startswith('_')])
    
    need_names = ('help formats read save RETURN_BYTES '
                  'EXPECT_IM EXPECT_MIM EXPECT_VOL EXPECT_MVOL '
                  'read imread mimread volread mvolread '
                  'save imsave mimsave volsave mvolsave'
                  ).split(' ')
    need_names = set([n for n in need_names if n])
    
    # Check that all names are there
    assert need_names.issubset(has_names)
    
    # Check that there are no extra names
    extra_names = has_names.difference(need_names)
    assert extra_names == set(['core', 'plugins'])


def test_format():
    """ Test the working of the Format class """
    # Test basic format creation
    F = Format('testname', 'test description', 'foo bar spam')
    assert F.name == 'TESTNAME'
    assert F.description == 'test description'
    assert F.name in repr(F)
    assert F.name in F.doc
    assert str(F) == F.doc
    assert set(F.extensions) == set(['foo', 'bar', 'spam'])
    
    # Test setting extensions
    F1 = Format('test', '', 'foo bar spam')
    F2 = Format('test', '', 'foo, bar,spam')
    F3 = Format('test', '', ['foo', 'bar', 'spam'])
    F4 = Format('test', '', '.foo .bar .spam')
    for F in (F1, F2, F3, F4):
        assert set(F.extensions) == set(['foo', 'bar', 'spam'])
    # Fail
    raises(ValueError, Format, 'test', '', 3)  # not valid ext
    
    # Read/write
    #assert isinstance(F.read('test-request'), F.Reader)
    #assert isinstance(F.save('test-request'), F.Writer)
    
    # Test subclassing
    class MyFormat(Format):
        """ TEST DOCS """
        pass
    F = MyFormat('test', '')
    assert 'TEST DOCS' in F.doc


def test_format_manager():
    """ Test working of the format manager """
    formats = imageio.formats
    
    # Test basics of FormatManager
    assert isinstance(formats, FormatManager)
    assert len(formats) > 0
    assert 'FormatManager' in repr(formats)
    
    # Get docs
    smalldocs = str(formats)
    fulldocs = formats.create_docs_for_all_formats()
    
    # Check each format ...
    for format in formats:
        #  That each format is indeed a Format
        assert isinstance(format, Format)
        # That they are mentioned
        assert format.name in smalldocs
        assert format.name in fulldocs
    
    fname = get_remote_file('images/chelsea.png')
    fname2 = fname[:-3] + 'noext'
    shutil.copy(fname, fname2)
    
    # Check getting
    F1 = formats['PNG']
    F2 = formats['.png']
    F3 = formats[fname2]  # will look in file itself
    assert F1 is F2
    assert F1 is F3
    # Check getting
    F1 = formats['DICOM']
    F2 = formats['.dcm']
    F3 = formats['dcm']  # If omitting dot, format is smart enough to try with
    assert F1 is F2
    assert F1 is F3
    # Fail
    raises(ValueError, formats.__getitem__, 678)  # must be str
    raises(IndexError, formats.__getitem__, '.nonexistentformat')
    
    # Adding a format
    myformat = Format('test', 'test description', 'testext1 testext2')
    formats.add_format(myformat)
    assert myformat in [f for f in formats]
    assert formats['testext1'] is myformat
    assert formats['testext2'] is myformat
    # Fail
    raises(ValueError, formats.add_format, 678)  # must be Format
    raises(ValueError, formats.add_format, myformat)  # cannot add twice
    
    # Test searchinhgfor read / write format
    ReadRequest = imageio.core.request.ReadRequest
    WriteRequest = imageio.core.request.WriteRequest
    F = formats.search_read_format(ReadRequest(fname, imageio.EXPECT_IM))
    assert F is formats['PNG']
    F = formats.search_save_format(WriteRequest(fname, imageio.EXPECT_IM))
    assert F is formats['PNG']
    # Potential
    F = formats.search_read_format(ReadRequest(b'asd', imageio.EXPECT_IM,
                                               dummy_potential=True))
    assert F is formats['DUMMY']
    F = formats.search_save_format(WriteRequest('<bytes>', imageio.EXPECT_IM,
                                                dummy_potential=True))
    assert F is formats['DUMMY']


def test_fetching():
    """ Test fetching of files """
    
    # Clear image files
    test_dir = os.path.join(core.appdata_dir('imageio'), 'test')
    if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)   
    
    # This should download the file
    fname1 = get_remote_file('images/chelsea.png', test_dir)
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
    assert mtime1 == mtime2
    assert mtime1 < mtime3
    assert mtime3 < mtime4
    assert mtime4 == mtime5
    
    # Test failures
    _urlopen = core.fetching.urlopen
    _move = shutil.move
    #
    raises(RuntimeError, get_remote_file, 'this_does_not_exist', test_dir)
    #
    try:
        core.fetching.urlopen = None
        raises(RuntimeError, get_remote_file, 'images/chelsea.png', None, True)
    finally:
        core.fetching.urlopen = _urlopen
    #
    try:
        shutil.move = None
        raises(RuntimeError, get_remote_file, 'images/chelsea.png', None, True)
    finally:
        shutil.move = _move
    
    # Coverage miss
    assert '0 bytes' == core.fetching._sizeof_fmt(0)


def test_findlb():
    """ Test finding of libs """
    
    if not sys.platform.startswith('linux'):
        return
    
    # Candidate libs for common lib
    dirs, paths = core.findlib.generate_candidate_libs(['libzip'])
    assert paths
    
    # Candidate libs for common freeimage 
    fi_dir = os.path.join(core.appdata_dir('imageio'), 'freeimage')
    dirs, paths = core.findlib.generate_candidate_libs(['libfreeimage'], 
                                                       [fi_dir])
    assert fi_dir in dirs
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
    return
    
    # Check uri-type, this is not a public property, so we test the private
    R = core.Request('http://example.com')
    assert R._uri_type == core.request.URI_HTTP
    R = core.Request('ftp://example.com')
    assert R._uri_type == core.request.URI_FTP
    R = core.Request('file://example.com')
    assert R._uri_type == core.request.URI_FILENAME
    R = core.Request('<video0>')
    assert R._uri_type == core.request.URI_BYTES
    R = core.Request('<bytes>')
    assert R._uri_type == core.request.URI_BYTES
    #
    R = core.Request(get_remote_file('images/chelsea.png'))
    assert R._uri_type == core.request.URI_FILENAME
    R = core.Request(get_remote_file('/file/that/does/not/exist'))
    assert R._uri_type == core.request.URI_FILENAME  # Too short to be bytes
    R = core.Request(b'x'*600)
    assert R._uri_type == core.request.URI_BYTES
    R = core.request.ReadRequest(sys.stdin)
    assert R._uri_type == core.request.URI_FILE
    R = core.request.WriteRequest(sys.stdout)
    assert R._uri_type == core.request.URI_FILE
    #


def test_util():
    """ Test our misc utils """
    
    meta = {'foo': 3, 'bar': {'spam': 1, 'eggs': 2}}
    
    # Image list
    L = core.util.ImageList(meta)
    assert isinstance(L, list)
    assert L.meta == meta
    # Fail
    raises(ValueError, core.util.ImageList, 3)  # not a dict
    
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
    assert not isinstance(im2, core.util.Image)
    s = im.sum()
    assert not isinstance(s, core.util.Image)
    # Repr
    assert '2D image' in repr(core.util.Image(np.zeros((10, 10))))
    assert '2D image' in repr(core.util.Image(np.zeros((10, 10, 3))))
    assert '3D image' in repr(core.util.Image(np.zeros((10, 10, 10))))
    # Fail
    raises(ValueError, core.util.Image, 3)  # not a ndarray
    raises(ValueError, core.util.Image, a, 3)  # not a dict
    
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
    

def test_progres_bar(sleep=0):
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


def test_functions():
    """ Test the user-facing API functions """
    
    # Test help(), it prints stuff, so we just check whether that goes ok
    imageio.help()  # should print overview
    imageio.help('PNG')  # should print about PNG
    
    fname1 = get_remote_file('images/chelsea.png')
    fname2 = fname1[:-3] + 'jpg'
    fname3 = fname1[:-3] + 'notavalidext'
    open(fname3, 'wb')
    
    # Test read()
    R1 = imageio.read(fname1)
    R2 = imageio.read(fname1, 'png')
    assert R1.format is R2.format
    # Fail
    raises(ValueError, imageio.read, fname3)  # existing but not readable
    raises(OSError, imageio.read, 'notexisting.barf')
    raises(IndexError, imageio.read, fname1, 'notexistingformat')
    
    # Test save()
    W1 = imageio.save(fname2)
    W2 = imageio.save(fname2, 'JPG')
    assert W1.format is W2.format
    # Fail
    raises(ValueError, imageio.save, 'wtf.notexistingfile')
    
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
    fname3 = get_remote_file('images/newtonscradle.gif')
    ims = imageio.mimread(fname3)
    assert isinstance(ims, list)
    assert len(ims) > 1
    assert ims[0].ndim == 3
    assert ims[0].shape[2] in (1, 3, 4)
    
    # Test mimsave()
    fname5 = fname3[:-5] + '2.gif'
    if os.path.isfile(fname5):
        os.remove(fname5)
    assert not os.path.isfile(fname5)
    imageio.mimsave(fname5, [im[:, :, 0] for im in ims])
    imageio.mimsave(fname5, ims)
    assert os.path.isfile(fname5)
    
    # Test volread()
    fname4 = get_remote_file('images/dicom_sample.zip')
    dname4 = fname4[:-4]
    z = zipfile.ZipFile(fname4)
    z.extractall(dname4)
    #
    vol = imageio.volread(dname4, 'DICOM')
    assert vol.ndim == 3
    assert vol.shape[0] > 20
    assert vol.shape[1] == 512
    assert vol.shape[2] == 512
    
    # Test volsave()
    raises(ValueError, imageio.volsave, dname4, vol)
    raises(ValueError, imageio.volsave, dname4, np.zeros((100, 100, 100, 3)))
    # todo: we have no format to save volumes yet!
    
    # Test mvolread()
    vols = imageio.mvolread(dname4, 'DICOM')
    assert isinstance(vols, list)
    assert len(vols) == 1
    assert vols[0].shape == vol.shape
    
    # Test mvolsave()
    raises(ValueError, imageio.mvolsave, dname4, vols)
    # todo: we have no format to save volumes yet!
    
    # Fail for save functions
    raises(ValueError, imageio.imsave, fname2, np.zeros((100, 100, 5)))
    raises(ValueError, imageio.imsave, fname2, 42)
    raises(ValueError, imageio.mimsave, fname5, [np.zeros((100, 100, 5))])
    raises(ValueError, imageio.mimsave, fname5, [42])
    raises(ValueError, imageio.volsave, dname4, np.zeros((100, 100, 100, 40)))
    raises(ValueError, imageio.volsave, dname4, 42)
    raises(ValueError, imageio.mvolsave, dname4, [np.zeros((90, 90, 90, 40))])
    raises(ValueError, imageio.mvolsave, dname4, [42])

run_tests_if_main()
