import pytest
import imageio.v2 as iio
import numpy as np


def test_reader(test_images):
    with iio.get_reader(test_images / "chelsea.png") as file:
        assert file.request.extension == ".png"

        img = file.get_data(0)
        assert img.shape == (300, 451, 3)

        # read using alternative method
        file.set_image_index(0)
        img2 = file.get_next_data()

        assert np.allclose(img2, img)


def test_get_reader_format(test_images):
    with iio.get_reader(test_images / "chelsea.png") as file:
        with pytest.raises(ValueError):
            file.format  # v3 Pillow Plugin


def test_get_length(test_images):
    with iio.get_reader(test_images / "chelsea.png") as file:
        v3_count = file.instance.properties(index=...).shape[0]
        assert len(file) == v3_count


def test_iterating(test_images):
    with iio.get_reader(test_images / "newtonscradle.gif") as file:
        for count, img in enumerate(file):
            assert img.shape == (150, 200, 3)

        assert count == len(file) - 1


def test_writer(test_images, tmp_path):
    img = iio.imread(test_images / "chelsea.png")

    with iio.get_writer(tmp_path / "test.png") as file:
        assert file.request.extension == ".png"
        file.append_data(img)


def test_get_writer_format(tmp_path):
    with iio.get_writer(tmp_path / "test.png") as file:
        with pytest.raises(ValueError):
            file.format  # v3 Pillow Plugin


def test_warnings(tmp_path, test_images):
    img = iio.imread(test_images / "chelsea.png")

    with iio.get_writer(tmp_path / "test.png") as writer:
        with pytest.warns(UserWarning):
            writer.append_data(img, meta={"meta_key": "meta_value"})
