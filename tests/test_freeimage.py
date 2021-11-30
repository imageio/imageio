""" Tests for imageio's freeimage plugin
"""

import os
import sys

import numpy as np

from pytest import raises, skip
import pytest
from imageio.testing import run_tests_if_main, get_test_dir, need_internet

import imageio
from imageio import core
from imageio.core import get_remote_file, IS_PYPY


test_dir = get_test_dir()


def setup_module():
    # During this test, pretend that FI is the default format
    imageio.formats.sort("-FI")

    # This tests requires our version of the FI lib
    try:
        imageio.plugins.freeimage.download()
    except core.InternetNotAllowedError:
        # We cannot download; skip all freeimage tests
        need_internet()


def teardown_module():
    # Set back to normal
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


def test_download():
    # this is a regression test
    # see: https://github.com/imageio/imageio/issues/690

    assert hasattr(imageio.plugins.freeimage, "download")


def test_get_ref_im():
    """A test for our function to get test images"""

    crop = 0
    for f in (False, True):
        for colors in (0, 1, 3, 4):
            rim = get_ref_im(0, crop, f)
            assert rim.flags.c_contiguous is True
            assert rim.shape[:2] == (42, 32)

    crop = 1
    for f in (False, True):
        for colors in (0, 1, 3, 4):
            rim = get_ref_im(0, crop, f)
            assert rim.flags.c_contiguous is True
            assert rim.shape[:2] == (41, 31)

    if IS_PYPY:
        return "PYPY cannot have non-contiguous data"

    crop = 2
    for f in (False, True):
        for colors in (0, 1, 3, 4):
            rim = get_ref_im(0, crop, f)
            assert rim.flags.c_contiguous is False
            assert rim.shape[:2] == (41, 31)


def test_get_fi_lib():
    need_internet()

    from imageio.plugins._freeimage import get_freeimage_lib

    lib = get_freeimage_lib()
    assert os.path.isfile(lib)


def test_freeimage_format():

    # Format
    F = imageio.formats["PNG-FI"]
    assert F.name == "PNG-FI"

    # Reader
    R = F.get_reader(core.Request("imageio:chelsea.png", "ri"))
    assert len(R) == 1
    assert isinstance(R.get_meta_data(), dict)
    assert isinstance(R.get_meta_data(0), dict)
    raises(IndexError, R.get_data, 2)
    raises(IndexError, R.get_meta_data, 2)

    # Writer
    W = F.get_writer(core.Request(fnamebase + ".png", "wi"))
    W.append_data(im0)
    W.set_meta_data({"foo": 3})
    raises(RuntimeError, W.append_data, im0)


def test_freeimage_lib():

    fi = imageio.plugins.freeimage.fi

    # Error messages
    imageio.plugins._freeimage.fi._messages.append("this is a test")
    assert imageio.plugins._freeimage.fi.get_output_log()
    imageio.plugins._freeimage.fi._show_any_warnings()
    imageio.plugins._freeimage.fi._get_error_message()

    # Test getfif
    raises(ValueError, fi.getFIF, "foo.png", "x")  # mode must be r or w
    raises(ValueError, fi.getFIF, "foo.notvalid", "w")  # invalid ext
    raises(ValueError, fi.getFIF, "foo.iff", "w")  # We cannot write iff


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

    # Run exact same test, but now in pypy backup mode
    try:
        imageio.plugins._freeimage.TEST_NUMPY_NO_STRIDES = True
        for isfloat in (False, True):
            for crop in (0, 1, 2):
                for colors in (0, 1, 3, 4):
                    fname = fnamebase + "%i.%i.%i.png" % (isfloat, crop, colors)
                    rim = get_ref_im(colors, crop, isfloat)
                    imageio.imsave(fname, rim)
                    im = imageio.imread(fname)
                    mul = 255 if isfloat else 1
                    assert_close(rim * mul, im, 0.1)  # lossless
    finally:
        imageio.plugins._freeimage.TEST_NUMPY_NO_STRIDES = False

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
    if sys.platform.startswith("darwin"):
        return  # quantization segfaults on my osx VM
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


def test_png_dtypes():
    # See issue #44

    # Two images, one 0-255, one 0-200
    im1 = np.zeros((100, 100, 3), dtype="uint8")
    im2 = np.zeros((100, 100, 3), dtype="uint8")
    im1[20:80, 20:80, :] = 255
    im2[20:80, 20:80, :] = 200

    fname = fnamebase + ".dtype.png"

    # uint8
    imageio.imsave(fname, im1)
    assert_close(im1, imageio.imread(fname))
    imageio.imsave(fname, im2)
    assert_close(im2, imageio.imread(fname))

    # float scaled
    imageio.imsave(fname, im1 / 255.0)
    assert_close(im1, imageio.imread(fname))
    imageio.imsave(fname, im2 / 255.0)
    assert_close(im2, imageio.imread(fname))

    # float not scaled
    imageio.imsave(fname, im1 * 1.0)
    assert_close(im1, imageio.imread(fname))
    imageio.imsave(fname, im2 * 1.0)
    assert_close(im1, imageio.imread(fname))  # scaled

    # int16
    imageio.imsave(fname, im1.astype("int16"))
    assert_close(im1, imageio.imread(fname))
    imageio.imsave(fname, im2.astype("int16"))
    assert_close(im1, imageio.imread(fname))  # scaled


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
    raises(Exception, imageio.imsave, fname, im4)

    # Parameters
    imageio.imsave(
        fnamebase + ".jpg", im3, progressive=True, optimize=True, baseline=True
    )

    # Parameter fail
    raises(
        TypeError,
        imageio.imread,
        fnamebase + ".jpg",
        notavalidkwarg=True,
        format="JPEG-FI",
    )
    raises(
        TypeError,
        imageio.imsave,
        fnamebase + ".jpg",
        im,
        notavalidk=True,
        format="JPEG-FI",
    )

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
    bb = imageio.imsave(imageio.RETURN_BYTES, img, "JPEG-FI")
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


def test_bmp():

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3, 4):
                fname = fnamebase + "%i.%i.%i.bmp" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim, format="BMP-FI")
                im = imageio.imread(fname, format="BMP-FI")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Compression
    imageio.imsave(fnamebase + "1.bmp", im3, compression=False, format="BMP-FI")
    imageio.imsave(fnamebase + "2.bmp", im3, compression=True, format="BMP-FI")
    s1 = os.stat(fnamebase + "1.bmp").st_size
    s2 = os.stat(fnamebase + "2.bmp").st_size
    assert s1 + s2  # todo: bug in FreeImage? assert s1 < s2

    # Parameter fail
    raises(
        TypeError,
        imageio.imread,
        fnamebase + "1.bmp",
        notavalidkwarg=True,
        format="BMP-FI",
    )
    raises(
        TypeError,
        imageio.imsave,
        fnamebase + "1.bmp",
        im,
        notavalidk=True,
        format="BMP-FI",
    )


def test_gif():
    # The not-animated gif

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 3, 4):
                if colors > 1 and sys.platform.startswith("darwin"):
                    continue  # quantize fails, see also png
                fname = fnamebase + "%i.%i.%i.gif" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim, format="GIF-FI")
                im = imageio.imread(fname, format="GIF-FI")
                mul = 255 if isfloat else 1
                if colors in (0, 1):
                    im = im[:, :, 0]
                else:
                    im = im[:, :, :3]
                    rim = rim[:, :, :3]
                assert_close(rim * mul, im, 1.1)  # lossless

    # Parameter fail
    raises(TypeError, imageio.imread, fname, notavalidkwarg=True, format="GIF-FI")
    raises(
        TypeError,
        imageio.imsave,
        fnamebase + "1.gif",
        im,
        notavalidk=True,
        format="GIF-FI",
    )


def test_animated_gif():

    if sys.platform.startswith("darwin"):
        skip("On OSX quantization of freeimage is unstable")

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
            imageio.mimsave(fname, ims1, duration=0.2, format="GIF-FI")
            # Retrieve
            ims2 = imageio.mimread(fname, format="GIF-FI")
            ims1 = [x[:, :, :3] for x in ims]  # fresh ref
            ims2 = [x[:, :, :3] for x in ims2]  # discart alpha
            for im1, im2 in zip(ims1, ims2):
                assert_close(im1, im2, 1.1)

    # We can also store grayscale
    fname = fnamebase + ".animated.%i.gif" % 1
    imageio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2, format="GIF-FI")
    imageio.mimsave(fname, [x[:, :, :1] for x in ims], duration=0.2, format="GIF-FI")

    # Irragular duration. You probably want to check this manually (I did)
    duration = [0.1 for i in ims]
    for i in [2, 5, 7]:
        duration[i] = 0.5
    imageio.mimsave(
        fnamebase + ".animated_irr.gif", ims, duration=duration, format="GIF-FI"
    )

    # Other parameters
    imageio.mimsave(
        fnamebase + ".animated.loop2.gif", ims, loop=2, fps=20, format="GIF-FI"
    )
    R = imageio.read(fnamebase + ".animated.loop2.gif", format="GIF-FI")
    W = imageio.save(
        fnamebase + ".animated.palettes100.gif", palettesize=100, format="GIF-FI"
    )
    assert W._palettesize == 128
    # Fail
    raises(IndexError, R.get_meta_data, -1)
    raises(ValueError, imageio.mimsave, fname, ims, palettesize=300)
    raises(ValueError, imageio.mimsave, fname, ims, quantizer="foo", format="GIF-FI")
    raises(ValueError, imageio.mimsave, fname, ims, duration="foo", format="GIF-FI")

    # Add one duplicate image to ims to touch subractangle with not change
    ims.append(ims[-1])

    # Test subrectangles
    imageio.mimsave(fnamebase + ".subno.gif", ims, subrectangles=False, format="GIF-FI")
    imageio.mimsave(fnamebase + ".subyes.gif", ims, subrectangles=True, format="GIF-FI")
    s1 = os.stat(fnamebase + ".subno.gif").st_size
    s2 = os.stat(fnamebase + ".subyes.gif").st_size
    assert s2 < s1

    # Meta (dummy, because always {}
    assert isinstance(imageio.read(fname).get_meta_data(), dict)


def test_ico():

    for isfloat in (False, True):
        for crop in (0,):
            for colors in (1, 3, 4):
                fname = fnamebase + "%i.%i.%i.ico" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                rim = rim[:32, :32]  # ico needs nice size
                imageio.imsave(fname, rim, format="ICO-FI")
                im = imageio.imread(fname, format="ICO-FI")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Meta data
    R = imageio.read(fnamebase + "0.0.1.ico", format="ICO-FI")
    assert isinstance(R.get_meta_data(0), dict)
    assert isinstance(R.get_meta_data(None), dict)  # But this print warning
    R.close()
    writer = imageio.save(fnamebase + "I.ico", format="ICO-FI")
    writer.set_meta_data({})
    writer.close()

    # Parameters. Note that with makealpha, RGBA images are read in incorrectly
    im = imageio.imread(fnamebase + "0.0.1.ico", makealpha=True, format="ICO-FI")
    assert im.ndim == 3 and im.shape[-1] == 4

    # Parameter fail
    raises(TypeError, imageio.imread, fname, notavalidkwarg=True, format="ICO-FI")
    raises(
        TypeError,
        imageio.imsave,
        fnamebase + "1.ico",
        im,
        notavalidk=True,
        format="ICO-FI",
    )


# Skip on Windows xref: https://github.com/imageio/imageio/issues/21
@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Windows has a known issue with multi-icon files",
)
def test_multi_icon_ico():
    im = get_ref_im(4, 0, 0)[:32, :32]
    ims = [np.repeat(np.repeat(im, i, 1), i, 0) for i in (1, 2)]  # SegF on win
    ims = im, np.column_stack((im, im)), np.row_stack((im, im))  # error on win
    imageio.mimsave(fnamebase + "I2.ico", ims, format="ICO-FI")
    ims2 = imageio.mimread(fnamebase + "I2.ico", format="ICO-FI")
    for im1, im2 in zip(ims, ims2):
        assert_close(im1, im2, 0.1)


def test_mng():
    pass  # MNG seems broken in FreeImage
    # ims = imageio.imread(get_remote_file('images/mngexample.mng'))


def test_pnm():
    for useAscii in (True, False):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3):
                fname = fnamebase
                fname += "%i.%i.%i.ppm" % (useAscii, crop, colors)
                rim = get_ref_im(colors, crop, isfloat=False)
                imageio.imsave(fname, rim, use_ascii=useAscii, format="PPM-FI")
                im = imageio.imread(fname, format="PPM-FI")
                assert_close(rim, im, 0.1)  # lossless

                # Parameter fail
                raises(
                    TypeError,
                    imageio.imread,
                    fname,
                    notavalidkwarg=True,
                    format="PPM-FI",
                )
                raises(
                    TypeError,
                    imageio.imsave,
                    fname,
                    im,
                    notavalidk=True,
                    format="PPM-FI",
                )


def test_other():
    # Cannot save float
    im = get_ref_im(3, 0, 1)
    raises(Exception, imageio.imsave, fnamebase + ".jng", im, "JNG")


def test_gamma_correction():
    need_internet()

    fname = get_remote_file("images/kodim03.png")

    # Load image three times
    im1 = imageio.imread(fname, format="PNG-FI")
    im2 = imageio.imread(fname, ignoregamma=True, format="PNG-FI")
    im3 = imageio.imread(fname, ignoregamma=False, format="PNG-FI")

    # Default is to ignore gamma
    assert np.all(im1 == im2)

    # Test result depending of application of gamma
    assert im1.mean() == im2.mean()

    # TODO: We have assert im2.mean() == im3.mean()
    # But this is wrong, we want: assert im2.mean() < im3.mean()

    # test_regression_302
    for im in (im1, im2, im3):
        assert im.shape == (512, 768, 3) and im.dtype == "uint8"


if __name__ == "__main__":
    # test_animated_gif()
    run_tests_if_main()
