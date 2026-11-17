"""Loader diagnostics must not interfere with FreeImage plugin probing."""

import io
import logging

import numpy as np
from PIL import Image

import imageio.v3 as iio
from imageio.config import known_extensions
from imageio.plugins import _freeimage


def fail_to_load():
    raise OSError("incompatible architecture: have x86_64, need arm64")


def test_freeimage_loader_failure_is_logged_at_debug(monkeypatch, caplog):
    wrapper = _freeimage.Freeimage()
    monkeypatch.setattr(wrapper, "load_freeimage", fail_to_load)

    with caplog.at_level(logging.DEBUG, logger=_freeimage.__name__):
        assert wrapper.has_lib() is False

    assert "incompatible architecture: have x86_64, need arm64" in caplog.text
    assert caplog.records[0].levelno == logging.DEBUG


def test_freeimage_loader_failure_is_quiet_by_default(monkeypatch, caplog):
    wrapper = _freeimage.Freeimage()
    monkeypatch.setattr(wrapper, "load_freeimage", fail_to_load)

    with caplog.at_level(logging.WARNING, logger=_freeimage.__name__):
        assert wrapper.has_lib() is False

    assert not caplog.records


def test_freeimage_available_library_has_no_failure_log(caplog):
    wrapper = _freeimage.Freeimage()
    wrapper._lib = object()

    with caplog.at_level(logging.DEBUG, logger=_freeimage.__name__):
        assert wrapper.has_lib() is True

    assert not caplog.records


def test_freeimage_loader_failure_preserves_plugin_fallback(monkeypatch, caplog):
    monkeypatch.setattr(_freeimage.fi, "_lib", None)
    monkeypatch.setattr(_freeimage.fi, "load_freeimage", fail_to_load)
    monkeypatch.setattr(known_extensions[".png"][0], "priority", ["PNG-FI", "pillow"])
    pixels = np.array([[0, 64], [128, 255]], dtype=np.uint8)
    encoded = io.BytesIO()
    Image.fromarray(pixels).save(encoded, format="PNG")

    with caplog.at_level(logging.DEBUG, logger=_freeimage.__name__):
        decoded = iio.imread(encoded.getvalue(), extension=".png")

    np.testing.assert_array_equal(decoded, pixels)
    assert "incompatible architecture: have x86_64, need arm64" in caplog.text
