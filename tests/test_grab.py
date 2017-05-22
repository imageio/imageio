import sys

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main

import imageio


def test_grab_plugin_load():
    
    reader = imageio.get_reader('<screen>')
    assert reader.format.name == 'SCREENGRAB'
    
    reader = imageio.get_reader('<clipboard>')
    assert reader.format.name == 'CLIPBOARDGRAB'

    with raises(ValueError):
        imageio.get_writer('<clipboard>')
    with raises(ValueError):
        imageio.get_writer('<screen>')
    

def test_grab_simulated():
    # Hard to test for real, if only because its only fully suppored on
    # Windows, but we can monkey patch so we can test all the imageio bits.
    from PIL import ImageGrab
    
    _grab = getattr(ImageGrab, 'grab', None)
    _grabclipboard = getattr(ImageGrab, '_grabclipboard', None)
    _plat = sys.platform
    
    ImageGrab.grab = lambda: np.zeros((8, 8, 3), np.uint8)
    ImageGrab.grabclipboard = lambda: np.zeros((9, 9, 3), np.uint8)
    sys.platform = 'win32'
    
    try:
        
        im = imageio.imread('<screen>')
        assert im.shape == (8, 8, 3)
        
        reader = imageio.get_reader('<screen>')
        im1 = reader.get_data(0)
        im2 = reader.get_data(0)
        im3 = reader.get_data(1)
        assert im1.shape == (8, 8, 3)
        assert im2.shape == (8, 8, 3)
        assert im3.shape == (8, 8, 3)
        
        im = imageio.imread('<clipboard>')
        assert im.shape == (9, 9, 3)
        
        reader = imageio.get_reader('<clipboard>')
        im1 = reader.get_data(0)
        im2 = reader.get_data(0)
        im3 = reader.get_data(1)
        assert im1.shape == (9, 9, 3)
        assert im2.shape == (9, 9, 3)
        assert im3.shape == (9, 9, 3)
        
        # Grabbing from clipboard can fail if there is no image data to grab
        ImageGrab.grabclipboard = lambda: None
        with raises(RuntimeError):
            im = imageio.imread('<clipboard>')
    
    finally:
        ImageGrab.grab = _grab
        ImageGrab.grabclipboard = _grabclipboard
        sys.platform = _plat

run_tests_if_main()
