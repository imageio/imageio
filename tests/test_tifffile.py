""" Test tifffile plugin functionality.
"""

import datetime
import io
import warnings
from copy import deepcopy

import numpy as np
import pytest
from conftest import deprecated_test

import imageio.v2 as iio
import imageio.v3 as iio3
from imageio.config import known_extensions, known_plugins

tifffile = pytest.importorskip("tifffile", reason="tifffile is not installed")


@pytest.fixture(scope="module", autouse=True)
def use_tifffile_v3():
    plugin_name = "TIFF"
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


@deprecated_test
def test_tifffile_format():
    # Test selection
    for name in ["tiff", ".tif"]:
        format = iio.formats[name]
        assert format.name == "TIFF"


def test_tifffile_reading_writing(test_images, tmp_path):
    """Test reading and saving tiff"""

    im2 = np.ones((10, 10, 3), np.uint8) * 2

    filename1 = tmp_path / "test_tiff.tiff"

    # One image
    iio.imsave(filename1, im2)
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()
    assert len(ims) == 1

    # Multiple images
    iio.mimsave(filename1, [im2, im2, im2])
    im = iio.imread(filename1)
    ims = iio.mimread(filename1)
    assert im.shape == im2.shape
    assert (im == im2).all()  # note: this does not imply that the shape match!
    assert len(ims) == 3
    for i in range(3):
        assert ims[i].shape == im2.shape
        assert (ims[i] == im2).all()

    # volumetric data
    iio.volwrite(filename1, np.tile(im2, (3, 1, 1, 1)))
    vol = iio.volread(filename1)
    vols = iio.mvolread(filename1)
    assert vol.shape == (3,) + im2.shape
    assert len(vols) == 1 and vol.shape == vols[0].shape
    for i in range(3):
        assert (vol[i] == im2).all()

    # remote channel-first volume rgb (2, 3, 10, 10)
    filename2 = test_images / "multipage_rgb.tif"
    img = iio.mimread(filename2)
    assert len(img) == 2
    assert img[0].shape == (3, 10, 10)

    # Mixed
    W = iio.save(filename1)
    W.set_meta_data({"planarconfig": "SEPARATE"})  # was "planar"
    assert W.format.name == "TIFF"
    W.append_data(im2)
    W.append_data(im2)
    W.close()
    #
    R = iio.read(filename1)
    assert R.format.name == "TIFF"
    ims = list(R)  # == [im for im in R]
    assert (ims[0] == im2).all()
    # meta = R.get_meta_data()
    # assert meta['orientation'] == 'top_left'  # not there in later version
    # Fail
    with pytest.raises(IndexError):
        R.get_data(-1)

    with pytest.raises(IndexError):
        R.get_data(3)

    # Ensure imread + imwrite works round trip
    filename3 = tmp_path / "test_tiff2.tiff"
    im1 = iio.imread(filename1)
    iio.imwrite(filename3, im1)
    im3 = iio.imread(filename3)
    assert im1.ndim == 3
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Ensure imread + imwrite works round trip - volume like
    filename3 = tmp_path / "test_tiff2.tiff"
    im1 = np.stack(iio.mimread(filename1))
    iio.volwrite(filename3, im1)
    im3 = iio.volread(filename3)
    assert im1.ndim == 4
    assert im1.shape == im3.shape
    assert (im1 == im3).all()

    # Read metadata
    md = iio.get_reader(filename2).get_meta_data()
    assert not md["is_imagej"]
    assert md["description"] == "shape=(2,3,10,10)"
    assert md["description1"] == ""
    assert md["datetime"] == datetime.datetime(2015, 5, 9, 9, 8, 29)
    assert md["software"] == "tifffile.py"

    # Write metadata
    dt = datetime.datetime(2018, 8, 6, 15, 35, 5)
    with iio.get_writer(filename1, software="testsoftware") as w:
        w.append_data(
            np.zeros((10, 10)), meta={"description": "test desc", "datetime": dt}
        )
        w.append_data(np.zeros((10, 10)), meta={"description": "another desc"})
    with iio.get_reader(filename1) as r:
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
    iio3.imwrite(tmp_path / "v.tif", img)


def test_stk_volume(test_images):
    # this is a regression test for
    # https://github.com/imageio/imageio/issues/802

    expected = iio.volread(test_images / "movie.stk")
    actual = iio3.imread(test_images / "movie.stk")

    np.allclose(actual, expected)


def test_tiff_page_writing():
    # regression test for
    # https://github.com/imageio/imageio/issues/849
    base_image = np.full((256, 256, 3), 42, dtype=np.uint8)

    buffer = io.BytesIO()
    iio3.imwrite(buffer, base_image, extension=".tiff")
    buffer.seek(0)

    with tifffile.TiffFile(buffer) as file:
        assert len(file.pages) == 1


def test_bool_writing():
    # regression test for
    # https://github.com/imageio/imageio/issues/852

    expected = (np.arange(255 * 123) % 2 == 0).reshape((255, 123))

    img_bytes = iio3.imwrite("<bytes>", expected, extension=".tiff")
    actual = iio.imread(img_bytes)

    assert np.allclose(actual, expected)


def test_roundtrip(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/854

    iio3.imwrite(tmp_path / "test.tiff", np.ones((10, 64, 64), "u4"))
    actual = iio3.imread(tmp_path / "test.tiff")

    assert actual.shape == (10, 64, 64)


def test_volume_roudtrip(tmp_path):
    # regression test for
    # https://github.com/imageio/imageio/issues/818

    expected_volume = np.full((23, 123, 456, 3), 42, dtype=np.uint8)
    iio3.imwrite(tmp_path / "volume.tiff", expected_volume)

    # assert that the file indeed contains a volume
    with tifffile.TiffFile(tmp_path / "volume.tiff") as file:
        assert file.series[0].shape == (23, 123, 456, 3)
        assert len(file.series) == 1

    actual_volume = iio3.imread(tmp_path / "volume.tiff")
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

    actual_flat = iio3.imread(tmp_path / "flat.tiff")
    assert np.allclose(actual_flat, expected_flat)

    for idx, page in enumerate(iio3.imiter(tmp_path / "flat.tiff")):
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
    assert iio3.imread(tmp_path / "nightmare.tiff", index=0).shape == (4, 255, 255, 3)
    assert iio3.imread(tmp_path / "nightmare.tiff", index=1).shape == (255, 255, 3)
    assert iio3.imread(tmp_path / "nightmare.tiff", index=2).shape == (120, 73, 3)

    # imiter will yield the three images in order
    shapes = [(4, 255, 255, 3), (255, 255, 3), (120, 73, 3)]
    for image, shape in zip(iio3.imiter(tmp_path / "nightmare.tiff"), shapes):
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
