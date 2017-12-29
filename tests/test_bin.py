""" Test imageio binary download/removal functionality.
"""
import os
import shutil

import pytest

from imageio.testing import run_tests_if_main
import imageio
import imageio.__main__
from imageio.core import get_remote_file, NeedDownloadError, util


NOINET = os.getenv('IMAGEIO_NO_INTERNET', '').lower() in ('1', 'true', 'yes')


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_download_ffmpeg():
    # 1st remove ffmpeg binary
    imageio.__main__.remove_bin(["ffmpeg"])
    
    # 2nd check if removal worked
    plat = util.get_platform()
    fname = 'ffmpeg/' + imageio.plugins.ffmpeg.FNAME_PER_PLATFORM[plat]
    try:
        get_remote_file(fname=fname, auto=False)
    except NeedDownloadError:
        pass
    else:
        raise Exception("NeedDownloadError should have been raised.")
    
    # 3rd download ffmpeg binary
    imageio.__main__.download_bin(["ffmpeg"])
    
    # 4th check if download succeeded
    try:
        get_remote_file(fname=fname, auto=False)
    except Exception:
        raise Exception("Binary should have been downloaded.")


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_remove_ffmpeg():
    # 1st download it
    imageio.__main__.download_bin(["ffmpeg"])

    # 2nd Make sure binary is there
    plat = util.get_platform()
    fname = 'ffmpeg/' + imageio.plugins.ffmpeg.FNAME_PER_PLATFORM[plat]
    get_remote_file(fname=fname, auto=False)

    # 3rd Remove binary
    imageio.__main__.remove_bin(["ffmpeg"])

    # 4th check if removal worked
    try:
        get_remote_file(fname=fname, auto=False)
    except NeedDownloadError:
        pass
    else:
        raise Exception("NeedDownloadError should have been raised.")

    # 5th download again so that other tests wont fail
    imageio.__main__.download_bin(["ffmpeg"])


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_download_package_dir():
    # test for downloading a binary
    # to the package "resources" directory.
    res_dir = util.resource_package_dir()
    res_ffmpeg = os.path.join(res_dir, "ffmpeg")
    
    # check if ffmpeg is there and remove it
    # (this should not conflict with any other tests)
    shutil.rmtree(res_ffmpeg, ignore_errors=True)
    msg = "deleting ffmpeg from resources failed!"
    assert not os.path.isdir(res_ffmpeg), msg
    
    # Download to resources
    imageio.__main__.download_bin(["ffmpeg"], package_dir=True)
    assert os.path.isdir(res_ffmpeg)


run_tests_if_main()
