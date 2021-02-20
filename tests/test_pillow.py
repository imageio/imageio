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


def test_jpg():

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3):
                fname = fnamebase + "%i.%i.%i.jpg" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim)
                im = imageio.imread(fname)
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 1.1)  # lossy

    # No alpha in JPEG
    fname = fnamebase + ".jpg"
    raises(Exception, imageio.imsave, fname, im4)

    # Parameters
    imageio.imsave(
        fnamebase + ".jpg", im3, progressive=True, optimize=True, baseline=True
    )

    # Parameter fail - We let Pillow kwargs thorugh
    # raises(TypeError, imageio.imread, fnamebase + '.jpg', notavalidkwarg=1)
    # raises(TypeError, imageio.imsave, fnamebase + '.jpg', im, notavalidk=1)

    # Compression
    imageio.imsave(fnamebase + "1.jpg", im3, quality=10)
    imageio.imsave(fnamebase + "2.jpg", im3, quality=90)
    s1 = os.stat(fnamebase + "1.jpg").st_size
    s2 = os.stat(fnamebase + "2.jpg").st_size
    assert s2 > s1
    raises(ValueError, imageio.imsave, fnamebase + ".jpg", im, quality=120)


def test_jpg_more():
    need_internet()

    # Test broken JPEG
    fname = fnamebase + "_broken.jpg"
    open(fname, "wb").write(b"this is not an image")
    raises(Exception, imageio.imread, fname)
    #
    bb = imageio.imsave(imageio.RETURN_BYTES, get_ref_im(3, 0, 0), "JPEG")
    with open(fname, "wb") as f:
        f.write(bb[:400])
        f.write(b" ")
        f.write(bb[400:])
    raises(Exception, imageio.imread, fname)

    # Test EXIF stuff
    fname = get_remote_file("images/rommel.jpg")
    im = imageio.imread(fname)
    assert im.shape[0] > im.shape[1]
    im = imageio.imread(fname, exifrotate=False)
    assert im.shape[0] < im.shape[1]
    im = imageio.imread(fname, exifrotate=2)  # Rotation in Python
    assert im.shape[0] > im.shape[1]
    # Write the jpg and check that exif data is maintained
    if sys.platform.startswith("darwin"):
        return  # segfaults on my osx VM, why?
    imageio.imsave(fnamebase + "rommel.jpg", im)
    im = imageio.imread(fname)
    assert im.meta.EXIF_MAIN


def test_gif():
    # The not-animated gif

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 3, 4):
                if colors > 1 and sys.platform.startswith("darwin"):
                    continue  # quantize fails, see also png
                fname = fnamebase + "%i.%i.%i.gif" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim)
                im = imageio.imread(fname)
                mul = 255 if isfloat else 1
                if colors not in (0, 1):
                    im = im[:, :, :3]
                    rim = rim[:, :, :3]
                assert_close(rim * mul, im, 1.1)  # lossless

    # Parameter fail
    raises(TypeError, imageio.imread, fname, notavalidkwarg=True)
    raises(TypeError, imageio.imsave, fnamebase + "1.gif", im, notavalidk=True)


def test_animated_gif():

    # Read newton's cradle
    ims = imageio.mimread("imageio:newtonscradle.gif")
    assert len(ims) == 36
    for im in ims:
        assert im.shape == (150, 200, 4)
        assert im.min() > 0
        assert im.max() <= 255

    # Get images
    im = get_ref_im(4, 0, 0)
    ims = []
    for i in range(10):
        im = im.copy()
        im[:, -5:, 0] = i * 20
        ims.append(im)

    # Store - animated GIF always poops out RGB
    for isfloat in (False, True):
        for colors in (3, 4):
            ims1 = ims[:]
            if isfloat:
                ims1 = [x.astype(np.float32) / 256 for x in ims1]
            ims1 = [x[:, :, :colors] for x in ims1]
            fname = fnamebase + ".animated.%i.gif" % colors
            imageio.mimsave(fname, ims1, duration=0.2)
            # Retrieve
            print("fooo", fname, isfloat, colors)
            ims2 = imageio.mimread(fname)
            ims1 = [x[:, :, :3] for x in ims]  # fresh ref
            ims2 = [x[:, :, :3] for x in ims2]  # discart alpha
            for im1, im2 in zip(ims1, ims2):
                assert_close(im1, im2, 1.1)

    # We can also store grayscale
    fname = fnamebase + ".animated.%i.gif" % 1
    imageio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2)
    imageio.mimsave(fname, [x[:, :, :1] for x in ims], duration=0.2)

    # Irragular duration. You probably want to check this manually (I did)
    duration = [0.1 for i in ims]
    for i in [2, 5, 7]:
        duration[i] = 0.5
    imageio.mimsave(fnamebase + ".animated_irr.gif", ims, duration=duration)

    # Other parameters
    imageio.mimsave(fnamebase + ".animated.loop2.gif", ims, loop=2, fps=20)
    R = imageio.read(fnamebase + ".animated.loop2.gif")
    W = imageio.save(fnamebase + ".animated.palettes100.gif", palettesize=100)
    assert W._writer.opt_palette_size == 128
    # Fail
    assert raises(IndexError, R.get_meta_data, -1)
    assert raises(ValueError, imageio.mimsave, fname, ims, palettesize=300)
    assert raises(ValueError, imageio.mimsave, fname, ims, quantizer="foo")
    assert raises(ValueError, imageio.mimsave, fname, ims, duration="foo")

    # Add one duplicate image to ims to touch subractangle with not change
    ims.append(ims[-1])

    # Test subrectangles
    imageio.mimsave(fnamebase + ".subno.gif", ims, subrectangles=False)
    imageio.mimsave(fnamebase + ".subyes.gif", ims, subrectangles=True)
    s1 = os.stat(fnamebase + ".subno.gif").st_size
    s2 = os.stat(fnamebase + ".subyes.gif").st_size
    assert s2 < s1

    # Meta (dummy, because always {})
    imageio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2)
    assert isinstance(imageio.read(fname).get_meta_data(), dict)


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
