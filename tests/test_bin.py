""" Test imageio binary download/removal functionality.
"""
import os
import shutil

import pytest

from imageio.testing import run_tests_if_main
import imageio
import imageio.__main__
from imageio.core import get_remote_file, NeedDownloadError, util


NOINET = os.getenv("IMAGEIO_NO_INTERNET", "").lower() in ("1", "true", "yes")

if os.getenv("APPVEYOR") or os.getenv("TRAVIS_OS_NAME") == "windows":
    pytest.skip("Skip this on the Travis Windows run for now", allow_module_level=True)


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_download_avbin():
    # 1st remove avbin binary
    imageio.__main__.remove_bin(["avbin"])

    # 2nd check if removal worked
    plat = util.get_platform()
    fname = "avbin/" + imageio.plugins.avbin.FNAME_PER_PLATFORM[plat]
    try:
        get_remote_file(fname=fname, auto=False)
    except NeedDownloadError:
        pass
    else:
        raise Exception("NeedDownloadError should have been raised.")

    # 3rd download avbin binary
    imageio.__main__.download_bin(["avbin"])

    # 4th check if download succeeded
    try:
        get_remote_file(fname=fname, auto=False)
    except Exception:
        raise Exception("Binary should have been downloaded.")


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_remove_avbin():
    # 1st download it
    imageio.__main__.download_bin(["avbin"])

    # 2nd Make sure binary is there
    plat = util.get_platform()
    fname = "avbin/" + imageio.plugins.avbin.FNAME_PER_PLATFORM[plat]
    get_remote_file(fname=fname, auto=False)

    # 3rd Remove binary
    imageio.__main__.remove_bin(["avbin"])

    # 4th check if removal worked
    try:
        get_remote_file(fname=fname, auto=False)
    except NeedDownloadError:
        pass
    else:
        raise Exception("NeedDownloadError should have been raised.")

    # 5th download again so that other tests wont fail
    imageio.__main__.download_bin(["avbin"])


@pytest.mark.xfail(NOINET, reason="Internet not allowed")
def test_download_package_dir():
    # test for downloading a binary
    # to the package "resources" directory.
    res_dir = util.resource_package_dir()
    res_avbin = os.path.join(res_dir, "avbin")

    # check if avbin is there and remove it
    # (this should not conflict with any other tests)
    shutil.rmtree(res_avbin, ignore_errors=True)
    msg = "deleting avbin from resources failed!"
    assert not os.path.isdir(res_avbin), msg

    # Download to resources
    imageio.__main__.download_bin(["avbin"], package_dir=True)
    assert os.path.isdir(res_avbin)


run_tests_if_main()
