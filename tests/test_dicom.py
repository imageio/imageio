""" Test imageio core functionality.
"""

from zipfile import ZipFile

import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir

import imageio
from imageio.core import get_remote_file


test_dir = get_test_dir()


def test_dicom():
    
    # Test volread()
    fname1 = get_remote_file('images/dicom_sample.zip', test_dir)
    dname1 = fname1[:-4]
    z = ZipFile(fname1)
    z.extractall(dname1)
    #
    vol = imageio.volread(dname1, 'DICOM')
    assert vol.ndim == 3
    assert vol.shape[0] > 20
    assert vol.shape[1] == 512
    assert vol.shape[2] == 512
    
    # Test volsave()
    raises(ValueError, imageio.volsave, dname1, vol)
    raises(ValueError, imageio.volsave, dname1, np.zeros((100, 100, 100, 3)))
    # todo: we have no format to save volumes yet!
    
    # Test mvolread()
    vols = imageio.mvolread(dname1, 'DICOM')
    assert isinstance(vols, list)
    assert len(vols) == 1
    assert vols[0].shape == vol.shape


run_tests_if_main()
