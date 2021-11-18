""" Tests for imageio's pillow plugin
"""

from imageio.core.request import Request
import os
import io
import pytest
import numpy as np
from pathlib import Path
from PIL import Image, ImageSequence

import imageio as iio
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
def test_write_single_frame(image_files: Path, im_npy: str, im_out: str, im_comp: str):
    # the base image as numpy array
    im = np.load(image_files / im_npy)
    # written with imageio
    iio_file = image_files / im_out
    iio.v3.imwrite(iio_file, im, plugin="pillow")

    # written with pillow directly
    pil_file = image_files / im_comp
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
def test_write_multiframe(image_files: Path, im_npy: str, im_out: str, im_comp: str):
    # the base image as numpy array
    im = np.load(image_files / im_npy)
    # written with imageio
    iio_file = image_files / im_out
    iio.v3.imwrite(iio_file, im, plugin="pillow")

    # written with pillow directly
    pil_file = image_files / im_comp
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
def test_read(image_files: Path, im_in: str, mode: str):
    im_path = image_files / im_in
    iio_im = iio.v3.imread(im_path, plugin="pillow", mode=mode)

    pil_im = np.asarray(
        [
            np.array(frame.convert(mode))
            for frame in ImageSequence.Iterator(Image.open(im_path))
        ]
    )
    if pil_im.shape[0] == 1:
        pil_im = pil_im.squeeze(axis=0)

    assert np.allclose(iio_im, pil_im)


@pytest.mark.parametrize(
    "im_in,mode",
    [
        ("newtonscradle.gif", "RGB"),
        ("newtonscradle.gif", "RGBA"),
    ],
)
def test_gif_legacy_pillow(image_files: Path, im_in: str, mode: str):
    """
    This test tests backwards compatibility of using the new API
    with a legacy plugin. IN particular reading ndimages

    I'm not sure where this test should live, so it is here for now.
    """

    im_path = image_files / im_in
    with iio.imopen(im_path, "r", legacy_mode=True, plugin="GIF-PIL") as file:
        iio_im = file.read(pilmode=mode)

    pil_im = np.asarray(
        [
            np.array(frame.convert(mode))
            for frame in ImageSequence.Iterator(Image.open(im_path))
        ]
    )
    if pil_im.shape[0] == 1:
        pil_im = pil_im.squeeze(axis=0)

    assert np.allclose(iio_im, pil_im)


def test_png_compression(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    iio.v3.imwrite(image_files / "1.png", im, plugin="pillow", compress_level=0)
    iio.v3.imwrite(image_files / "2.png", im, plugin="pillow", compress_level=9)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_quantization(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    iio.v3.imwrite(image_files / "1.png", im, plugin="pillow", bits=8)
    iio.v3.imwrite(image_files / "2.png", im, plugin="pillow", bits=2)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_16bit(image_files: Path):
    # 16b bit images
    im = np.load(image_files / "chelsea.npy")[..., 0]

    iio.v3.imwrite(
        image_files / "1.png", 2 * im.astype(np.uint16), plugin="pillow", mode="I;16"
    )
    iio.v3.imwrite(image_files / "2.png", im, plugin="pillow", mode="L")

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1

    im2 = iio.v3.imread(image_files / "2.png", plugin="pillow")
    assert im2.dtype == np.uint8

    im3 = iio.v3.imread(image_files / "1.png", plugin="pillow")
    assert im3.dtype == np.int32


# Note: There was a test here referring to issue #352 and a `prefer_uint8`
# argument that was introduced as a consequence This argument was default=true
# (for backwards compatibility) in the legacy plugin with the recommendation to
# set it to False. In the new API, we literally just wrap Pillow, so we match
# their behavior. Consequentially this test was removed.


def test_png_remote():
    # issue #202

    url = "https://github.com/imageio/imageio-binaries/blob/master/test-images/chelsea.png?raw=true"
    im = iio.v3.imread(url, plugin="pillow")
    assert im.shape == (300, 451, 3)


def test_png_transparent_pixel(image_files: Path):
    # see issue #245
    im = iio.v3.imread(
        image_files / "imageio_issue246.png", plugin="pillow", mode="RGBA"
    )
    assert im.shape == (24, 30, 4)


def test_png_gamma_correction(image_files: Path):
    with iio.imopen(image_files / "kodim03.png", "r", plugin="pillow") as f:
        im1 = f.read()
        im1_meta = f.get_meta()

    im2 = iio.v3.imread(image_files / "kodim03.png", plugin="pillow", apply_gamma=True)

    # Test result depending of application of gamma
    assert im1_meta["gamma"] < 1
    assert im1.mean() < im2.mean()

    assert im1.shape == (512, 768, 3)
    assert im1.dtype == "uint8"
    assert im2.shape == (512, 768, 3)
    assert im2.dtype == "uint8"


def test_jpg_compression(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    iio.v3.imwrite(image_files / "1.jpg", im, plugin="pillow", quality=90)
    iio.v3.imwrite(image_files / "2.jpg", im, plugin="pillow", quality=10)

    size_1 = os.stat(image_files / "1.jpg").st_size
    size_2 = os.stat(image_files / "2.jpg").st_size
    assert size_2 < size_1


def test_exif_orientation(image_files: Path):
    from PIL.Image import Exif

    im = np.load(image_files / "chelsea.npy")

    # original image is has landscape format
    assert im.shape[0] < im.shape[1]

    im_flipped = np.rot90(im, -1)
    exif_tag = Exif()
    exif_tag[274] = 6  # Set Orientation to 6

    iio.v3.imwrite(
        image_files / "chelsea_tagged.png", im_flipped, plugin="pillow", exif=exif_tag
    )

    with iio.imopen(
        image_files / "chelsea_tagged.png",
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
        image_files / "chelsea_tagged.png", plugin="pillow", rotate=True
    )

    assert np.array_equal(im, im_reloaded)


def test_gif_rgb_vs_rgba(image_files: Path):
    # Note: I don't understand the point of this test
    im_rgb = iio.v3.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGB"
    )
    im_rgba = iio.v3.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA"
    )

    assert np.allclose(im_rgb, im_rgba[..., :3])


def test_gif_gray(image_files: Path):
    # Note: There was no assert here; we test that it doesn't crash?
    im = iio.v3.imread(image_files / "newtonscradle.gif", plugin="pillow", mode="L")

    iio.v3.imwrite(
        image_files / "test.gif", im[..., 0], plugin="pillow", duration=0.2, mode="L"
    )


def test_gif_irregular_duration(image_files: Path):
    im = iio.v3.imread(image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA")
    duration = [0.5 if idx in [2, 5, 7] else 0.1 for idx in range(im.shape[0])]

    with iio.imopen(image_files / "test.gif", "w", plugin="pillow") as file:
        for frame, duration in zip(im, duration):
            file.write(frame, duration=duration)

    # how to assert duration here


def test_gif_palletsize(image_files: Path):
    im = iio.v3.imread(image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA")

    iio.v3.imwrite(image_files / "test.gif", im, plugin="pillow", palletsize=100)
    # TODO: assert pallet size is 128


def test_gif_loop_and_fps(image_files: Path):
    # Note: I think this test tests pillow kwargs, not imageio functionality
    # maybe we should drop it?

    im = iio.v3.imread(image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA")

    with iio.imopen(image_files / "test.gif", "w", plugin="pillow") as file:
        for frame in im:
            file.write(frame, palettesize=100, fps=20, loop=2)

    # This test had no assert; how to assert fps and loop count?


def test_gif_indexed_read(image_files: Path):
    idx = 0
    numpy_im = np.load(image_files / "newtonscradle_rgb.npy")[idx, ...]

    with iio.imopen(image_files / "newtonscradle.gif", "r", plugin="pillow") as file:
        # exists to touch branch, would be better two write an explicit test
        meta = file.get_meta(index=idx)
        assert "version" in meta

        pillow_im = file.read(index=idx, mode="RGB")

    assert np.allclose(pillow_im, numpy_im)


def test_unknown_image(image_files: Path):
    with open(image_files / "foo.unknown", "w") as file:
        file.write("This image, which is actually no image, has an unknown image type.")

    with pytest.raises(InitializationError):
        r = Request(image_files / "foo.unknown", "r")
        PillowPlugin(r)


# TODO: introduce new plugin for writing compressed GIF
# This is not what pillow does, and hence unexpected when explicitly calling
# for pillow
# def test_gif_subrectangles(image_files: Path):
#     # feature might be made obsolete by upstream (pillow) supporting it natively
#     # related issues: https://github.com/python-pillow/Pillow/issues/4977
#     im = iio.v3.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")
#     im = np.stack((*im, im[-1]), axis=0)
#     print(im.dtype)

#     with iio.imopen(image_files / "1.gif", legacy_api=False, plugin="pillow") as f:
#         f.write(im, subrectangles=False, mode="RGBA")

#     with iio.imopen(image_files / "2.gif", legacy_api=False, plugin="pillow") as f:
#         f.write(im, subrectangles=True, mode="RGBA")

#     size_1 = os.stat(image_files / "1.gif").st_size
#     size_2 = os.stat(image_files / "2.gif").st_size
#     assert size_2 < size_1


def test_gif_transparent_pixel(image_files: Path):
    # see issue #245
    im = iio.v3.imread(
        image_files / "imageio_issue245.gif", plugin="pillow", mode="RGBA"
    )
    assert im.shape == (24, 30, 4)


# TODO: Pillow actually doesn't read zip. This should be a different plugin.
# def test_inside_zipfile():
#     need_internet()

#     fname = os.path.join(test_dir, "pillowtest.zip")
#     with ZipFile(fname, "w") as z:
#         z.writestr("x.png", open(get_remote_file(
#             "images/chelsea.png"), "rb").read())
#         z.writestr("x.jpg", open(get_remote_file(
#             "images/rommel.jpg"), "rb").read())

#     for name in ("x.png", "x.jpg"):
#         imageio.imread(fname + "/" + name)


def test_legacy_exif_orientation(image_files: Path):
    from PIL.Image import Exif

    im = np.load(image_files / "chelsea.npy")

    # original image is has landscape format
    assert im.shape[0] < im.shape[1]

    im_flipped = np.rot90(im, -1)
    exif_tag = Exif()
    exif_tag[274] = 6  # Set Orientation to 6

    iio.v3.imwrite(
        image_files / "chelsea_tagged.png", im_flipped, plugin="pillow", exif=exif_tag
    )

    with iio.imopen(
        image_files / "chelsea_tagged.png",
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
        image_files / "chelsea_tagged.png", plugin="pillow", rotate=True
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
