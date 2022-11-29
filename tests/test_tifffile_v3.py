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
    # TODO: fixme
    filename = tmp_path / "test.tiff"

    # Write metadata
    dt = datetime.datetime(2018, 8, 6, 15, 35, 5)
    with iio.get_writer(filename, software="testsoftware") as w:
        w.append_data(
            np.zeros((10, 10)), meta={"description": "test desc", "datetime": dt}
        )
        w.append_data(np.zeros((10, 10)), meta={"description": "another desc"})
    with iio.get_reader(filename) as r:
        for md in r.get_meta_data(), r.get_meta_data(0):
            assert "datetime" in md
            assert md["datetime"] == dt
            assert "software" in md
            assert md["software"] == "testsoftware"
            assert "description" in md
            assert md["description"] == "test desc"

        md = r.get_meta_data(1)
        assert "description" in md
        assert md["description"] == "another desc"


def test_imagej_hyperstack(tmp_path):
    # create artifical hyperstack

    tifffile.imwrite(
        tmp_path / "hyperstack.tiff",
        np.zeros((15, 2, 180, 183), dtype=np.uint8),
        imagej=True,
    )

    # test ImageIO plugin
    img = iio.volread(tmp_path / "hyperstack.tiff", format="TIFF")
    assert img.shape == (15, 2, 180, 183)


@pytest.mark.parametrize(
    "dpi,expected_resolution",
    [
        ((0, 1), (0, 1, "INCH")),
        ((0, 12), (0, 12, "INCH")),
        ((100, 200), (100, 200, "INCH")),
        ((0.5, 0.5), (0.5, 0.5, "INCH")),
        (((1, 3), (1, 3)), (1 / 3, 1 / 3, "INCH")),
    ],
)
def test_resolution_metadata(tmp_path, dpi, expected_resolution):
    data = np.zeros((200, 100), dtype=np.uint8)

    writer = iio.get_writer(tmp_path / "test.tif")
    writer.append_data(data, dict(resolution=dpi))
    writer.close()

    read_image = iio.imread(tmp_path / "test.tif")

    assert read_image.meta["resolution"] == expected_resolution
    assert read_image.meta["resolution_unit"] == 2


@pytest.mark.parametrize("resolution", [(1, 0), (0, 0)])
def test_invalid_resolution_metadata(tmp_path, resolution):
    data = np.zeros((200, 100), dtype=np.uint8)

    tif_path = tmp_path / "test.tif"

    writer = iio.get_writer(tif_path)
    writer.append_data(data)
    writer.close()
    # Overwrite low level metadata the exact way we want it
    # to avoid any re-interpretation of the metadata by imageio
    # For example, it seems that (0, 0) gets rewritten as (0, 1)
    with tifffile.TiffFile(tif_path, mode="r+b") as tif:
        tags = tif.pages[0].tags
        tags["XResolution"].overwrite(resolution)
        tags["YResolution"].overwrite(resolution)

    # Validate with low level library that the invalid metadata is written
    with tifffile.TiffFile(tif_path, mode="rb") as tif:
        tags = tif.pages[0].tags
        assert tags["XResolution"].value == resolution
        assert tags["YResolution"].value == resolution

    with pytest.warns(RuntimeWarning):
        read_image = iio.imread(tmp_path / "test.tif")

    assert "resolution" not in read_image.meta


def test_read_bytes():
    # regression test for: https://github.com/imageio/imageio/issues/703

    some_bytes = iio.imwrite("<bytes>", [[0]], format="tiff")
    assert some_bytes is not None


def test_write_file(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/810
    img = np.zeros((32, 32), dtype=np.uint16)
    iio.imwrite(tmp_path / "v.tif", img)


def test_stk_volume(test_images):
    # this is a regression test for
    # https://github.com/imageio/imageio/issues/802

    expected = iio.volread(test_images / "movie.stk")
    actual = iio.imread(test_images / "movie.stk")

    np.allclose(actual, expected)


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

    # this creates a TIFF with two flat images (non-volumetric)
    # Note: our plugin currently can't do this, but tifffile itself can
    expected_flat = np.full((35, 73, 3), 114, dtype=np.uint8)
    with tifffile.TiffWriter(tmp_path / "flat.tiff") as file:
        file.write(expected_flat)
        file.write(expected_flat)

    actual_flat = iio.imread(tmp_path / "flat.tiff")
    assert np.allclose(actual_flat, expected_flat)

    for idx, page in enumerate(iio.imiter(tmp_path / "flat.tiff")):
        assert np.allclose(page, expected_flat)
    assert idx == 1


def test_multiple_ndimages(tmp_path):
    volumetric = np.full((4, 255, 255, 3), 114, dtype=np.uint8)
    flat = np.full((255, 255, 3), 114, dtype=np.uint8)
    different_shape = np.full((120, 73, 3), 114, dtype=np.uint8)
    with tifffile.TiffWriter(tmp_path / "nightmare.tiff") as file:
        file.write(volumetric)
        file.write(flat)
        file.write(different_shape)

    # imread will read the image at the respective index
    assert iio.imread(tmp_path / "nightmare.tiff", index=0).shape == (4, 255, 255, 3)
    assert iio.imread(tmp_path / "nightmare.tiff", index=1).shape == (255, 255, 3)
    assert iio.imread(tmp_path / "nightmare.tiff", index=2).shape == (120, 73, 3)

    # imiter will yield the three images in order
    shapes = [(4, 255, 255, 3), (255, 255, 3), (120, 73, 3)]
    for image, shape in zip(iio.imiter(tmp_path / "nightmare.tiff"), shapes):
        assert image.shape == shape


def test_compression(tmp_path):
    img = np.ones((128, 128))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        iio.imwrite(tmp_path / "test.tiff", img, metadata={"compress": 5})

    with tifffile.TiffFile(tmp_path / "test.tiff") as file:
        # this should be tifffile.COMPRESSION.ADOBE_DEFLATE
        # but that isn't supported by tifffile on python 3.7
        assert file.pages[0].compression == 8
        print("")

    iio.imwrite(tmp_path / "test.tiff", img, metadata={"compression": "zlib"})
    with tifffile.TiffFile(tmp_path / "test.tiff") as file:
        # this should be tifffile.COMPRESSION.ADOBE_DEFLATE
        # but that isn't supported by tifffile on python 3.7
        assert file.pages[0].compression == 8
        print("")

    iio.imwrite(
        tmp_path / "test.tiff",
        img,
    )
    with tifffile.TiffFile(tmp_path / "test.tiff") as file:
        # this should be tifffile.COMPRESSION.NONE
        # but that isn't supported by tifffile on python 3.7
        assert file.pages[0].compression == 1
