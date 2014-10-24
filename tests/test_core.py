""" Test imageio core functionality.
"""

import pytest
from imageio.core.testing import run_tests_if_main

import imageio
from imageio.core import Format, FormatManager


def test_format():
    """ Test the working of the Format class """
    # Test basic format creation
    F = Format('testname', 'test description', 'foo bar spam')
    assert F.name == 'TESTNAME'
    assert F.description == 'test description'
    assert F.name in repr(F)
    assert F.name in F.doc
    assert set(F.extensions) == set(['foo', 'bar', 'spam'])
    
    # Test setting extensions
    F1 = Format('test', '', 'foo bar spam')
    F2 = Format('test', '', 'foo, bar,spam')
    F3 = Format('test', '', ['foo', 'bar', 'spam'])
    F4 = Format('test', '', '.foo .bar .spam')
    for F in (F1, F2, F3, F4):
        assert set(F.extensions) == set(['foo', 'bar', 'spam'])
    
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
        
    # Check getting
    F1 = formats['DICOM']
    F2 = formats['.dcm']
    assert F1 is F2
    # Fail
    pytest.raises(IndexError, formats.__getitem__, '.nonexistentformat')


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


run_tests_if_main()
