""" Test tifffile plugin functionality.
"""

import datetime
import numpy as np
import pytest
import io
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

    # read all series as batch
    actual = iio.imread(filename, index=...)
    assert actual.shape == (3, 10, 10, 3)

    # read each series individually
    for idx in range(3):
        actual = iio.imread(filename, index=idx)
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
        if tuple(int(x) for x in tifffile.__version__.split(".")) <= (2021, 11, 2):
            assert tif.series[0].pages[0].tags[284].value == 2
        else:
            assert tif.series[0].dims == ("sample", "height", "width")


def test_metadata_reading(test_images):
    filename = test_images / "multipage_rgb.tif"

    file_metadata = iio.immeta(filename)
    assert file_metadata["is_imagej"] is False
    assert file_metadata["is_shaped"] is True

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

    metadata = iio.immeta(filename)
    assert metadata["is_imagej"] is True


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
    assert iio.imread(filename, index=0).shape == (4, 255, 255, 3)
    assert iio.imread(filename, index=1).shape == (255, 255, 3)
    assert iio.imread(filename, index=2).shape == (120, 73, 3)

    # imread will read the respective plane when using index kwarg
    assert iio.imread(filename, index=..., page=0).shape == (255, 255, 3)
    assert iio.imread(filename, index=..., page=1).shape == (255, 255, 3)
    assert iio.imread(filename, index=..., page=2).shape == (255, 255, 3)
    assert iio.imread(filename, index=..., page=3).shape == (255, 255, 3)
    assert iio.imread(filename, index=..., page=4).shape == (255, 255, 3)
    assert iio.imread(filename, index=..., page=5).shape == (120, 73, 3)

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


def test_properties(tmp_path):
    filename = tmp_path / "test.tiff"
    data = np.full((255, 255, 3), 42, dtype=np.uint8)
    iio.imwrite(filename, data)

    props = iio.improps(filename)
    assert props.shape == (255, 255, 3)
    assert props.n_images is None

    props = iio.improps(filename, index=...)
    assert props.shape == (1, 255, 255, 3)
    assert props.n_images == 1

    data = np.full((6, 255, 255, 3), 42, dtype=np.uint8)
    iio.imwrite(filename, data)

    props = iio.improps(filename, page=3)
    assert props.shape == (255, 255, 3)
    assert props.n_images is None

    props = iio.improps(filename, index=...)
    assert props.shape == (1, 255, 255, 3)
    assert props.n_images == 1

    props = iio.improps(filename, index=..., page=...)
    assert props.shape == (6, 255, 255, 3)
    assert props.n_images == 6


def test_contigous_writing(tmp_path):
    filename = tmp_path / "test.tiff"
    data = np.full((128, 128, 3), 42, np.uint8)

    with tifffile.TiffWriter(filename) as tw:
        tw.write(data, contiguous=True)
        tw.write(data, contiguous=True)
        tw.write(data, contiguous=True)
        tw.write(data, contiguous=True)

    metadata = iio.immeta(filename)
    assert metadata["is_shaped"] is True
    assert metadata["shape"] == [4, 128, 128, 3]


def test_unreadable_file():
    garbage = b"awdadbj30993urfj"

    with pytest.raises(OSError):
        iio.imread(garbage)


def test_touch_invalid_kwargs(tmp_path):
    filename = tmp_path / "test.tiff"
    data = np.full((5, 128, 128, 3), 42, np.uint8)
    iio.imwrite(filename, data)

    with pytest.raises(ValueError):
        iio.imread(filename, key=0, page=0)

    with pytest.raises(ValueError):
        iio.imread(filename, series=0, index=0)


def test_tiffile_native_arguments(tmp_path):
    filename = tmp_path / "test.tiff"
    data = np.full((5, 128, 128, 3), 42, np.uint8)
    data[0, 2, 3, :] = 7
    iio.imwrite(filename, data)

    page = iio.imread(filename, key=0)
    np.testing.assert_allclose(page, data[0])

    img = iio.imread(filename, series=0)
    np.testing.assert_allclose(img, data)


def test_various_metadata_reading(tmp_path):
    filename = tmp_path / "nightmare.tiff"
    flat = np.full((255, 255, 3), 114, dtype=np.uint8)
    volumetric = np.full((4, 255, 255, 3), 114, dtype=np.uint8)
    different_shape = np.full((120, 73, 3), 114, dtype=np.uint8)
    with iio.imopen(filename, "w") as file:
        file.write(flat)
        file.write(volumetric, compression="zlib")
        file.write(different_shape)

    metadata = iio.immeta(filename, index=1, page=2)
    assert metadata["compression"] == 8  # (ADOBE_DEFLATE)

    metadata = iio.immeta(filename, index=..., page=2)
    assert metadata["compression"] == 8  # (ADOBE_DEFLATE)


def test_iter_pages(tmp_path):
    filename = tmp_path / "nightmare.tiff"
    flat = np.full((255, 255, 3), 114, dtype=np.uint8)
    volumetric = np.full((4, 255, 255, 3), 114, dtype=np.uint8)
    different_shape = np.full((120, 73, 3), 114, dtype=np.uint8)
    with iio.imopen(filename, "w") as file:
        file.write(flat)
        file.write(volumetric, compression="zlib")
        file.write(different_shape)

    with iio.imopen(filename, "r") as file:
        for idx, page in enumerate(file.iter_pages(index=1)):
            np.testing.assert_allclose(page, volumetric[idx])
