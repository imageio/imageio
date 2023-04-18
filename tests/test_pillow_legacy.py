""" Tests for imageio's pillow plugin
"""

import os
import sys
import io
from zipfile import ZipFile
import numpy as np

import pytest

import imageio
from imageio import core
from conftest import deprecated_test


@deprecated_test
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


@deprecated_test
def test_pillow_format(test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    # Format - Pillow is the default!
    F = imageio.formats["PNG"]
    assert F.name == "PNG-PIL"

    # Reader
    R = F.get_reader(core.Request(test_images / "chelsea.png", "ri"))
    assert len(R) == 1
    assert isinstance(R.get_meta_data(), dict)
    assert isinstance(R.get_meta_data(0), dict)

    with pytest.raises(IndexError):
        R.get_data(2)

    with pytest.raises(IndexError):
        R.get_meta_data(2)

    # Writer
    W = F.get_writer(core.Request(fnamebase + ".png", "wi"))
    W.append_data(im0)
    W.set_meta_data({"foo": 3})
    with pytest.raises(RuntimeError):
        W.append_data(im0)


@deprecated_test
def test_png(test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3, 4):
                fname = fnamebase + "%i.%i.%i.png" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim, format="PNG-PIL")
                im = imageio.imread(fname, format="PNG-PIL")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Parameters
    im = imageio.imread(test_images / "chelsea.png", ignoregamma=True, format="PNG-PIL")
    imageio.imsave(fnamebase + ".png", im, interlaced=True)

    # Parameter fail
    with pytest.raises(TypeError):
        imageio.imread(test_images / "chelsea.png", notavalidk=True, format="PNG-PIL")

    with pytest.raises(TypeError):
        imageio.imsave(fnamebase + ".png", im, notavalidk=True, format="PNG-PIL")

    # Compression
    imageio.imsave(fnamebase + "1.png", im, compression=0, format="PNG-PIL")
    imageio.imsave(fnamebase + "2.png", im, compression=9, format="PNG-PIL")
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s2 < s1
    # Fail
    with pytest.raises(ValueError):
        imageio.imsave(fnamebase + ".png", im, compression=12, format="PNG-PIL")

    # Quantize
    imageio.imsave(fnamebase + "1.png", im, quantize=256, format="PNG-PIL")
    imageio.imsave(fnamebase + "2.png", im, quantize=4, format="PNG-PIL")

    im = imageio.imread(
        fnamebase + "2.png", format="PNG-PIL"
    )  # touch palette read code
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s1 > s2
    # Fail
    fname = fnamebase + "1.png"
    with pytest.raises(ValueError):
        imageio.imsave(fname, im[:, :, :3], quantize=300, format="PNG-PIL")

    with pytest.raises(ValueError):
        imageio.imsave(fname, im[:, :, 0], quantize=100, format="PNG-PIL")

    # 16b bit images
    im = imageio.imread(test_images / "chelsea.png")[:, :, 0]
    imageio.imsave(fnamebase + "1.png", im.astype("uint16") * 2, format="PNG-PIL")
    imageio.imsave(fnamebase + "2.png", im, format="PNG-PIL")
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s2 < s1
    im2 = imageio.imread(fnamebase + "1.png", format="PNG-PIL")
    assert im2.dtype == np.uint16

    # issue #352 - prevent low-luma uint16 truncation to uint8
    arr = np.full((32, 32), 255, dtype=np.uint16)  # values within range of uint8
    preferences_dtypes = [
        [{}, np.uint8],
        [{"prefer_uint8": True}, np.uint8],
        [{"prefer_uint8": False}, np.uint16],
    ]
    for preference, dtype in preferences_dtypes:
        imageio.imwrite(fnamebase + ".png", arr, **preference, format="PNG-PIL")
        im = imageio.imread(fnamebase + ".png", format="PNG-PIL")
        assert im.dtype == dtype


@pytest.mark.needs_internet
@deprecated_test
def test_png_remote():
    # issue #202
    im = imageio.imread(
        "https://raw.githubusercontent.com/imageio/test_images/main/astronaut.png"
    )
    assert im.shape == (512, 512, 3)


@deprecated_test
def test_jpg(tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3):
                fname = fnamebase + "%i.%i.%i.jpg" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim, format="JPEG-PIL")
                im = imageio.imread(fname, format="JPEG-PIL")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 1.1)  # lossy

    # No alpha in JPEG
    fname = fnamebase + ".jpg"
    with pytest.raises(Exception):
        imageio.imsave(fname, im4, format="JPEG-PIL")

    # Parameters
    imageio.imsave(
        fnamebase + ".jpg",
        im3,
        progressive=True,
        optimize=True,
        baseline=True,
        format="JPEG-PIL",
    )

    # Parameter fail - We let Pillow kwargs thorugh
    # pytest.raises(TypeError, imageio.imread, fnamebase + '.jpg', notavalidkwarg=1)
    # pytest.raises(TypeError, imageio.imsave, fnamebase + '.jpg', im, notavalidk=1)

    # Compression
    imageio.imsave(fnamebase + "1.jpg", im3, quality=10, format="JPEG-PIL")
    imageio.imsave(fnamebase + "2.jpg", im3, quality=90, format="JPEG-PIL")
    s1 = os.stat(fnamebase + "1.jpg").st_size
    s2 = os.stat(fnamebase + "2.jpg").st_size
    assert s2 > s1
    with pytest.raises(ValueError):
        imageio.imsave(fnamebase + ".jpg", im, quality=120, format="JPEG-PIL")


@deprecated_test
def test_jpg_more(test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    # Test broken JPEG
    fname = fnamebase + "_broken.jpg"
    open(fname, "wb").write(b"this is not an image")
    with pytest.raises(Exception):
        imageio.imread(fname)
    #
    img = get_ref_im(3, 0, 0)
    bb = imageio.imsave(imageio.RETURN_BYTES, img, "JPEG-PIL")
    with open(fname, "wb") as f:
        f.write(bb[:400])
        f.write(b" ")
        f.write(bb[400:])
    with pytest.raises(Exception):
        imageio.imread(fname, format="JPEG-PIL")

    # Test EXIF stuff
    fname = test_images / "rommel.jpg"
    im = imageio.imread(fname, format="JPEG-PIL")
    assert im.shape[0] > im.shape[1]
    im = imageio.imread(fname, exifrotate=False, format="JPEG-PIL")
    assert im.shape[0] < im.shape[1]
    im = imageio.imread(fname, exifrotate=2, format="JPEG-PIL")  # Rotation in Python
    assert im.shape[0] > im.shape[1]
    # Write the jpg and check that exif data is maintained
    if sys.platform.startswith("darwin"):
        return  # segfaults on my osx VM, why?
    imageio.imsave(fnamebase + "rommel.jpg", im, format="JPEG-PIL")
    im = imageio.imread(fname, format="JPEG-PIL")
    assert im.meta.EXIF_MAIN


@deprecated_test
def test_gif(tmp_path):
    fnamebase = str(tmp_path / "test")

    # The not-animated gif

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 3, 4):
                if colors > 1 and sys.platform.startswith("darwin"):
                    continue  # quantize fails, see also png
                fname = fnamebase + "%i.%i.%i.gif" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                imageio.imsave(fname, rim, format="GIF-PIL")
                im = imageio.imread(fname, format="GIF-PIL")
                mul = 255 if isfloat else 1
                if colors not in (0, 1):
                    im = im[:, :, :3]
                    rim = rim[:, :, :3]
                assert_close(rim * mul, im, 1.1)  # lossless

    # Parameter fail
    with pytest.raises(TypeError):
        imageio.imread(fname, notavalidkwarg=True, format="GIF-PIL")

    with pytest.raises(TypeError):
        imageio.imsave(fnamebase + "1.gif", im, notavalidk=True, format="GIF-PIL")


@deprecated_test
def test_animated_gif(test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    # Read newton's cradle
    ims = imageio.mimread(test_images / "newtonscradle.gif", format="GIF-PIL")
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
            imageio.mimsave(fname, ims1, duration=0.2, format="GIF-PIL")
            # Retrieve
            print("fooo", fname, isfloat, colors)
            ims2 = imageio.mimread(fname, format="GIF-PIL")
            ims1 = [x[:, :, :3] for x in ims]  # fresh ref
            ims2 = [x[:, :, :3] for x in ims2]  # discart alpha
            for im1, im2 in zip(ims1, ims2):
                assert_close(im1, im2, 1.1)

    # We can also store grayscale
    fname = fnamebase + ".animated.%i.gif" % 1
    imageio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2, format="GIF-PIL")
    imageio.mimsave(fname, [x[:, :, :1] for x in ims], duration=0.2, format="GIF-PIL")

    # Irragular duration. You probably want to check this manually (I did)
    duration = [0.1 for i in ims]
    for i in [2, 5, 7]:
        duration[i] = 0.5
    imageio.mimsave(
        fnamebase + ".animated_irr.gif", ims, duration=duration, format="GIF-PIL"
    )

    # Other parameters
    imageio.mimsave(
        fnamebase + ".animated.loop2.gif", ims, loop=2, fps=20, format="GIF-PIL"
    )
    R = imageio.read(fnamebase + ".animated.loop2.gif", format="GIF-PIL")
    W = imageio.save(
        fnamebase + ".animated.palettes100.gif", palettesize=100, format="GIF-PIL"
    )
    assert W._writer.opt_palette_size == 128
    # Fail
    with pytest.raises(IndexError):
        R.get_meta_data(-1)

    with pytest.raises(ValueError):
        imageio.mimsave(fname, ims, palettesize=300, format="GIF-PIL")

    with pytest.raises(ValueError):
        imageio.mimsave(fname, ims, quantizer="foo", format="GIF-PIL")

    with pytest.raises(ValueError):
        imageio.mimsave(fname, ims, duration="foo", format="GIF-PIL")

    # Add one duplicate image to ims to touch subractangle with not change
    ims.append(ims[-1])

    # Test subrectangles
    imageio.mimsave(
        fnamebase + ".subno.gif", ims, subrectangles=False, format="GIF-PIL"
    )
    imageio.mimsave(
        fnamebase + ".subyes.gif", ims, subrectangles=True, format="GIF-PIL"
    )
    s1 = os.stat(fnamebase + ".subno.gif").st_size
    s2 = os.stat(fnamebase + ".subyes.gif").st_size
    assert s2 < s1

    # Meta (dummy, because always {})
    imageio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2, format="GIF-PIL")
    assert isinstance(imageio.read(fname).get_meta_data(), dict)


def test_v3_gif(test_images):
    img = imageio.v3.imread(
        test_images / "newtonscradle.gif", plugin="GIF-PIL", index=None
    )
    assert img.shape == (36, 150, 200, 4)


@deprecated_test
def test_images_with_transparency(test_images):
    # Not alpha channel, but transparent pixels, see issue #245 and #246

    fname = test_images / "imageio_issue245.gif"
    im = imageio.imread(fname, format="GIF-PIL")
    assert im.shape == (24, 30, 4)

    fname = test_images / "imageio_issue246.png"
    im = imageio.imread(fname, format="PNG-PIL")
    assert im.shape == (24, 30, 4)


@deprecated_test
def test_gamma_correction(test_images):
    fname = test_images / "kodim03.png"

    # Load image three times
    im1 = imageio.imread(fname, format="PNG-PIL")
    im2 = imageio.imread(fname, ignoregamma=True, format="PNG-PIL")
    im3 = imageio.imread(fname, ignoregamma=False, format="PNG-PIL")

    # Default is to ignore gamma
    assert np.all(im1 == im2)

    # Test result depending of application of gamma
    assert im1.meta["gamma"] < 1
    assert im1.mean() == im2.mean()
    assert im2.mean() < im3.mean()

    # test_regression_302
    for im in (im1, im2, im3):
        assert im.shape == (512, 768, 3) and im.dtype == "uint8"


@deprecated_test
def test_inside_zipfile(test_images, tmp_path):
    fname = str(tmp_path / "pillowtest.zip")
    with ZipFile(fname, "w") as z:
        z.writestr(
            "x.png",
            (test_images / "chelsea.png").read_bytes(),
        )
        z.writestr(
            "x.jpg",
            (test_images / "rommel.jpg").read_bytes(),
        )

    for name in ("x.png", "x.jpg"):
        imageio.imread(fname + "/" + name)


@deprecated_test
def test_bmp(test_images):
    fname = test_images / "scribble_P_RGB.bmp"

    imageio.imread(fname)
    imageio.imread(fname, pilmode="RGB", format="BMP-PIL")
    imageio.imread(fname, pilmode="RGBA", format="BMP-PIL")


@deprecated_test
def test_scipy_imread_compat(test_images):
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.imread.html
    # https://github.com/scipy/scipy/blob/41a3e69ca3141d8bf996bccb5eca5fc7bbc21a51/scipy/misc/pilutil.py#L111

    fname = test_images / "chelsea.png"

    im = imageio.imread(fname)
    assert im.shape == (300, 451, 3) and im.dtype == "uint8"

    # Scipy users may default to using "mode", but our getreader() already has
    # a "mode" argument, so they should use pilmode instead.
    try:
        im = imageio.imread(fname, mode="L")
    except TypeError as err:
        assert "pilmode" in str(err)

    im = imageio.imread(fname, pilmode="RGBA", format="PNG-PIL")
    assert im.shape == (300, 451, 4) and im.dtype == "uint8"

    im = imageio.imread(fname, pilmode="L", format="PNG-PIL")
    assert im.shape == (300, 451) and im.dtype == "uint8"

    im = imageio.imread(fname, pilmode="F", format="PNG-PIL")
    assert im.shape == (300, 451) and im.dtype == "float32"

    im = imageio.imread(fname, as_gray=True, format="PNG-PIL")
    assert im.shape == (300, 451) and im.dtype == "float32"

    # Force using pillow (but really, Pillow's imageio's first choice! Except
    # for tiff)
    im = imageio.imread(fname, "PNG-PIL")


@deprecated_test
def test_write_jpg_to_bytes_io():
    # this is a regression test
    # see: https://github.com/imageio/imageio/issues/687

    image = np.zeros((200, 200), dtype=np.uint8)
    bytes_io = io.BytesIO()
    imageio.imwrite(bytes_io, image, "jpeg")
    bytes_io.seek(0)

    image_from_file = imageio.imread(bytes_io)
    assert np.allclose(image_from_file, image)
