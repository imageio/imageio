import platform
import pytest
import os
import shutil
from pathlib import Path
import contextlib

import imageio as iio
import requests


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


@pytest.fixture
def image_files(test_images, tmp_path):
    """A copy of the test images

    This is intended for tests that write to or modify the test images.
    """
    for item in test_images.iterdir():
        if item.is_file():
            shutil.copy(item, tmp_path / item.name)

    yield tmp_path


@pytest.fixture
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
