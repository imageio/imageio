""" Tests for imageio's pillow plugin
"""

import pytest
import os
import numpy as np
from pathlib import Path
import urllib.request
import shutil

import imageio as iio


@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory):
    # A temporary directory loaded with the test image files
    # downloaded once in the beginning
    tmp_path = tmp_path_factory.getbasetemp() / "image_cache"
    tmp_path.mkdir()
    imgs = [
        "chelsea.bmp",
        "chelsea.bsdf",
        "chelsea.jpg",
        "chelsea.npy",
        "chelsea_jpg.npy",
        "chelsea.png",
        "chelsea.zip",
        "newtonscradle_rgb.npy",
        "newtonscradle_rgba.npy",
        "newtonscradle.gif"
    ]
    base_url = "https://raw.githubusercontent.com/FirefoxMetzger/imageio-binaries/master/test-images/"
    for im in imgs:
        urllib.request.urlretrieve(base_url + im, tmp_path / im)
    return tmp_path_factory.getbasetemp()


@pytest.fixture
def image_files(tmp_dir):
    # create a copy of the test images for the actual tests
    # not avoid interaction between tests
    image_dir = tmp_dir / "image_cache"
    data_dir = tmp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    for item in image_dir.iterdir():
        if item.is_file():
            shutil.copy(item, data_dir / item.name)

    yield data_dir

    shutil.rmtree(data_dir)


@pytest.fixture
def test_image(request, image_files) -> np.array:
    im = np.zeros((1, 1, 3), dtype=np.uint8)

    if request.param == "rgb":
        im = np.zeros((42, 32, 3), np.uint8)
        im[:16, :, 0] = 250
        im[:, :16, 1] = 200
        im[50:, :16, 2] = 100
    elif request.param == "rgba":
        im = np.zeros((42, 32, 4), np.uint8)
        im[:16, :, 0] = 250
        im[:, :16, 1] = 200
        im[50:, :16, 2] = 100
        im[:, :, 3] = 255
        im[20:, :, 3] = 120
    elif request.param == "luminance0":
        im = np.zeros((42, 32), np.uint8)
        im[:16, :] = 200
    elif request.param == "luminance1":
        im = np.zeros((42, 32, 1), np.uint8)
        im[:16, :] = 200
    elif request.param == "chelsea":
        im = np.load(image_files / "chelsea.npy")
    elif request.param == "newtonscradle_rgb":
        im = np.load(image_files / "newtonscradle_rgb.npy")
    elif request.param == "newtonscradle_rgba":
        im = np.load(image_files / "newtonscradle_rgba.npy")

    return im

# --- Reading Tests ---


@pytest.mark.parametrize(
    "im_npy,im_out,im_comp",
    [
        ("chelsea.npy", "test.png", "chelsea.png"),
        ("chelsea.npy", "test.jpg", "chelsea.jpg"),
        ("chelsea.npy", "test.jpeg", "chelsea.jpg"),
        ("newtonscradle_rgb.npy", "test.gif", "newtonscradle.gif"),
        ("newtonscradle_rgba.npy", "test.gif", "newtonscradle.gif"),
    ],
)
def test_write(image_files: Path, im_npy: str, im_out: str, im_comp: str):
    im = np.load(image_files / im_npy)
    created_file = image_files / im_out

    with iio.imopen(created_file, plugin="pillow", legacy_api=False) as f:
        f.write(im)

    # file exists
    assert os.path.exists(created_file)

    # file content matches expected content
    target = image_files / im_comp
    assert target.read_bytes() == created_file.read_bytes()


@pytest.mark.parametrize(
    "im_in,npy_comp,mode",
    [
        ("chelsea.png", "chelsea.npy", "RGB"),
        ("chelsea.jpg", "chelsea_jpg.npy", "RGB"),
        ("newtonscradle.gif", "newtonscradle_rgb.npy", "RGB"),
        ("newtonscradle.gif", "newtonscradle_rgba.npy", "RGBA"),
    ],
)
def test_read(image_files: Path, im_in: str, npy_comp: str, mode: str):
    im_path = image_files / im_in
    im = iio.new_api.imread(im_path, legacy_api=False, plugin="pillow")

    target = np.load(image_files / npy_comp)
    assert np.allclose(im, target)


def test_png_compression(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    with iio.imopen(image_files / "1.png", legacy_api=False, plugin="pillow") as f:
        f.write(im, compress_level=0)

    with iio.imopen(image_files / "2.png", legacy_api=False, plugin="pillow") as f:
        f.write(im, compress_level=9)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_quantization(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    with iio.imopen(image_files / "1.png", legacy_api=False, plugin="pillow") as f:
        f.write(im, bits=8)

    with iio.imopen(image_files / "2.png", legacy_api=False, plugin="pillow") as f:
        f.write(im, bits=2)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1


def test_png_16bit(image_files: Path):
    # 16b bit images
    im = np.load(image_files / "chelsea.npy")[..., 0]

    with iio.imopen(image_files / "1.png", legacy_api=False, plugin="pillow") as f:
        f.write(2 * im.astype(np.uint16))

    with iio.imopen(image_files / "2.png", legacy_api=False, plugin="pillow") as f:
        f.write(im)

    size_1 = os.stat(image_files / "1.png").st_size
    size_2 = os.stat(image_files / "2.png").st_size
    assert size_2 < size_1

    im2 = iio.new_api.imread(image_files / "1.png")
    assert im2.dtype == np.uint16


# Note: There was a test here referring to issue #352 and a `prefer_uint8`
# argument that was introduced as a consequence This argument was default=true
# (for backwards compatibility) in the legacy plugin with the recommendation to
# set it to False. In the new API, we literally just wrap Pillow, so we match
# their behavior. Consequentially this test was removed.

def test_png_remote():
    # issue #202

    url = ("https://raw.githubusercontent.com/imageio/"
           "imageio-binaries/master/images/astronaut.png")
    response = urllib.request.urlopen(url)
    im = iio.new_api.imread(response, legacy_api=False, plugin="pillow")
    assert im.shape == (512, 512, 3)


def test_jpg_compression(image_files: Path):
    # Note: Note sure if we should test this or pillow

    im = np.load(image_files / "chelsea.npy")

    with iio.imopen(image_files / "1.jpg", legacy_api=False, plugin="pillow") as f:
        f.write(im, quality=90)

    with iio.imopen(image_files / "2.jpg", legacy_api=False, plugin="pillow") as f:
        f.write(im, quality=10)

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

    with iio.imopen(image_files / "chelsea_tagged.png", legacy_api=False, plugin="pillow") as f:
        f.write(im_flipped, exif=exif_tag)

    with iio.imopen(image_files / "chelsea_tagged.png", legacy_api=False, plugin="pillow") as f:
        im_reloaded = f.read()
        im_meta = f.get_meta()

    # ensure raw image is now portrait
    assert im_reloaded.shape[0] > im_reloaded.shape[1]
    # ensure that the Exif tag is set in the file
    assert "Orientation" in im_meta and im_meta["Orientation"] == 6

    with iio.imopen(image_files / "chelsea_tagged.png", legacy_api=False, plugin="pillow") as f:
        im_rotated = f.read(rotate=True)

    assert np.array_equal(im, im_rotated)


def get_ref_im(colors, crop, isfloat):
    """Get reference image with
    * colors: 0, 1, 3, 4
    * cropping: 0-> none, 1-> crop, 2-> crop with non-contiguous data
    * float: False, True
    """
    assert colors in (0, 1, 3, 4)
    assert crop in (0, 1, 2)
    assert isfloat in (False, True)
    rim = [im0, im1, None, im3, im4][colors]
    if isfloat:
        rim = rim.astype(np.float32) / 255.0
    if crop == 1:
        rim = rim[:-1, :-1].copy()
    elif crop == 2:
        rim = rim[:-1, :-1]
    return rim


def assert_close(im1, im2, tol=0.0):
    if im1.ndim == 3 and im1.shape[-1] == 1:
        im1 = im1.reshape(im1.shape[:-1])
    if im2.ndim == 3 and im2.shape[-1] == 1:
        im2 = im2.reshape(im2.shape[:-1])
    assert im1.shape == im2.shape
    diff = im1.astype("float32") - im2.astype("float32")
    diff[15:17, :] = 0  # Mask edge artifacts
    diff[:, 15:17] = 0
    assert np.abs(diff).max() <= tol
    # import visvis as vv
    # vv.subplot(121); vv.imshow(im1); vv.subplot(122); vv.imshow(im2)

# TODO: Recover JPEG tests from old PC's hard drive

def test_gif_rgb_vs_rgba(image_files: Path):
    # Note: I don't understand the point of this test
    im_rgb = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGB")
    im_rgba = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")

    assert np.allclose(im_rgb, im_rgba[..., :3])

def test_gif_gray(image_files: Path):
    # Note: There was no assert here; we test that it doesn't crash?
    im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="L")

    with iio.imopen(image_files / "test.gif", legacy_api=False, plugin="pillow") as file:
        file.save(im[..., 0], duration=0.2)

def test_gif_irregular_duration(image_files: Path):
    im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")
    duration = [0.5 if x in [2, 5, 7] else 0.1 for idx in range(im.shape[0])]

    with iio.imopen(image_files / "test.gif", legacy_api=False, plugin="pillow") as file:
        for frame, duration in zip(im, duration):
            file.save(frame, duration=duration)

    # how to assert duration here

def test_gif_palletsize(image_files: Path):
    im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")

    with iio.imopen(image_files / "test.gif", legacy_api=False, plugin="pillow") as file:
        file.save(im, palettesize=100)
    
    # TODO: assert pallet size is 128

def test_gif_loop_and_fps(image_files: Path):
    # Note: I think this test tests pillow kwargs, not imageio functionality
    # maybe we should drop it?

    im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")

    with iio.imopen(image_files / "test.gif", legacy_api=False, plugin="pillow") as file:
        file.save(im, palettesize=100, fps=20, loop=2)

    # This test had no assert; how to assert fps and loop count?

def test_gif_subrectangles(image_files: Path):
    im = iio.new_api.imread(image_files / "newtonscradle.gif", legacy_api=False, plugin="pillow", mode="RGBA")
    im = np.stack((im, im[-1]), axis=0)

    # TODO: Copy filesize test from JPG tests
    # # Test subrectangles
    # imageio.mimsave(fnamebase + ".subno.gif", ims, subrectangles=False)
    # imageio.mimsave(fnamebase + ".subyes.gif", ims, subrectangles=True)
    # s1 = os.stat(fnamebase + ".subno.gif").st_size
    # s2 = os.stat(fnamebase + ".subyes.gif").st_size
    # assert s2 < s1

def test_gif_transparent_pixel(image_files: Path):
    # see issue #245

def test_images_with_transparency():
    # Not alpha channel, but transparent pixels, see issue #245 and #246
    need_internet()

    fname = get_remote_file("images/imageio_issue245.gif")
    im = imageio.imread(fname)
    assert im.shape == (24, 30, 4)

    fname = get_remote_file("images/imageio_issue246.png")
    im = imageio.imread(fname)
    assert im.shape == (24, 30, 4)


def test_gamma_correction():
    need_internet()

    fname = get_remote_file("images/kodim03.png")

    # Load image three times
    im1 = imageio.imread(fname)
    im2 = imageio.imread(fname, ignoregamma=True)
    im3 = imageio.imread(fname, ignoregamma=False)

    # Default is to ignore gamma
    assert np.all(im1 == im2)

    # Test result depending of application of gamma
    assert im1.meta["gamma"] < 1
    assert im1.mean() == im2.mean()
    assert im2.mean() < im3.mean()

    # test_regression_302
    for im in (im1, im2, im3):
        assert im.shape == (512, 768, 3) and im.dtype == "uint8"


def test_inside_zipfile():
    need_internet()

    fname = os.path.join(test_dir, "pillowtest.zip")
    with ZipFile(fname, "w") as z:
        z.writestr("x.png", open(get_remote_file(
            "images/chelsea.png"), "rb").read())
        z.writestr("x.jpg", open(get_remote_file(
            "images/rommel.jpg"), "rb").read())

    for name in ("x.png", "x.jpg"):
        imageio.imread(fname + "/" + name)


def test_bmp():
    need_internet()
    fname = get_remote_file("images/scribble_P_RGB.bmp", test_dir)

    imageio.imread(fname)
    imageio.imread(fname, pilmode="RGB")
    imageio.imread(fname, pilmode="RGBA")


def test_scipy_imread_compat():
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imread.html
    # https://github.com/scipy/scipy/blob/41a3e69ca3141d8bf996bccb5eca5fc7bbc21a51/scipy/misc/pilutil.py#L111

    im = imageio.imread("imageio:chelsea.png")
    assert im.shape == (300, 451, 3) and im.dtype == "uint8"

    # Scipy users may default to using "mode", but our getreader() already has
    # a "mode" argument, so they should use pilmode instead.
    try:
        im = imageio.imread("imageio:chelsea.png", mode="L")
    except TypeError as err:
        assert "pilmode" in str(err)

    im = imageio.imread("imageio:chelsea.png", pilmode="RGBA")
    assert im.shape == (300, 451, 4) and im.dtype == "uint8"

    im = imageio.imread("imageio:chelsea.png", pilmode="L")
    assert im.shape == (300, 451) and im.dtype == "uint8"

    im = imageio.imread("imageio:chelsea.png", pilmode="F")
    assert im.shape == (300, 451) and im.dtype == "float32"

    im = imageio.imread("imageio:chelsea.png", as_gray=True)
    assert im.shape == (300, 451) and im.dtype == "float32"

    # Force using pillow (but really, Pillow's imageio's first choice! Except
    # for tiff)
    im = imageio.imread("imageio:chelsea.png", "PNG-PIL")


if __name__ == "__main__":
    # test_inside_zipfile()
    # test_png()
    # test_animated_gif()
    # test_bmp()
    run_tests_if_main()
