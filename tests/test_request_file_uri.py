import imageio.v2 as iio2
import imageio.v3 as iio3
import numpy as np
import pytest
from PIL import Image


@pytest.mark.parametrize(
    "name", ["plain.png", "has space.png", "100%.png", "日本語.png", "plus+hash#.png"]
)
@pytest.mark.parametrize("api", [iio2, iio3])
def test_local_file_uri_read(tmp_path, name, api):
    expected = np.arange(3 * 5 * 3, dtype=np.uint8).reshape(3, 5, 3)
    path = tmp_path / name
    Image.fromarray(expected).save(path)
    actual = api.imread(path.as_uri())
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual, api.imread(path))


@pytest.mark.parametrize(
    "name", ["plain.png", "has space.png", "100%.png", "日本語.png", "plus+hash#.png"]
)
@pytest.mark.parametrize("api", [iio2, iio3])
def test_local_file_uri_write(tmp_path, name, api):
    expected = np.arange(3 * 5 * 3, dtype=np.uint8).reshape(3, 5, 3)
    path = tmp_path / name
    api.imwrite(path.as_uri(), expected)
    assert path.exists()
    np.testing.assert_array_equal(np.asarray(Image.open(path)), expected)
