""" Tests for imageio's pillow plugin
"""

import os
import sys
import io
from zipfile import ZipFile
import numpy as np

from pytest import raises
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import get_remote_file

test_dir = get_test_dir()


def setup_module():
    # Make sure format order is the default
    imageio.formats.sort()


# Create test images LUMINANCE
im0 = np.zeros((42, 32), np.uint8)
im0[:16, :] = 200
im1 = np.zeros((42, 32, 1), np.uint8)
im1[:16, :] = 200
# Create test image RGB
im3 = np.zeros((42, 32, 3), np.uint8)
im3[:16, :, 0] = 250
im3[:, :16, 1] = 200
im3[50:, :16, 2] = 100
# Create test image RGBA
im4 = np.zeros((42, 32, 4), np.uint8)
im4[:16, :, 0] = 250
im4[:, :16, 1] = 200
im4[50:, :16, 2] = 100
im4[:, :, 3] = 255
im4[20:, :, 3] = 120

fnamebase = os.path.join(test_dir, "test")


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


def test_pillow_format():

    # Format - Pillow is the default!
    F = imageio.formats["PNG"]
    assert F.name == "PNG-PIL"

    # Reader
    R = F.get_reader(core.Request("imageio:chelsea.png", "ri"))
    assert len(R) == 1
    assert isinstance(R.get_meta_data(), dict)
    assert isinstance(R.get_meta_data(0), dict)
    assert raises(IndexError, R.get_data, 2)
    assert raises(IndexError, R.get_meta_data, 2)

    # Writer
    W = F.get_writer(core.Request(fnamebase + ".png", "wi"))
    W.append_data(im0)
    W.set_meta_data({"foo": 3})
    assert raises(RuntimeError, W.append_data, im0)


def test_png():

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3, 4):
                fname = fnamebase + "%i.%i.%i.png" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim)
                im = imageio.imread(fname)
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Parameters
    im = imageio.imread("imageio:chelsea.png", ignoregamma=True)
    imageio.imsave(fnamebase + ".png", im, interlaced=True)

    # Parameter fail
    raises(TypeError, imageio.imread, "imageio:chelsea.png", notavalidk=True)
    raises(TypeError, imageio.imsave, fnamebase + ".png", im, notavalidk=True)

    # Compression
    imageio.imsave(fnamebase + "1.png", im, compression=0)
    imageio.imsave(fnamebase + "2.png", im, compression=9)
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s2 < s1
    # Fail
    raises(ValueError, imageio.imsave, fnamebase + ".png", im, compression=12)

    # Quantize
    imageio.imsave(fnamebase + "1.png", im, quantize=256)
    imageio.imsave(fnamebase + "2.png", im, quantize=4)

    im = imageio.imread(fnamebase + "2.png")  # touch palette read code
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s1 > s2
    # Fail
    fname = fnamebase + "1.png"
    raises(ValueError, imageio.imsave, fname, im[:, :, :3], quantize=300)
    raises(ValueError, imageio.imsave, fname, im[:, :, 0], quantize=100)

    # 16b bit images
    im = imageio.imread("imageio:chelsea.png")[:, :, 0]
    imageio.imsave(fnamebase + "1.png", im.astype("uint16") * 2)
    imageio.imsave(fnamebase + "2.png", im)
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s2 < s1
    im2 = imageio.imread(fnamebase + "1.png")
    assert im2.dtype == np.uint16

    # issue #352 - prevent low-luma uint16 truncation to uint8
    arr = np.full((32, 32), 255, dtype=np.uint16)  # values within range of uint8
    preferences_dtypes = [
        [{}, np.uint8],
        [{"prefer_uint8": True}, np.uint8],
        [{"prefer_uint8": False}, np.uint16],
    ]
    for preference, dtype in preferences_dtypes:
        imageio.imwrite(fnamebase + ".png", arr, **preference)
        im = imageio.imread(fnamebase + ".png")
        assert im.dtype == dtype


def test_png_remote():
    # issue #202
    need_internet()
    im = imageio.imread(
        "https://raw.githubusercontent.com/imageio/"
        + "imageio-binaries/master/images/astronaut.png"
    )
    assert im.shape == (512, 512, 3)


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
    img = get_ref_im(3, 0, 0)
    bb = imageio.imsave(imageio.RETURN_BYTES, img, "JPEG-PIL")
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
        z.writestr("x.png", open(get_remote_file("images/chelsea.png"), "rb").read())
        z.writestr("x.jpg", open(get_remote_file("images/rommel.jpg"), "rb").read())

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


def test_write_jpg_to_bytes_io():
    # this is a regression test
    # see: https://github.com/imageio/imageio/issues/687

    image = np.zeros((200, 200), dtype=np.uint8)
    bytes_io = io.BytesIO()
    imageio.imwrite(bytes_io, image, "jpeg")
    bytes_io.seek(0)

    image_from_file = imageio.imread(bytes_io)
    assert np.allclose(image_from_file, image)


if __name__ == "__main__":
    # test_inside_zipfile()
    # test_png()
    # test_animated_gif()
    # test_bmp()
    run_tests_if_main()
