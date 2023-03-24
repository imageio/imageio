""" Tests for imageio's freeimage plugin
"""

import os
import shutil
import sys
import platform
import warnings

import fsspec  # type: ignore
import imageio.plugins
import imageio.v3 as iio3
import imageio.v2 as iio
import numpy as np
import pytest
from imageio import core
from imageio.core import IS_PYPY
from pytest import raises
from conftest import deprecated_test


@pytest.fixture(scope="module")
def vendored_lib(request, tmp_path_factory):
    lib_dir = tmp_path_factory.mktemp("freeimage_dir")

    if platform.system() == "Linux":
        lib_extension = ".so"
    elif platform.system() == "Darwin":
        lib_extension = ".dylib"
    elif platform.system() == "Windows":
        lib_extension = ".dll"

    fs = fsspec.filesystem(
        "github",
        org="imageio",
        repo="imageio-binaries",
        username=request.config.getoption("--github-username"),
        token=request.config.getoption("--github-token"),
    )
    fs.get(
        [x for x in fs.ls("freeimage/") if x.endswith(lib_extension)],
        lib_dir.as_posix(),
    )

    yield lib_dir


# TODD: update fixture once we transition into v3
@pytest.fixture(scope="module")
def setup_library(tmp_path_factory, vendored_lib):
    # Checks if freeimage is installed by the system
    from imageio.plugins.freeimage import fi

    use_imageio_binary = not fi.has_lib()

    # During this test, pretend that FI is the default format
    with warnings.catch_warnings(record=True):
        iio.formats.sort("-FI")

    if use_imageio_binary:
        if sys.platform.startswith("win"):
            user_dir_env = "LOCALAPPDATA"
        else:
            user_dir_env = "IMAGEIO_USERDIR"

        # Setup from test_images/freeimage
        ud = tmp_path_factory.mktemp("userdir")
        old_user_dir = os.getenv(user_dir_env, None)
        os.environ[user_dir_env] = str(ud)
        os.makedirs(ud, exist_ok=True)

        add = core.appdata_dir("imageio")
        os.makedirs(add, exist_ok=True)
        shutil.copytree(vendored_lib, os.path.join(add, "freeimage"))
        fi.load_freeimage()
        assert fi.has_lib(), "imageio-binaries' version of libfreeimage was not found"

    yield

    if use_imageio_binary:
        if old_user_dir is not None:
            os.environ[user_dir_env] = old_user_dir
        else:
            del os.environ[user_dir_env]

    # Sort formats back to normal
    with warnings.catch_warnings(record=True):
        iio.formats.sort()


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


def test_get_fi_lib(vendored_lib, tmp_userdir):
    from imageio.plugins._freeimage import get_freeimage_lib

    add = core.appdata_dir("imageio")
    os.makedirs(add, exist_ok=True)
    shutil.copytree(vendored_lib, os.path.join(add, "freeimage"))

    lib = get_freeimage_lib()
    assert os.path.isfile(lib)


@deprecated_test
def test_freeimage_format(setup_library, test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    # Format
    F = iio.formats["PNG-FI"]
    assert F.name == "PNG-FI"

    # Reader
    R = F.get_reader(core.Request(test_images / "chelsea.png", "ri"))
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


def test_freeimage_lib(setup_library):
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


def test_png(setup_library, test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3, 4):
                fname = fnamebase + "%i.%i.%i.png" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                iio.imsave(fname, rim)
                im = iio.imread(fname)
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
                    iio.imsave(fname, rim)
                    im = iio.imread(fname)
                    mul = 255 if isfloat else 1
                    assert_close(rim * mul, im, 0.1)  # lossless
    finally:
        imageio.plugins._freeimage.TEST_NUMPY_NO_STRIDES = False

    # Parameters
    im = iio.imread(test_images / "chelsea.png", ignoregamma=True)
    iio.imsave(fnamebase + ".png", im, interlaced=True)

    # Parameter fail
    raises(
        TypeError,
        iio.imread,
        test_images / "chelsea.png",
        notavalidk=True,
    )
    raises(TypeError, iio.imsave, fnamebase + ".png", im, notavalidk=True)

    # Compression
    iio.imsave(fnamebase + "1.png", im, compression=0)
    iio.imsave(fnamebase + "2.png", im, compression=9)
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s2 < s1
    # Fail
    raises(ValueError, iio.imsave, fnamebase + ".png", im, compression=12)

    # Quantize
    if sys.platform.startswith("darwin"):
        return  # quantization segfaults on my osx VM
    iio.imsave(fnamebase + "1.png", im, quantize=256)
    iio.imsave(fnamebase + "2.png", im, quantize=4)

    im = iio.imread(fnamebase + "2.png")  # touch palette read code
    s1 = os.stat(fnamebase + "1.png").st_size
    s2 = os.stat(fnamebase + "2.png").st_size
    assert s1 > s2
    # Fail
    fname = fnamebase + "1.png"
    raises(ValueError, iio.imsave, fname, im[:, :, :3], quantize=300)
    raises(ValueError, iio.imsave, fname, im[:, :, 0], quantize=100)


def test_png_dtypes(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    # See issue #44

    # Two images, one 0-255, one 0-200
    im1 = np.zeros((100, 100, 3), dtype="uint8")
    im2 = np.zeros((100, 100, 3), dtype="uint8")
    im1[20:80, 20:80, :] = 255
    im2[20:80, 20:80, :] = 200

    fname = fnamebase + ".dtype.png"

    # uint8
    iio.imsave(fname, im1)
    assert_close(im1, iio.imread(fname))
    iio.imsave(fname, im2)
    assert_close(im2, iio.imread(fname))

    # float scaled
    iio.imsave(fname, im1 / 255.0)
    assert_close(im1, iio.imread(fname))
    iio.imsave(fname, im2 / 255.0)
    assert_close(im2, iio.imread(fname))

    # float not scaled
    iio.imsave(fname, im1 * 1.0)
    assert_close(im1, iio.imread(fname))
    iio.imsave(fname, im2 * 1.0)
    assert_close(im1, iio.imread(fname))  # scaled

    # int16
    iio.imsave(fname, im1.astype("int16"))
    assert_close(im1, iio.imread(fname))
    iio.imsave(fname, im2.astype("int16"))
    assert_close(im1, iio.imread(fname))  # scaled


def test_jpg(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3):
                fname = fnamebase + "%i.%i.%i.jpg" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                iio.imsave(fname, rim)
                im = iio.imread(fname)
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 1.1)  # lossy

    # No alpha in JPEG
    raises(Exception, iio.imsave, fname, im4)

    # Parameters
    iio.imsave(fnamebase + ".jpg", im3, progressive=True, optimize=True, baseline=True)

    # Parameter fail
    raises(
        TypeError,
        iio.imread,
        fnamebase + ".jpg",
        notavalidkwarg=True,
        format="JPEG-FI",
    )
    raises(
        TypeError,
        iio.imsave,
        fnamebase + ".jpg",
        im,
        notavalidk=True,
        format="JPEG-FI",
    )

    # Compression
    iio.imsave(fnamebase + "1.jpg", im3, quality=10)
    iio.imsave(fnamebase + "2.jpg", im3, quality=90)
    s1 = os.stat(fnamebase + "1.jpg").st_size
    s2 = os.stat(fnamebase + "2.jpg").st_size
    assert s2 > s1
    raises(ValueError, iio.imsave, fnamebase + ".jpg", im, quality=120)


def test_jpg_more(setup_library, test_images, tmp_path):
    fnamebase = str(tmp_path / "test")

    # Test broken JPEG
    fname = fnamebase + "_broken.jpg"
    open(fname, "wb").write(b"this is not an image")
    raises(Exception, iio.imread, fname)
    #
    img = get_ref_im(3, 0, 0)
    bb = iio.imsave(iio.RETURN_BYTES, img, "JPEG-FI")
    with open(fname, "wb") as f:
        f.write(bb[:400])
        f.write(b" ")
        f.write(bb[400:])
    raises(Exception, iio.imread, fname)

    # Test EXIF stuff
    fname = test_images / "rommel.jpg"
    im = iio.imread(fname)
    assert im.shape[0] > im.shape[1]
    im = iio.imread(fname, exifrotate=False)
    assert im.shape[0] < im.shape[1]
    im = iio.imread(fname, exifrotate=2)  # Rotation in Python
    assert im.shape[0] > im.shape[1]
    # Write the jpg and check that exif data is maintained
    if sys.platform.startswith("darwin"):
        return  # segfaults on my osx VM, why?
    iio.imsave(fnamebase + "rommel.jpg", im)
    im = iio.imread(fname)
    assert im.meta.EXIF_MAIN


def test_bmp(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3, 4):
                fname = fnamebase + "%i.%i.%i.bmp" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                iio.imsave(fname, rim, format="BMP-FI")
                im = iio.imread(fname, format="BMP-FI")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Compression
    iio.imsave(fnamebase + "1.bmp", im3, compression=False, format="BMP-FI")
    iio.imsave(fnamebase + "2.bmp", im3, compression=True, format="BMP-FI")
    s1 = os.stat(fnamebase + "1.bmp").st_size
    s2 = os.stat(fnamebase + "2.bmp").st_size
    assert s1 + s2  # todo: bug in FreeImage? assert s1 < s2

    # Parameter fail
    raises(
        TypeError,
        iio.imread,
        fnamebase + "1.bmp",
        notavalidkwarg=True,
        format="BMP-FI",
    )
    raises(
        TypeError,
        iio.imsave,
        fnamebase + "1.bmp",
        im,
        notavalidk=True,
        format="BMP-FI",
    )


def test_gif(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    # The not-animated gif

    for isfloat in (False, True):
        for crop in (0, 1, 2):
            for colors in (0, 3, 4):
                if colors > 1 and sys.platform.startswith("darwin"):
                    continue  # quantize fails, see also png
                fname = fnamebase + "%i.%i.%i.gif" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                iio.imsave(fname, rim, format="GIF-FI")
                im = iio.imread(fname, format="GIF-FI")
                mul = 255 if isfloat else 1
                if colors in (0, 1):
                    im = im[:, :, 0]
                else:
                    im = im[:, :, :3]
                    rim = rim[:, :, :3]
                assert_close(rim * mul, im, 1.1)  # lossless

    # Parameter fail
    raises(TypeError, iio.imread, fname, notavalidkwarg=True, format="GIF-FI")
    raises(
        TypeError,
        iio.imsave,
        fnamebase + "1.gif",
        im,
        notavalidk=True,
        format="GIF-FI",
    )


@pytest.mark.skipif(
    sys.platform.startswith("darwin"),
    reason="On OSX quantization of freeimage is unstable",
)
def test_animated_gif(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

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
            iio.mimsave(fname, ims1, duration=0.2, format="GIF-FI")
            # Retrieve
            ims2 = iio.mimread(fname, format="GIF-FI")
            ims1 = [x[:, :, :3] for x in ims]  # fresh ref
            ims2 = [x[:, :, :3] for x in ims2]  # discart alpha
            for im1, im2 in zip(ims1, ims2):
                assert_close(im1, im2, 1.1)

    # We can also store grayscale
    fname = fnamebase + ".animated.%i.gif" % 1
    iio.mimsave(fname, [x[:, :, 0] for x in ims], duration=0.2, format="GIF-FI")
    iio.mimsave(fname, [x[:, :, :1] for x in ims], duration=0.2, format="GIF-FI")

    # Irragular duration. You probably want to check this manually (I did)
    duration = [0.1 for i in ims]
    for i in [2, 5, 7]:
        duration[i] = 0.5
    iio.mimsave(
        fnamebase + ".animated_irr.gif", ims, duration=duration, format="GIF-FI"
    )

    # Other parameters
    iio.mimsave(fnamebase + ".animated.loop2.gif", ims, loop=2, fps=20, format="GIF-FI")
    R = iio.read(fnamebase + ".animated.loop2.gif", format="GIF-FI")
    W = iio.save(
        fnamebase + ".animated.palettes100.gif",
        palettesize=100,
        format="GIF-FI",
    )
    assert W._palettesize == 128
    # Fail
    raises(IndexError, R.get_meta_data, -1)
    raises(
        ValueError,
        iio.mimsave,
        fname,
        ims,
        quantizer="foo",
        format="GIF-FI",
    )
    raises(ValueError, iio.mimsave, fname, ims, duration="foo", format="GIF-FI")

    # Add one duplicate image to ims to touch subractangle with not change
    ims.append(ims[-1])

    # Test subrectangles
    iio.mimsave(fnamebase + ".subno.gif", ims, subrectangles=False, format="GIF-FI")
    iio.mimsave(fnamebase + ".subyes.gif", ims, subrectangles=True, format="GIF-FI")
    s1 = os.stat(fnamebase + ".subno.gif").st_size
    s2 = os.stat(fnamebase + ".subyes.gif").st_size
    assert s2 < s1

    # Meta (dummy, because always {}
    assert isinstance(iio.read(fname).get_meta_data(), dict)


def test_ico(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    for isfloat in (False, True):
        for crop in (0,):
            for colors in (1, 3, 4):
                fname = fnamebase + "%i.%i.%i.ico" % (isfloat, crop, colors)
                rim = get_ref_im(colors, crop, isfloat)
                rim = rim[:32, :32]  # ico needs nice size
                iio.imsave(fname, rim, format="ICO-FI")
                im = iio.imread(fname, format="ICO-FI")
                mul = 255 if isfloat else 1
                assert_close(rim * mul, im, 0.1)  # lossless

    # Meta data
    R = iio.read(fnamebase + "0.0.1.ico", format="ICO-FI")
    assert isinstance(R.get_meta_data(0), dict)
    assert isinstance(R.get_meta_data(None), dict)  # But this print warning
    R.close()
    writer = iio.save(fnamebase + "I.ico", format="ICO-FI")
    writer.set_meta_data({})
    writer.close()

    # Parameters. Note that with makealpha, RGBA images are read in incorrectly
    im = iio.imread(fnamebase + "0.0.1.ico", makealpha=True, format="ICO-FI")
    assert im.ndim == 3 and im.shape[-1] == 4

    # Parameter fail
    raises(TypeError, iio.imread, fname, notavalidkwarg=True, format="ICO-FI")
    raises(
        TypeError,
        iio.imsave,
        fnamebase + "1.ico",
        im,
        notavalidk=True,
        format="ICO-FI",
    )


# Skip on Windows xref: https://github.com/imageio/imageio/issues/21
@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows has a known issue with multi-icon files",
)
def test_multi_icon_ico(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    im = get_ref_im(4, 0, 0)[:32, :32]
    ims = [np.repeat(np.repeat(im, i, 1), i, 0) for i in (1, 2)]  # SegF on win
    ims = im, np.column_stack((im, im)), np.row_stack((im, im))  # error on win
    iio.mimsave(fnamebase + "I2.ico", ims, format="ICO-FI")
    ims2 = iio.mimread(fnamebase + "I2.ico", format="ICO-FI")
    for im1, im2 in zip(ims, ims2):
        assert_close(im1, im2, 0.1)


@pytest.mark.skip("MNG seems broken in FreeImage")
def test_mng(setup_library, test_images):
    iio.imread(test_images / "mngexample.mng")


def test_pnm(setup_library, tmp_path):
    fnamebase = str(tmp_path / "test")

    for useAscii in (True, False):
        for crop in (0, 1, 2):
            for colors in (0, 1, 3):
                fname = fnamebase
                fname += "%i.%i.%i.ppm" % (useAscii, crop, colors)
                rim = get_ref_im(colors, crop, isfloat=False)
                iio.imsave(fname, rim, use_ascii=useAscii, format="PPM-FI")
                im = iio.imread(fname, format="PPM-FI")
                assert_close(rim, im, 0.1)  # lossless

                # Parameter fail
                raises(
                    TypeError,
                    iio.imread,
                    fname,
                    notavalidkwarg=True,
                    format="PPM-FI",
                )
                raises(
                    TypeError,
                    iio.imsave,
                    fname,
                    im,
                    notavalidk=True,
                    format="PPM-FI",
                )


def test_gamma_correction(setup_library, test_images):
    fname = test_images / "kodim03.png"

    # Load image three times
    im1 = iio.imread(fname, format="PNG-FI")
    im2 = iio.imread(fname, ignoregamma=True, format="PNG-FI")
    im3 = iio.imread(fname, ignoregamma=False, format="PNG-FI")

    # Default is to ignore gamma
    assert np.all(im1 == im2)

    # Test result depending of application of gamma
    assert im1.mean() == im2.mean()

    # TODO: We have assert im2.mean() == im3.mean()
    # But this is wrong, we want: assert im2.mean() < im3.mean()

    # test_regression_302
    for im in (im1, im2, im3):
        assert im.shape == (512, 768, 3) and im.dtype == "uint8"


def test_improps(test_images):
    props = iio3.improps(test_images / "kodim03.png", plugin="PNG-FI")

    assert props.shape == (512, 768, 3)
    assert props.dtype == np.uint8
    assert props.is_batch is False


def test_exr_write():
    expected = np.full((128, 128, 3), 0.42, dtype=np.float32)
    buffer = iio3.imwrite("<bytes>", expected, extension=".exr")

    actual = iio3.imread(buffer)

    np.allclose(actual, expected)
