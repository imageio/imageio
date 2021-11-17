import pytest
import imageio as iio


def test_format_on_v3_plugin():
    with pytest.raises(RuntimeError):
        iio.config.known_plugins["pillow"].format
