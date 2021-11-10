import pytest
import os
import shutil
import subprocess

import imageio as iio


@pytest.fixture(scope="session")
def tmp_dir(tmp_path_factory):
    # A temporary directory loaded with the test image files
    # downloaded once in the beginning
    tmp_path = tmp_path_factory.getbasetemp() / "image_cache"
    tmp_path.mkdir()

    # download the (only) test images via git's sparse-checkout
    current_path = os.getcwd()
    os.chdir(tmp_path)
    git_version = subprocess.run(
        ["git", "--version"], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")[12:18]
    major, minor, _ = git_version.split(".")

    if int(major) == 2 and int(minor) < 30:
        # --sparse was introduced in git 2.30.0 (I think)
        os.system(
            "git clone --depth 1 --filter=blob:none --no-checkout https://github.com/imageio/imageio-binaries.git ."
        )
        os.system("git sparse-checkout init --cone")
        os.system("git sparse-checkout set test-images")
    else:
        # sparse checkout on GH Actions
        os.system(
            "git clone --sparse --filter=blob:none https://github.com/imageio/imageio-binaries.git ."
        )
        os.system("git sparse-checkout init --cone")
        os.system("git sparse-checkout set test-images")
    os.chdir(current_path)

    return tmp_path_factory.getbasetemp()


@pytest.fixture
def image_files(tmp_dir):
    # create a copy of the test images for the actual tests
    # not avoid interaction between tests
    image_dir = tmp_dir / "image_cache" / "test-images"
    data_dir = tmp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    for item in image_dir.iterdir():
        if item.is_file():
            shutil.copy(item, data_dir / item.name)

    yield data_dir

    shutil.rmtree(data_dir)


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
