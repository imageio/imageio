""" Test imageio avbin functionality.
"""


import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio
from imageio import core
from imageio.core import get_remote_file


test_dir = get_test_dir()


_prepared = None


def test_read():
    reader = imageio.read(get_remote_file('images/cockatoo.mp4'))
    assert reader.get_length() == np.inf
    reader.get_meta_data()
    reader.format.can_save(core.Request('test.mp4', 'wI'))
    
    for i in range(10):
        mean = reader.get_next_data().mean()
        assert mean > 100 and mean < 115
    
    with raises(IndexError):    
        reader.get_data(0)


def test_read_format():
    reader = imageio.read(get_remote_file('images/cockatoo.mp4'), 
                          videoformat='mp4')
    for i in range(10):
        mean = reader.get_next_data().mean()
        assert mean > 100 and mean < 115
 
 
def test_stream():
    with raises(IOError):
        imageio.read(get_remote_file('images/cockatoo.mp4'), stream=5)
  
  
def test_invalidfile():
    filename = test_dir+'/empty.mp4'
    with open(filename, 'w'):
        pass
    
    with raises(IOError):
        imageio.read(filename)
    
   
def show():
    reader = imageio.read(get_remote_file('images/cockatoo.mp4'))
    for i in range(10):
        reader.get_next_data()
       
    import pylab
    pylab.ion()
    pylab.show(reader.get_next_data())


run_tests_if_main(1)
