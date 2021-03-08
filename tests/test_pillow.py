""" Tests for imageio's pillow plugin
"""

import os
import pytest
import numpy as np
from pathlib import Path
import shutil
import urllib.request
from PIL import Image, ImageSequence

import imageio as iio


@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory):
    # A temporary directory loaded with the test image files
    # downloaded once in the beginning
    tmp_path = tmp_path_factory.getbasetemp() / "image_cache"
    tmp_path.mkdir()

    # download the (only) test images via git's sparse-checkout
    current_path = os.getcwd()
    os.chdir(tmp_path)
    os.system(
        "git clone --sparse --filter=blob:none https://github.com/FirefoxMetzger/imageio-binaries.git ."
    )
    os.system("git sparse-checkout init --cone")
    os.system("git sparse-checkout add test-images")
    os.chdir(current_path)

    return tmp_path_factory.getbasetemp()


@pytest.fixture
def image_files(tmp_dir):
    # create a copy of the test images for the actual tests
    # not avoid interaction between tests
    image_dir = tmp_dir / "image_cache" / "test-images"
    data_dir = tmp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    for item in image_dir.iterdir():
        if item.is_file():
            shutil.copy(item, data_dir / item.name)

    yield data_dir

    shutil.rmtree(data_dir)


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
    iio.new_api.imwrite(iio_file, im, plugin="pillow")

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
    iio.new_api.imwrite(iio_file, im, plugin="pillow")

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
    iio_im = iio.new_api.imread(im_path, plugin="pillow", mode=mode)

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

    iio.new_api.imwrite(image_files / "1.png", im, plugin="pillow", compress_level=0)
    iio.new_api.imwrite(image_files / "2.png", im, plugin="pillow", compress_level=9)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_quantization(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    iio.new_api.imwrite(image_files / "1.png", im, plugin="pillow", bits=8)
    iio.new_api.imwrite(image_files / "2.png", im, plugin="pillow", bits=2)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_16bit(image_files: Path):
    # 16b bit images
    im = np.load(image_files / "chelsea.npy")[..., 0]

    iio.new_api.imwrite(
        image_files / "1.png", 2 * im.astype(np.uint16), plugin="pillow", mode="I;16"
    )
    iio.new_api.imwrite(image_files / "2.png", im, plugin="pillow", mode="L")

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1

    im2 = iio.new_api.imread(image_files / "2.png")
    assert im2.dtype == np.uint8

    im3 = iio.new_api.imread(image_files / "1.png")
    assert im3.dtype == np.int32


# Note: There was a test here referring to issue #352 and a `prefer_uint8`
# argument that was introduced as a consequence This argument was default=true
# (for backwards compatibility) in the legacy plugin with the recommendation to
# set it to False. In the new API, we literally just wrap Pillow, so we match
# their behavior. Consequentially this test was removed.


def test_png_remote():
    # issue #202

    url = "https://github.com/FirefoxMetzger/imageio-binaries/blob/master/test-images/chelsea.png?raw=true"
    response = urllib.request.urlopen(url)
    im = iio.new_api.imread(response, plugin="pillow")
    assert im.shape == (300, 451, 3)


def test_png_transparent_pixel(image_files: Path):
    # see issue #245
    im = iio.new_api.imread(
        image_files / "imageio_issue246.png", plugin="pillow", mode="RGBA"
    )
    assert im.shape == (24, 30, 4)


def test_png_gamma_correction(image_files: Path):
    with iio.imopen(image_files / "kodim03.png", "r", plugin="pillow") as f:
        im1 = f.read()
        im1_meta = f.get_meta()

    im2 = iio.new_api.imread(
        image_files / "kodim03.png", plugin="pillow", apply_gamma=True
    )

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

    iio.new_api.imwrite(image_files / "1.jpg", im, plugin="pillow", quality=90)
    iio.new_api.imwrite(image_files / "2.jpg", im, plugin="pillow", quality=10)

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

    iio.new_api.imwrite(
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

    im_reloaded = iio.new_api.imread(
        image_files / "chelsea_tagged.png", plugin="pillow", rotate=True
    )

    assert np.array_equal(im, im_reloaded)


def test_gif_rgb_vs_rgba(image_files: Path):
    # Note: I don't understand the point of this test
    im_rgb = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGB"
    )
    im_rgba = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA"
    )

    assert np.allclose(im_rgb, im_rgba[..., :3])


def test_gif_gray(image_files: Path):
    # Note: There was no assert here; we test that it doesn't crash?
    im = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="L"
    )

    iio.new_api.imwrite(
        image_files / "test.gif", im[..., 0], plugin="pillow", duration=0.2, mode="L"
    )


def test_gif_irregular_duration(image_files: Path):
    im = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA"
    )
    duration = [0.5 if idx in [2, 5, 7] else 0.1 for idx in range(im.shape[0])]

    with iio.imopen(image_files / "test.gif", "w", plugin="pillow") as file:
        for frame, duration in zip(im, duration):
            file.write(frame, duration=duration)

    # how to assert duration here


def test_gif_palletsize(image_files: Path):
    im = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA"
    )

    iio.new_api.imwrite(image_files / "test.gif", im, plugin="pillow", palletsize=100)
    # TODO: assert pallet size is 128


def test_gif_loop_and_fps(image_files: Path):
    # Note: I think this test tests pillow kwargs, not imageio functionality
    # maybe we should drop it?

    im = iio.new_api.imread(
        image_files / "newtonscradle.gif", plugin="pillow", mode="RGBA"
    )

    with iio.imopen(image_files / "test.gif", "w", plugin="pillow") as file:
        for frame in im:
            file.write(frame, palettesize=100, fps=20, loop=2)

    # This test had no assert; how to assert fps and loop count?


# TODO: introduce new plugin for writing compressed GIF
# This is not what pillow does, and hence unexpected when explicitly calling
# for pillow
# def test_gif_subrectangles(image_files: Path):
#     # feature might be made obsolete by upstream (pillow) supporting it natively
#     # related issues: https://github.com/python-pillow/Pillow/issues/4977
#     im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")
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
    im = iio.new_api.imread(
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
