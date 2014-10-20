""" Test imageio core functionality.
"""

import pytest
from imageio.testing import run_tests_if_main

import imageio
from imageio.base import Format, FormatManager


def test_format():
    
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
    

run_tests_if_main()
