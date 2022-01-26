import platform
import pytest
import os
import shutil

import imageio as iio
import requests


@pytest.fixture(scope="session")
def tmp_dir(tmp_path_factory):
    # A temporary directory loaded with the test image files
    # downloaded once in the beginning
    tmp_path = tmp_path_factory.getbasetemp() / "image_cache"
    tmp_path.mkdir()

    # Get list of images. authenticate with our GH token so that the rate limit is per-repo
    # see: https://docs.github.com/en/rest/reference/repos#contents
    api_endpoint = "https://api.github.com/repos/imageio/imageio-binaries"
    token = os.getenv("GITHUB_TOKEN")
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    r = requests.get(api_endpoint + "/contents/test-images", headers=headers)
    r.raise_for_status()
    image_info_dicts = r.json()
    if platform.system() == "Darwin":
        print("!!!! DEBUG !!!")
        print(image_info_dicts)
        print("!!!! DEBUG !!!")

    # Download the images
    downloader = requests.Session()
    for image_info in image_info_dicts:
        if not isinstance(image_info, dict):
            print(image_info)
            print("!!!!!!!!!!!!!!!!!!!!!!!")
            continue

        response = downloader.get(image_info["download_url"])
        response.raise_for_status()
        (tmp_path / image_info["name"]).write_bytes(response.content)

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
