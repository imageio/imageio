""" Tests for imageio's pillow plugin
"""

from pathlib import Path

from imageio.core.request import Request
import os
import io
import pytest
import numpy as np
from PIL import Image, ImageSequence

import imageio as iio
from imageio.core.v3_plugin_api import PluginV3
from imageio.plugins.pillow import PillowPlugin
from imageio.core.request import InitializationError


@pytest.mark.parametrize(
    "im_npy,im_out,im_comp",
    [
        ("chelsea.npy", "iio.png", "pil.png"),
        ("chelsea.npy", "iio.jpg", "pil.jpg"),
        ("chelsea.npy", "iio.jpeg", "pil.jpg"),
        ("chelsea.npy", "iio.bmp", "pil.bmp"),
    ],
)
def test_write_single_frame(test_images, tmp_path, im_npy, im_out, im_comp):

    # the base image as numpy array
    im = np.load(test_images / im_npy)
    # written with imageio
    iio_file = tmp_path / im_out
    iio.v3.imwrite(iio_file, im, plugin="pillow")

    # written with pillow directly
    pil_file = tmp_path / im_comp
    Image.fromarray(im).save(pil_file)

    # file exists
    assert os.path.exists(iio_file)

    # imageio content matches pillow content
    assert iio_file.read_bytes() == pil_file.read_bytes()


@pytest.mark.parametrize(
    "im_npy,im_out,im_comp",
    [
        # Note: There might be a problem with reading/writing frames
        # Tracking Issue: https://github.com/python-pillow/Pillow/issues/5307
        ("newtonscradle_rgb.npy", "iio.gif", "pil.gif"),
        # ("newtonscradle_rgba.npy", "iio.gif", "pil.gif"),
    ],
)
@pytest.mark.needs_internet
def test_write_multiframe(test_images, tmp_path, im_npy, im_out, im_comp):

    # the base image as numpy array
    im = np.load(test_images / im_npy)
    # written with imageio
    iio_file = tmp_path / im_out
    iio.v3.imwrite(iio_file, im, plugin="pillow")

    # written with pillow directly
    pil_file = tmp_path / im_comp
    pil_images = [Image.fromarray(frame) for frame in im]
    pil_images[0].save(pil_file, save_all=True, append_images=pil_images[1:])

    # file exists
    assert os.path.exists(iio_file)

    # imageio content matches pillow content
    assert iio_file.read_bytes() == pil_file.read_bytes()


@pytest.mark.parametrize(
    "im_in,mode",
    [
        ("chelsea.png", "RGB"),
        ("chelsea.jpg", "RGB"),
        ("chelsea.bmp", "RGB"),
        ("newtonscradle.gif", "RGB"),
        ("newtonscradle.gif", "RGBA"),
    ],
)
def test_read(test_images, im_in, mode):
    im_path = test_images / im_in
    iio_im = iio.v3.imread(im_path, plugin="pillow", mode=mode, index=None)

    pil_im = np.asarray(
        [
            np.array(frame.convert(mode))
            for frame in ImageSequence.Iterator(Image.open(im_path))
        ]
    )

    assert np.allclose(iio_im, pil_im)


@pytest.mark.parametrize(
    "im_in,mode",
    [
        ("newtonscradle.gif", "RGB"),
        ("newtonscradle.gif", "RGBA"),
    ],
)
def test_gif_legacy_pillow(test_images, im_in, mode):
    """
    This test tests backwards compatibility of using the new API
    with a legacy plugin. IN particular reading ndimages

    I'm not sure where this test should live, so it is here for now.
    """

    im_path = test_images / im_in
    with iio.imopen(im_path, "r", legacy_mode=True, plugin="GIF-PIL") as file:
        iio_im = file.read(pilmode=mode, index=None)

    pil_im = np.asarray(
        [
            np.array(frame.convert(mode))
            for frame in ImageSequence.Iterator(Image.open(im_path))
        ]
    )
    if pil_im.shape[0] == 1:
        pil_im = pil_im.squeeze(axis=0)

    assert np.allclose(iio_im, pil_im)


def test_png_compression(test_images, tmp_path):
    # Note: Note sure if we should test this or pillow

    im = np.load(test_images / "chelsea.npy")

    iio.v3.imwrite(tmp_path / "1.png", im, plugin="pillow", compress_level=0)
    iio.v3.imwrite(tmp_path / "2.png", im, plugin="pillow", compress_level=9)

    size_1 = os.stat(tmp_path / "1.png").st_size
    size_2 = os.stat(tmp_path / "2.png").st_size
    assert size_2 < size_1


def test_png_quantization(test_images, tmp_path):
    # Note: Note sure if we should test this or pillow

    im = np.load(test_images / "chelsea.npy")

    iio.v3.imwrite(tmp_path / "1.png", im, plugin="pillow", bits=8)
    iio.v3.imwrite(tmp_path / "2.png", im, plugin="pillow", bits=2)

    size_1 = os.stat(tmp_path / "1.png").st_size
    size_2 = os.stat(tmp_path / "2.png").st_size
    assert size_2 < size_1


def test_png_16bit(test_images, tmp_path):
    # 16b bit images
    im = np.load(test_images / "chelsea.npy")[..., 0]

    iio.v3.imwrite(
        tmp_path / "1.png",
        2 * im.astype(np.uint16),
        plugin="pillow",
        mode="I;16",
    )
    iio.v3.imwrite(tmp_path / "2.png", im, plugin="pillow", mode="L")

    size_1 = os.stat(tmp_path / "1.png").st_size
    size_2 = os.stat(tmp_path / "2.png").st_size
    assert size_2 < size_1

    im2 = iio.v3.imread(tmp_path / "2.png", plugin="pillow")
    assert im2.dtype == np.uint8

    im3 = iio.v3.imread(tmp_path / "1.png", plugin="pillow")
    assert im3.dtype == np.int32


# Note: There was a test here referring to issue #352 and a `prefer_uint8`
# argument that was introduced as a consequence This argument was default=true
# (for backwards compatibility) in the legacy plugin with the recommendation to
# set it to False. In the new API, we literally just wrap Pillow, so we match
# their behavior. Consequentially this test was removed.


@pytest.mark.needs_internet
def test_png_remote():
    # issue #202

    url = "https://github.com/imageio/imageio-binaries/blob/master/test-images/chelsea.png?raw=true"
    im = iio.v3.imread(url, plugin="pillow")
    assert im.shape == (300, 451, 3)


def test_png_transparent_pixel(test_images):
    # see issue #245
    im = iio.v3.imread(
        test_images / "imageio_issue246.png",
        plugin="pillow",
        mode="RGBA",
    )
    assert im.shape == (24, 30, 4)


def test_png_gamma_correction(test_images: Path):
    # opens the file twice, but touches more parts of the API
    im1 = iio.v3.imread(test_images / "kodim03.png", plugin="pillow")
    im1_meta = iio.v3.immeta(
        test_images / "kodim03.png", plugin="pillow", exclude_applied=False
    )

    im2 = iio.v3.imread(
        test_images / "kodim03.png",
        plugin="pillow",
        apply_gamma=True,
    )

    # Test result depending of application of gamma
    assert im1_meta["gamma"] < 1
    assert im1.mean() < im2.mean()

    assert im1.shape == (512, 768, 3)
    assert im1.dtype == "uint8"
    assert im2.shape == (512, 768, 3)
    assert im2.dtype == "uint8"


def test_jpg_compression(test_images, tmp_path):
    # Note: Note sure if we should test this or pillow

    im = np.load(test_images / "chelsea.npy")

    iio.v3.imwrite(tmp_path / "1.jpg", im, plugin="pillow", quality=90)
    iio.v3.imwrite(tmp_path / "2.jpg", im, plugin="pillow", quality=10)

    size_1 = os.stat(tmp_path / "1.jpg").st_size
    size_2 = os.stat(tmp_path / "2.jpg").st_size
    assert size_2 < size_1


def test_exif_orientation(test_images, tmp_path):
    from PIL.Image import Exif

    im = np.load(test_images / "chelsea.npy")

    # original image is has landscape format
    assert im.shape[0] < im.shape[1]

    im_flipped = np.rot90(im, -1)
    exif_tag = Exif()
    exif_tag[274] = 6  # Set Orientation to 6

    iio.v3.imwrite(
        tmp_path / "chelsea_tagged.png",
        im_flipped,
        plugin="pillow",
        exif=exif_tag,
    )

    with iio.imopen(
        tmp_path / "chelsea_tagged.png",
        "r",
        plugin="pillow",
    ) as f:
        im_reloaded = f.read()
        im_meta = f.get_meta()

    # ensure raw image is now portrait
    assert im_reloaded.shape[0] > im_reloaded.shape[1]
    # ensure that the Exif tag is set in the file
    assert "Orientation" in im_meta and im_meta["Orientation"] == 6

    im_reloaded = iio.v3.imread(
        tmp_path / "chelsea_tagged.png", plugin="pillow", rotate=True
    )

    assert np.array_equal(im, im_reloaded)


def test_gif_rgb_vs_rgba(test_images):
    # Note: I don't understand the point of this test
    im_rgb = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="RGB",
    )
    im_rgba = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="RGBA",
    )

    assert np.allclose(im_rgb, im_rgba[..., :3])


def test_gif_gray(test_images, tmp_path):
    # Note: There was no assert here; we test that it doesn't crash?
    im = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="L",
    )

    iio.v3.imwrite(
        tmp_path / "test.gif",
        im[..., 0],
        plugin="pillow",
        duration=0.2,
        mode="L",
    )


def test_gif_irregular_duration(test_images, tmp_path):
    im = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="RGBA",
    )
    duration = [0.5 if idx in [2, 5, 7] else 0.1 for idx in range(im.shape[0])]

    with iio.imopen(tmp_path / "test.gif", "w", plugin="pillow") as file:
        for frame, duration in zip(im, duration):
            file.write(frame, duration=duration)

    # how to assert duration here


def test_gif_palletsize(test_images, tmp_path):
    im = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="RGBA",
    )

    iio.v3.imwrite(tmp_path / "test.gif", im, plugin="pillow", palletsize=100)
    # TODO: assert pallet size is 128


def test_gif_loop_and_fps(test_images, tmp_path):
    # Note: I think this test tests pillow kwargs, not imageio functionality
    # maybe we should drop it?

    im = iio.v3.imread(
        test_images / "newtonscradle.gif",
        plugin="pillow",
        mode="RGBA",
    )

    with iio.imopen(tmp_path / "test.gif", "w", plugin="pillow") as file:
        for frame in im:
            file.write(frame, palettesize=100, fps=20, loop=2)

    # This test had no assert; how to assert fps and loop count?


def test_gif_indexed_read(test_images):
    idx = 0
    numpy_im = np.load(test_images / "newtonscradle_rgb.npy")[idx, ...]

    with iio.imopen(test_images / "newtonscradle.gif", "r", plugin="pillow") as file:
        # exists to touch branch, would be better two write an explicit test
        meta = file.get_meta(index=idx)
        assert "version" in meta

        pillow_im = file.read(index=idx, mode="RGB")

    assert np.allclose(pillow_im, numpy_im)


def test_unknown_image(tmp_path):
    with open(tmp_path / "foo.unknown", "w") as file:
        file.write("This image, which is actually no image, has an unknown image type.")

    with pytest.raises(InitializationError):
        r = Request(tmp_path / "foo.unknown", "r")
        PillowPlugin(r)


# TODO: introduce new plugin for writing compressed GIF
# This is not what pillow does, and hence unexpected when explicitly calling
# for pillow
# def test_gif_subrectangles(test_images, tmp_path):
#     # feature might be made obsolete by upstream (pillow) supporting it natively
#     # related issues: https://github.com/python-pillow/Pillow/issues/4977
#     im = iio.v3.imread(test_images / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")
#     im = np.stack((*im, im[-1]), axis=0)
#     print(im.dtype)

#     with iio.imopen(tmp_path / "1.gif", legacy_api=False, plugin="pillow") as f:
#         f.write(im, subrectangles=False, mode="RGBA")

#     with iio.imopen(tmp_path / "2.gif", legacy_api=False, plugin="pillow") as f:
#         f.write(im, subrectangles=True, mode="RGBA")

#     size_1 = os.stat(tmp_path / "1.gif").st_size
#     size_2 = os.stat(tmp_path / "2.gif").st_size
#     assert size_2 < size_1


def test_gif_transparent_pixel(test_images):
    # see issue #245
    im = iio.v3.imread(
        test_images / "imageio_issue245.gif",
        plugin="pillow",
        mode="RGBA",
    )
    assert im.shape == (24, 30, 4)


# TODO: Pillow actually doesn't read zip. This should be a different plugin.
# def test_inside_zipfile(test_images):

#     fname = os.path.join(tmp_path, "pillowtest.zip")
#     with ZipFile(fname, "w") as z:
#         z.writestr("x.png", open(test_images / "chelsea.png", "rb").read())
#         z.writestr("x.jpg", open(test_images / "rommel.jpg", "rb").read())

#     for name in ("x.png", "x.jpg"):
#         imageio.imread(fname + "/" + name)


def test_legacy_exif_orientation(test_images, tmp_path):
    from PIL.Image import Exif

    im = np.load(test_images / "chelsea.npy")

    # original image is has landscape format
    assert im.shape[0] < im.shape[1]

    im_flipped = np.rot90(im, -1)
    exif_tag = Exif()
    exif_tag[274] = 6  # Set Orientation to 6

    iio.v3.imwrite(
        tmp_path / "chelsea_tagged.png",
        im_flipped,
        plugin="pillow",
        exif=exif_tag,
    )

    with iio.imopen(
        tmp_path / "chelsea_tagged.png",
        "r",
        legacy_mode=True,
        plugin="PNG-PIL",
    ) as f:
        im_reloaded = np.asarray(f.read()[0])
        im_meta = f.get_meta()

    # ensure raw image is now portrait
    assert im_reloaded.shape[0] > im_reloaded.shape[1]
    # ensure that the Exif tag is set in the file
    assert "exif" in im_meta

    im_reloaded = iio.v3.imread(
        tmp_path / "chelsea_tagged.png", plugin="pillow", rotate=True
    )

    assert np.array_equal(im, im_reloaded)


def test_incomatible_write_format(tmp_path):
    with pytest.raises(IOError):
        iio.v3.imopen(tmp_path / "foo.mp3", "w", plugin="pillow", legacy_mode=False)


def test_write_to_bytes():
    image = (np.random.rand(600, 800, 3) * 255).astype(np.uint8)

    # writing to bytes with pillow
    with io.BytesIO() as output:
        Image.fromarray(image).save(output, format="PNG")
        contents = output.getvalue()

    # writing to bytes with imageIO
    with io.BytesIO() as output:
        iio.v3.imwrite(output, image, plugin="pillow", format="PNG")
        iio_contents = output.getvalue()

    assert iio_contents == contents


def test_write_to_bytes_rgba():
    image = (np.random.rand(600, 800, 4) * 255).astype(np.uint8)

    # writing to bytes with pillow
    with io.BytesIO() as output:
        Image.fromarray(image).save(output, format="PNG")
        contents = output.getvalue()

    # writing to bytes with imageIO
    with io.BytesIO() as output:
        iio.v3.imwrite(output, image, plugin="pillow", format="PNG", mode="RGBA")
        iio_contents = output.getvalue()

    assert iio_contents == contents


def test_write_to_bytes_imwrite():
    image = (np.random.rand(600, 800, 3) * 255).astype(np.uint8)

    # writing to bytes with pillow
    with io.BytesIO() as output:
        Image.fromarray(image).save(output, format="PNG")
        contents = output.getvalue()

    # write with ImageIO
    bytes_string = iio.v3.imwrite("<bytes>", image, plugin="pillow", format="PNG")

    assert contents == bytes_string


def test_write_to_bytes_jpg():
    image = (np.random.rand(600, 800, 3) * 255).astype(np.uint8)

    # writing to bytes with pillow
    with io.BytesIO() as output:
        Image.fromarray(image).save(output, format="JPEG")
        contents = output.getvalue()

    # write with ImageIO
    bytes_string = iio.v3.imwrite("<bytes>", image, plugin="pillow", format="JPEG")

    assert contents == bytes_string


def test_write_jpg_to_bytes_io():
    # this is a regression test
    # see: https://github.com/imageio/imageio/issues/687

    image = np.zeros((200, 200), dtype=np.uint8)
    bytes_io = io.BytesIO()
    iio.v3.imwrite(bytes_io, image, plugin="pillow", format="jpeg", mode="L")
    bytes_io.seek(0)

    image_from_file = iio.v3.imread(bytes_io, plugin="pillow")
    assert np.allclose(image_from_file, image)


def test_initialization_failure(test_images):
    test_image = b"this is not an image and will break things."

    with pytest.raises(OSError):
        iio.v3.imread(test_image, plugin="pillow")

    with pytest.raises(OSError):
        # pillow can not handle npy
        iio.v3.imread(test_images / "chelsea_jpg.npy", plugin="pillow")


def test_boolean_reading(tmp_path):
    # Bugfix: https://github.com/imageio/imageio/issues/721
    expected = np.arange(256 * 256).reshape((256, 256)) % 2 == 0

    Image.fromarray(expected).save(tmp_path / "iio.png")

    actual = iio.v3.imread(tmp_path / "iio.png")
    assert np.allclose(actual, expected)


def test_boolean_writing(tmp_path):
    # Bugfix: https://github.com/imageio/imageio/issues/721
    expected = np.arange(256 * 256).reshape((256, 256)) % 2 == 0

    iio.v3.imwrite(tmp_path / "iio.png", expected)

    actual = np.asarray(Image.open(tmp_path / "iio.png"))
    # actual = iio.v3.imread(tmp_path / "iio.png")
    assert np.allclose(actual, expected)


def test_quantized_gif(test_images, tmp_path):
    original = iio.v3.imread(test_images / "newtonscradle.gif")

    iio.v3.imwrite(tmp_path / "quantized.gif", original, plugin="pillow", bits=4)
    quantized = iio.v3.imread(tmp_path / "quantized.gif")

    for original_frame, quantized_frame in zip(original, quantized):
        assert len(np.unique(quantized_frame)) <= len(np.unique(original_frame))


def test_properties(image_files: Path):
    file: PluginV3

    # test a flat image (RGB PNG)
    with iio.v3.imopen(image_files / "chelsea.png", "r", plugin="pillow") as file:
        properties = file.properties(index=0)

    assert properties.shape == (300, 451, 3)
    assert properties.dtype == np.uint8

    # test a ndimage (GIF)
    properties = iio.v3.improps(
        image_files / "newtonscradle.gif", plugin="pillow", index=None
    )
    assert properties.shape == (36, 150, 200, 3)
    assert properties.dtype == np.uint8
    assert properties.is_batch is True

    # test a flat gray image
    with iio.v3.imopen(image_files / "text.png", "r", plugin="pillow") as file:
        properties = file.properties(index=0)

    assert properties.shape == (172, 448)
    assert properties.dtype == np.uint8


def test_metadata(test_images):
    meta = iio.v3.immeta(test_images / "newtonscradle.gif")
    assert "version" in meta and meta["version"] == b"GIF89a"

    with iio.v3.imopen(
        test_images / "newtonscradle.gif", "r", plugin="pillow"
    ) as image_file:
        image_file.read(index=5)
        meta = image_file.metadata(index=0)
        assert "version" in meta and meta["version"] == b"GIF89a"


def test_apng_reading(tmp_path, test_images):
    # create a APNG
    img = iio.v3.imread(test_images / "newtonscradle.gif", index=None)
    iio.v3.imwrite(tmp_path / "test.apng", img)

    # test single image read
    with Image.open(tmp_path / "test.apng") as im:
        im.seek(8)
        expected = np.asarray(im)
    actual = iio.v3.imread(tmp_path / "test.apng", index=8)
    assert np.allclose(actual, expected)

    # test reading all frames
    all_frames = iio.v3.imread(tmp_path / "test.apng", index=None)
    with Image.open(tmp_path / "test.apng") as im:
        for idx, frame in enumerate(ImageSequence.Iterator(im)):
            expected = np.asarray(frame)
            actual = all_frames[idx]
            assert np.allclose(actual, expected)
