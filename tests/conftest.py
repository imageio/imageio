import os
import stat
import shutil
from pathlib import Path
import contextlib
import subprocess
import contextlib

import pytest

import imageio as iio


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "needs_internet: Marks a test that requires an active interent connection."
        " (deselect with '-m \"not needs_internet\"').",
    )


def pytest_addoption(parser):
    parser.addoption(
        "--imageio-binaries",
        action="store",
        metavar="GIT_REPO",
        default="https://github.com/imageio/imageio-binaries.git",
        help="Repository to use for checking out binary data used at tests"
        " (default: %(default)s).  Use 'file:///path/to/imageio-binaries'"
        " to clone from a local repository and save testing bandwidth.",
    )


@contextlib.contextmanager
def working_directory(path):
    """
    A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.
    Usage:
    > # Do something in original directory
    > with working_directory('/my/new/path'):
    >     # Do something in new directory
    > # Back to old directory

    Credit goes to @anjos .
    """

    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture(scope="session")
def test_images(request):
    """A collection of test images.

    Note: The images are cached persistently (across test runs) in
    the project's root folder (at `project_root/.test_images`).

    """
    # A temporary directory loaded with the test image files
    # downloaded once in the beginning

    checkout_dir = request.config.cache.get("imageio_test_binaries", None)

    if checkout_dir is not None and not Path(checkout_dir).exists():
        # cache value set, but cache is gone :( ... recreate
        checkout_dir = None

    if checkout_dir is None:
        # download test images and other binaries
        checkout_dir = Path(__file__).parents[1] / ".test_images"

        try:
            checkout_dir.mkdir()
        except FileExistsError:
            pass  # dir exist, validate and fail later
        else:
            with working_directory(checkout_dir):
                os.system("git clone https://github.com/imageio/test_images.git .")

        request.config.cache.set("imageio_test_binaries", str(checkout_dir))

    checkout_dir = Path(checkout_dir)

    with working_directory(checkout_dir):
        result = os.system("git pull")

    if result != 0:
        request.config.cache.set("imageio_test_binaries", None)
        raise RuntimeError(
            "Cache directory is corrupt. Delete `.test_images` at project root."
        )

    return checkout_dir


@pytest.fixture()
def image_files(test_images, tmp_path):
    """A copy of the test images

    This is intended for tests that write to or modify the test images.
    """
    for item in test_images.iterdir():
        if item.is_file():
            shutil.copy(item, tmp_path / item.name)

    yield tmp_path


def pytest_collection_modifyitems(items):

    # all tests using the image_cache fixture, require internet automatically
    # iff they checkout from the remote repository - everything else does not
    internet_protocols = ("git", "http", "ssh")
    for item in items:
        if ("image_cache" in getattr(item, "fixturenames", ())) or (
            "image_copy" in getattr(item, "fixturenames", ())
        ):
            if item.config.getoption("imageio_binaries").startswith(internet_protocols):
                item.add_marker("needs_internet")


@pytest.fixture()
def clear_plugins():

    old_extensions = iio.config.known_extensions.copy()
    old_plugins = iio.config.known_plugins.copy()

    iio.config.known_extensions.clear()
    iio.config.known_plugins.clear()

    yield

    iio.config.known_extensions.clear()
    iio.config.known_plugins.clear()

    iio.config.known_plugins.update(old_plugins)
    iio.config.known_extensions.update(old_extensions)


@pytest.fixture()
def invalid_file(tmp_path, request):
    ext = request.param
    with open(tmp_path / ("foo" + ext), "w") as file:
        file.write("Actually not a file.")

    return tmp_path / ("foo" + ext)


@pytest.fixture()
def tmp_userdir(tmp_path):

    ud = tmp_path / "userdir"
    os.makedirs(ud, exist_ok=True)
    os.environ["IMAGEIO_USERDIR"] = str(ud)

    yield ud

    del os.environ["IMAGEIO_USERDIR"]
    shutil.rmtree(ud)
