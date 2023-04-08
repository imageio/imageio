import warnings

import imageio.v3 as iio
import numpy as np
import pytest

pytest.importorskip("imageio.plugins.opencv")
import cv2  # noqa: E402


def test_basic_reading(test_images, tmp_path):
    img_expected = iio.imread(test_images / "chelsea.png")
    img = iio.imread(test_images / "chelsea.png", plugin="opencv")
    assert img.shape == (300, 451, 3)
    assert np.allclose(img, img_expected)

    img = iio.imread(
        test_images / "chelsea.png", plugin="opencv", colorspace=cv2.COLOR_BGR2RGBA
    )
    img2 = iio.imread(test_images / "chelsea.png", plugin="opencv", colorspace="RGBA")
    assert img.shape == (300, 451, 4)
    assert np.allclose(img, img2)

    img_expected = iio.imread(test_images / "camera.png")
    img = iio.imread(
        test_images / "camera.png", plugin="opencv", flags=cv2.IMREAD_ANYCOLOR
    )
    assert img.shape == (512, 512)
    assert np.allclose(img, img_expected)

    img_expected = iio.imread(test_images / "astronaut.png", mode="RGBA")
    iio.imwrite(tmp_path / "test.png", img_expected)
    img = iio.imread(tmp_path / "test.png", plugin="opencv", flags=cv2.IMREAD_UNCHANGED)
    assert img.shape == (512, 512, 4)
    assert np.allclose(img, img_expected)

    with pytest.raises(IOError):
        iio.imread("nonexistant.png", plugin="opencv")


def test_bytes_reading(test_images):
    img_expected = iio.imread(test_images / "chelsea.png")
    encoded_image = (test_images / "chelsea.png").read_bytes()

    img = iio.imread(encoded_image, plugin="opencv")

    assert img.shape == (300, 451, 3)
    np.allclose(img, img_expected)


def test_multi_reading(test_images, tmp_path):
    img_expected = iio.imread(test_images / "newtonscradle.gif")
    iio.imwrite(tmp_path / "test.tiff", img_expected)

    img = iio.imread(tmp_path / "test.tiff", plugin="opencv")

    assert img.shape == (36, 150, 200, 3)
    np.allclose(img, img_expected)

    img = iio.imread(tmp_path / "test.tiff", index=3, plugin="opencv")

    assert img.shape == (150, 200, 3)
    np.allclose(img, img_expected[3])

    with pytest.raises(ValueError):
        iio.imread(tmp_path / "test.tiff", index=200, plugin="opencv")


def test_iter(test_images, tmp_path):
    img_expected = iio.imread(test_images / "newtonscradle.gif")
    iio.imwrite(tmp_path / "test.tiff", img_expected)

    for idx, img in enumerate(iio.imiter(tmp_path / "test.tiff", plugin="opencv")):
        assert img.shape == (150, 200, 3)
        np.allclose(img, img_expected[idx])


def test_writing(test_images, tmp_path):
    img_expected = iio.imread(test_images / "chelsea.png")
    iio.imwrite(tmp_path / "test.png", img_expected, plugin="opencv")
    result = iio.imread(tmp_path / "test.png")
    np.allclose(result, img_expected)

    img_expected = iio.imread(test_images / "chelsea.png", mode="RGBA")
    iio.imwrite(tmp_path / "test.png", img_expected, plugin="opencv")
    result = iio.imread(tmp_path / "test.png")
    np.allclose(result, img_expected)

    img_expected = iio.imread(test_images / "camera.png")
    iio.imwrite(tmp_path / "test.png", img_expected, plugin="opencv")
    result = iio.imread(tmp_path / "test.png")
    np.allclose(result, img_expected)

    img_expected = iio.imread(test_images / "camera.png")
    with pytest.raises(IOError):
        iio.imwrite("no_extension", img_expected, plugin="opencv")


def test_write_bytes(test_images):
    img_expected = iio.imread(test_images / "chelsea.png")

    img_encoded = iio.imwrite(
        "<bytes>", img_expected, plugin="opencv", extension=".png"
    )
    result = iio.imread(img_encoded)

    np.allclose(result, img_expected)


def test_write_batch(test_images, tmp_path):
    img_expected = iio.imread(test_images / "newtonscradle.gif")

    iio.imwrite(tmp_path / "test.tiff", img_expected, plugin="opencv", is_batch=True)
    img = iio.imread(tmp_path / "test.tiff", plugin="opencv")
    np.allclose(img, img_expected)

    img_list = [x for x in img_expected]
    iio.imwrite(tmp_path / "test.tiff", img_list, plugin="opencv", is_batch=True)
    img = iio.imread(tmp_path / "test.tiff", plugin="opencv")
    np.allclose(img, img_expected)


def test_props(test_images, tmp_path):
    props = iio.improps(test_images / "astronaut.png", plugin="opencv")
    assert props.shape == (512, 512, 3)
    assert props.dtype == np.uint8
    assert props.n_images is None
    assert props.is_batch is False

    img_expected = iio.imread(test_images / "newtonscradle.gif")
    iio.imwrite(tmp_path / "test.tiff", img_expected)

    props = iio.improps(tmp_path / "test.tiff", plugin="opencv", index=...)
    assert props.shape == (36, 150, 200, 3)
    assert props.dtype == np.uint8
    assert props.n_images == 36
    assert props.is_batch is True

    props = iio.improps(tmp_path / "test.tiff", plugin="opencv", index=0)
    assert props.shape == (150, 200, 3)
    assert props.dtype == np.uint8
    assert props.n_images is None
    assert props.is_batch is False


def test_metadata(test_images):
    with warnings.catch_warnings(record=True):
        metadata = iio.immeta(test_images / "astronaut.png", plugin="opencv")

    assert metadata == dict()
