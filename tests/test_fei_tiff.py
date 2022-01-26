"""Test FEI SEM image plugin functionality.

FEI TIFFs contain metadata as ASCII plaintext at the end of the file.
"""
from __future__ import unicode_literals

import pytest
import numpy as np

import imageio


def test_fei_file_reading(test_images):
    fei_filename = test_images / "fei-sem-rbc.tif"
    reader = imageio.get_reader(fei_filename, format="fei")
    image = reader.get_data(0)  # imageio.Image object
    assert image.shape == (1024, 1536)
    assert np.round(np.mean(image)) == 142
    assert len(image.meta) == 18
    assert image.meta["EScan"]["PixelHeight"] == 7.70833e-009
    assert isinstance(image.meta["Image"]["ResolutionX"], int)

    image_with_watermark = reader.get_data(0, discard_watermark=False)
    assert image_with_watermark.shape == (1094, 1536)
    assert np.round(np.mean(image_with_watermark)) == 137

    assert reader.get_data(0, discard_watermark=False).shape == (1094, 1536)


def test_fei_file_fail(tmp_path):
    normal_tif = tmp_path / "test_tiff.tiff"
    imageio.imsave(normal_tif, np.zeros((5, 5), dtype=np.uint8))
    bad_reader = imageio.get_reader(normal_tif, format="fei")
    with pytest.raises(ValueError):
        bad_reader._get_meta_data()
