"""Test FEI SEM image plugin functionality.

FEI TIFFs contain metadata as ASCII plaintext at the end of the file.
"""
from __future__ import unicode_literals

import os

import numpy as np

from imageio.testing import run_tests_if_main, get_test_dir, need_internet
from imageio.core import get_remote_file

import imageio


def test_fei_file_reading():
    need_internet()  # We keep a test image in the imageio-binaries repo
    fei_filename = get_remote_file('images/fei-sem-rbc.tif')
    reader = imageio.get_reader(fei_filename, format='fei')
    image = reader.get_data(0)  # imageio.Image object
    assert image.shape == (1024, 1536)
    assert np.round(np.mean(image)) == 142
    assert len(image.meta) == 18
    assert image.meta['EScan']['PixelHeight'] == '7.70833e-009'

    image_with_watermark = reader.get_data(0, discard_watermark=False)
    assert image_with_watermark.shape == (1094, 1536)
    assert np.round(np.mean(image_with_watermark)) == 137

    assert reader.get_data(0, discard_watermark=False).shape == (1094, 1536)


def test_fei_file_fail():
    normal_tif = os.path.join(get_test_dir(), 'test_tiff.tiff')
    bad_reader = imageio.get_reader(normal_tif, format='fei')
    np.testing.assert_raises(ValueError, bad_reader._get_meta_data)


run_tests_if_main()
