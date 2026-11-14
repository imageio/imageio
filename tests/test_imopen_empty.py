"""Empty local files should fail before automatic plugin selection."""

import os
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest

import imageio.v2 as iio2
import imageio.v3 as iio3
from imageio.config import FileExtension, known_extensions, known_plugins
from imageio.config.plugins import PluginConfig
from imageio.core import Request
from imageio.core.request import InitializationError
from imageio.core.v3_plugin_api import PluginV3


@pytest.mark.parametrize("legacy_mode, error", [(False, OSError), (True, ValueError)])
@pytest.mark.parametrize(
    "options", [{}, {"extension": ".png"}, {"format_hint": ".png"}]
)
def test_empty_file_skips_plugins(tmp_path, monkeypatch, legacy_mode, error, options):
    path = tmp_path / "empty.png"
    path.touch()
    calls = []

    def reject(request, **kwargs):
        calls.append(request)
        raise InitializationError("Not an image")

    monkeypatch.setattr(PluginConfig, "plugin_class", property(lambda self: reject))
    with pytest.raises(error) as exc_info:
        iio3.imopen(path, "r", legacy_mode=legacy_mode, **options)
    assert calls == []
    assert "is empty" in str(exc_info.value).lower()
    assert str(path) in str(exc_info.value)


@pytest.mark.parametrize("api, error", [(iio2, ValueError), (iio3, OSError)])
@pytest.mark.parametrize("uri_kind", ["path", "string", "relative", "file_uri", "home"])
def test_empty_file_paths(tmp_path, monkeypatch, api, error, uri_kind):
    path = tmp_path / "zero.png"
    path.touch()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    uri = {
        "path": path,
        "string": str(path),
        "relative": "./zero.png",
        "file_uri": "file://" + str(path),
        "home": "~/zero.png",
    }[uri_kind]
    with pytest.raises(error, match="is empty"):
        api.imread(uri)


@pytest.mark.parametrize("api", [iio2, iio3])
def test_write_empty_target_and_read(tmp_path, api):
    path = tmp_path / "image.png"
    path.touch()
    expected = np.array([[0, 127], [255, 42]], dtype=np.uint8)
    api.imwrite(path, expected)
    np.testing.assert_array_equal(api.imread(path), expected)


def test_zero_stat_size_with_content(tmp_path, monkeypatch):
    path = tmp_path / "image.png"
    expected = np.array([[0, 127], [255, 42]], dtype=np.uint8)
    iio3.imwrite(path, expected, plugin="pillow")
    original_stat = Path.stat

    def zero_size(self, *args, **kwargs):
        result = original_stat(self, *args, **kwargs)
        if self == path:
            values = list(result)
            values[6] = 0
            return os.stat_result(values)
        return result

    monkeypatch.setattr(Path, "stat", zero_size)
    np.testing.assert_array_equal(iio3.imread(path), expected)


@pytest.mark.parametrize("legacy_mode, error", [(False, OSError), (True, RuntimeError)])
def test_empty_file_explicit_plugin(tmp_path, legacy_mode, error):
    path = tmp_path / "empty.png"
    path.touch()
    calls = []
    failure = InitializationError("Plugin-specific failure")

    def reject(request):
        calls.append(request.filename)
        raise failure

    with pytest.raises(error) as exc_info:
        iio3.imopen(path, "r", plugin=reject, legacy_mode=legacy_mode)
    assert calls == [str(path)]
    assert exc_info.value.__cause__ is failure

    with iio3.imopen(path, "r", plugin=PluginV3) as plugin:
        assert plugin.request.filename == str(path)


def test_empty_directory_reaches_plugin(tmp_path, monkeypatch):
    path = tmp_path / "images.dcm"
    path.mkdir()
    config = PluginConfig(
        name="directory",
        class_name="PluginV3",
        module_name="imageio.core.v3_plugin_api",
    )
    monkeypatch.setitem(known_plugins, "directory", config)
    monkeypatch.setitem(
        known_extensions,
        ".dcm",
        [FileExtension(extension=".dcm", priority=["directory"])],
    )
    with iio3.imopen(path, "r") as plugin:
        assert plugin.request.filename == str(path)


def test_empty_file_closes_request(tmp_path):
    path = tmp_path / "empty.png"
    path.touch()
    request = Request(path, "r")
    handle = request.get_file()
    with pytest.raises(ValueError, match="is empty"):
        iio3.imopen(request, "r", legacy_mode=True)
    assert handle.closed
    assert request._file is None
    path.unlink()


def test_empty_file_read_error_closes_request(tmp_path, monkeypatch):
    path = tmp_path / "empty.png"
    path.touch()
    request = Request(path, "r")
    handle = request.get_file()
    failure = OSError("Read failed")

    def fail(self):
        raise failure

    monkeypatch.setattr(Request, "_read_first_bytes", fail)
    with pytest.raises(OSError) as exc_info:
        iio3.imopen(request, "r", legacy_mode=True)
    assert exc_info.value is failure
    assert handle.closed
    assert request._file is None


def test_empty_stream_retains_caller_ownership(monkeypatch):
    def reject(request, **kwargs):
        raise InitializationError("Not an image")

    monkeypatch.setattr(PluginConfig, "plugin_class", property(lambda self: reject))
    with BytesIO() as stream:
        with pytest.raises(OSError, match="Could not find a backend"):
            iio3.imread(stream)
        assert not stream.closed
