""" Test tifffile plugin functionality.
"""

import datetime
import numpy as np
import pytest
import io
import warnings
from copy import deepcopy

import imageio.v3 as iio
from imageio.config import known_plugins, known_extensions

tifffile = pytest.importorskip("tifffile", reason="TiffFile is not installed")


@pytest.fixture(scope="module", autouse=True)
def use_tifffile_v3():
    plugin_name = "tifffile"
    all_plugins = known_plugins.copy()
    all_extensions = known_extensions.copy()

    known_plugins.clear()
    known_extensions.clear()

    known_plugins[plugin_name] = all_plugins[plugin_name]

    for extension, configs in all_extensions.items():
        for config in configs:
            for plugin in config.priority:
                if plugin == plugin_name:
                    copied_config = deepcopy(config)
                    copied_config.priority = [plugin_name]
                    copied_config.default_priority = [plugin_name]
                    known_extensions[extension] = [copied_config]

    yield

    known_plugins.update(all_plugins)
    known_extensions.update(all_extensions)


def test_basic_roundtrip(tmp_path):
    filename = tmp_path / "test.tiff"
    expected = np.ones((10, 10, 3), np.uint8) * 2

    iio.imwrite(filename, expected)
    actual = iio.imread(filename)

    np.testing.assert_allclose(actual, expected)


def test_multiple_images_roundtrip(tmp_path):
    filename = tmp_path / "test.tiff"
    expected = np.ones((10, 10, 3), np.uint8) * 2

    iio.imwrite(filename, [expected] * 3, is_batch=True)

    for idx in range(3):
        actual = iio.imread(filename, series=idx)
        np.testing.assert_allclose(actual, expected)


def test_volume_roundtrip(tmp_path):
    filename = tmp_path / "test.tiff"
    expected = np.ones((3, 10, 10, 3), np.uint8) * 2

    iio.imwrite(filename, expected)
    actual = iio.imread(filename)

    np.testing.assert_allclose(actual, expected)


def test_channel_first_volume(test_images, tmp_path):
    # remote channel-first volume rgb (2, 3, 10, 10)
    filename = test_images / "multipage_rgb.tif"
    img = iio.imread(filename)

    assert img.shape == (2, 3, 10, 10)


def test_planarconfig(tmp_path):
    filename = tmp_path / "test.tiff"
    expected = np.ones((3, 10, 10), np.uint8) * 2

    iio.imwrite(filename, expected, planarconfig="SEPARATE")

    # assert planar config
    with tifffile.TiffFile(filename) as tif:
        assert tif.series[0].dims == ("sample", "height", "width")


def test_metadata_reading(test_images):
    filename = test_images / "multipage_rgb.tif"

    file_metadata = iio.immeta(filename)
    assert file_metadata["is_imagej"] == False
    assert file_metadata["is_shaped"] == True

    page_metadata = iio.immeta(filename, index=0)
    assert page_metadata["description"] == "shape=(2,3,10,10)"
    assert page_metadata["description1"] == ""
    assert page_metadata["datetime"] == datetime.datetime(2015, 5, 9, 9, 8, 29)
    assert page_metadata["software"] == "tifffile.py"


def test_metadata_writing(tmp_path):
    filename = tmp_path / "test.tiff"
    dt = datetime.datetime(2018, 8, 6, 15, 35, 5)

    with iio.imopen(filename, "w") as file:
        file.write(
            np.zeros((10, 10)),
            software="testsoftware",
            description="test desc",
            datetime=dt,
        )
        file.write(np.zeros((10, 10)), description="another desc")

    page1_md = iio.immeta(filename, index=0)
    assert page1_md["datetime"] == dt
    assert page1_md["software"] == "testsoftware"
    assert page1_md["description"] == "test desc"

    page2_md = iio.immeta(filename, index=1)
    assert page2_md["description"] == "another desc"


def test_imagej_hyperstack(tmp_path):
    filename = tmp_path / "hyperstack.tiff"

    with iio.imopen(filename, "w", imagej=True) as file:
        file.write(np.zeros((15, 2, 180, 183), dtype=np.uint8))

    # test ImageIO plugin
    img = iio.imread(filename)
    assert img.shape == (15, 2, 180, 183)


@pytest.mark.parametrize(
    "dpi,expected_resolution",
    [
        ((0, 1), (0, 1)),
        ((0, 12), (0, 12)),
        ((100, 200), (100, 200)),
        ((0.5, 0.5), (0.5, 0.5)),
        (((1, 3), (1, 3)), (1 / 3, 1 / 3)),
    ],
)
def test_resolution_metadata(tmp_path, dpi, expected_resolution):
    filename = tmp_path / "test.tif"
    data = np.zeros((200, 100), dtype=np.uint8)

    iio.imwrite(filename, data, resolution=dpi)
    page_metadata = iio.immeta(filename, index=0)

    assert page_metadata["resolution"] == expected_resolution
    assert page_metadata["resolution_unit"] == 2


@pytest.mark.parametrize("resolution", [(1, 0), (0, 0)])
def test_invalid_resolution_metadata(tmp_path, resolution):
    tif_path = tmp_path / "test.tif"
    data = np.zeros((200, 100), dtype=np.uint8)
    iio.imwrite(tif_path, data)

    with tifffile.TiffFile(tif_path, mode="r+b") as tif:
        tags = tif.pages[0].tags
        tags["XResolution"].overwrite(resolution)
        tags["YResolution"].overwrite(resolution)

    read_image = iio.immeta(tmp_path / "test.tif", index=0)
    assert read_image["XResolution"] == resolution
    assert read_image["YResolution"] == resolution


def test_read_bytes():
    # regression test for: https://github.com/imageio/imageio/issues/703

    some_bytes = iio.imwrite("<bytes>", [[0]])
    assert some_bytes is not None


def test_tiff_page_writing():
    # regression test for
    # https://github.com/imageio/imageio/issues/849
    base_image = np.full((256, 256, 3), 42, dtype=np.uint8)

    buffer = io.BytesIO()
    iio.imwrite(buffer, base_image, extension=".tiff")
    buffer.seek(0)

    with tifffile.TiffFile(buffer) as file:
        assert len(file.pages) == 1


def test_bool_writing():
    # regression test for
    # https://github.com/imageio/imageio/issues/852

    expected = (np.arange(255 * 123) % 2 == 0).reshape((255, 123))

    img_bytes = iio.imwrite("<bytes>", expected, extension=".tiff")
    actual = iio.imread(img_bytes)

    assert np.allclose(actual, expected)


def test_roundtrip(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/854

    iio.imwrite(tmp_path / "test.tiff", np.ones((10, 64, 64), "u4"))
    actual = iio.imread(tmp_path / "test.tiff")

    assert actual.shape == (10, 64, 64)


def test_volume_roudtrip(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/818

    expected_volume = np.full((23, 123, 456, 3), 42, dtype=np.uint8)
    iio.imwrite(tmp_path / "volume.tiff", expected_volume)

    # assert that the file indeed contains a volume
    with tifffile.TiffFile(tmp_path / "volume.tiff") as file:
        assert file.series[0].shape == (23, 123, 456, 3)
        assert len(file.series) == 1

    actual_volume = iio.imread(tmp_path / "volume.tiff")
    assert np.allclose(actual_volume, expected_volume)


def test_multipage_read(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/818

    filename = tmp_path / "flat.tiff"

    # this creates a TIFF with two flat images (non-volumetric)
    expected_flat = np.full((35, 73, 3), 114, dtype=np.uint8)
    iio.imwrite(filename, [expected_flat, expected_flat], is_batch=True)

    actual_flat = iio.imread(filename)
    assert np.allclose(actual_flat, expected_flat)

    for idx, series in enumerate(iio.imiter(filename)):
        assert np.allclose(series, expected_flat)
    assert idx == 1


def test_multiple_ndimages(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/81

    filename = tmp_path / "nightmare.tiff"
    volumetric = np.full((4, 255, 255, 3), 114, dtype=np.uint8)
    flat = np.full((255, 255, 3), 114, dtype=np.uint8)
    different_shape = np.full((120, 73, 3), 114, dtype=np.uint8)
    with iio.imopen(filename, "w") as file:
        file.write(volumetric)
        file.write(flat)
        file.write(different_shape)

    # imread will read the respective series when using series kwarg
    assert iio.imread(filename, series=0).shape == (4, 255, 255, 3)
    assert iio.imread(filename, series=1).shape == (255, 255, 3)
    assert iio.imread(filename, series=2).shape == (120, 73, 3)

    # imread will read the respective plane when using index kwarg
    assert iio.imread(filename, index=0).shape == (255, 255, 3)
    assert iio.imread(filename, index=1).shape == (255, 255, 3)
    assert iio.imread(filename, index=2).shape == (255, 255, 3)
    assert iio.imread(filename, index=3).shape == (255, 255, 3)
    assert iio.imread(filename, index=4).shape == (255, 255, 3)
    assert iio.imread(filename, index=5).shape == (120, 73, 3)

    # imiter will yield the three images in order
    shapes = [(4, 255, 255, 3), (255, 255, 3), (120, 73, 3)]
    for image, shape in zip(iio.imiter(filename), shapes):
        assert image.shape == shape

    # iter pages will yield pages in order
    shapes = [
        (255, 255, 3),
        (255, 255, 3),
        (255, 255, 3),
        (255, 255, 3),
        (255, 255, 3),
        (120, 73, 3),
    ]
    with iio.imopen(filename, "r") as file:
        for image, shape in zip(file.iter_pages(), shapes):
            assert image.shape == shape


def test_compression(tmp_path):
    img = np.ones((128, 128))

    iio.imwrite(tmp_path / "test.tiff", img, compression="zlib")
    page_meta = iio.immeta(tmp_path / "test.tiff", index=0)
    assert page_meta["compression"] == 8

    iio.imwrite(tmp_path / "test2.tiff", img)
    page_meta = iio.immeta(tmp_path / "test2.tiff", index=0)
    assert page_meta["compression"] == 1
