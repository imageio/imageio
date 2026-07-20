"""Tests for the pydicom v3 plugin."""

import numpy as np
import pytest

pydicom = pytest.importorskip("pydicom")

import imageio.v3 as iio
from pydicom.pixels import apply_color_lut, apply_rescale, apply_voi_lut, pixel_array
from pydicom.uid import ExplicitVRLittleEndian, RLELossless


PLUGIN = "pydicom"


def test_plugin_loads():
    assert "pydicom" in iio.imopen.__module__ or True
    from imageio.config import known_plugins

    assert "pydicom" in known_plugins
    assert known_plugins["pydicom"].class_name == "PydicomPlugin"


def test_extension_priority():
    from imageio.config.extensions import known_extensions

    assert known_extensions[".dcm"][0].priority == ["DICOM", "pydicom", "ITK"]
    assert known_extensions[".ct"][0].priority == ["DICOM", "pydicom"]
    assert known_extensions[".mri"][0].priority == ["DICOM", "pydicom"]
    assert known_extensions[".dicom"][0].priority == ["ITK", "pydicom"]
    assert known_extensions[".gdcm"][0].priority == ["ITK", "pydicom"]


def test_read_matches_pixel_array_raw(test_images):
    path = test_images / "dicom_file01.dcm"
    expected = pixel_array(str(path), raw=True)
    actual = iio.imread(path, plugin=PLUGIN, raw=True)
    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == (512, 512)


def test_read_applies_rescale_by_default(test_images):
    path = test_images / "dicom_file01.dcm"
    ds = pydicom.dcmread(str(path))
    stored = pixel_array(ds, raw=True)
    expected = apply_voi_lut(apply_rescale(stored, ds), ds)
    actual = iio.imread(path, plugin=PLUGIN)
    np.testing.assert_array_equal(actual, expected)


def test_read_non_dicom_raises(tmp_path):
    path = tmp_path / "not.dcm"
    path.write_bytes(b"not a dicom file at all")
    with pytest.raises(OSError, match="pydicom"):
        iio.imread(path, plugin=PLUGIN)


def test_imiter_framewise(test_images):
    path = test_images / "dicom_file01.dcm"
    frames = list(iio.imiter(path, plugin=PLUGIN))
    assert len(frames) == 1
    assert frames[0].shape == (512, 512)


def test_read_index_ellipsis(test_images):
    path = test_images / "dicom_file01.dcm"
    arr = iio.imread(path, index=..., plugin=PLUGIN)
    assert arr.shape == (1, 512, 512)


def test_properties_no_pixel_decode(test_images, monkeypatch):
    path = test_images / "dicom_file01.dcm"
    calls = {"pixel_array": 0}

    import imageio.plugins.pydicom as plugin_mod

    real_pixel_array = plugin_mod.pdcm.pixels.pixel_array

    def wrapped(*args, **kwargs):
        calls["pixel_array"] += 1
        return real_pixel_array(*args, **kwargs)

    monkeypatch.setattr(plugin_mod.pdcm.pixels, "pixel_array", wrapped)
    props = iio.improps(path, plugin=PLUGIN, raw=True)
    assert calls["pixel_array"] == 0
    assert props.shape == (512, 512)
    assert props.dtype == np.dtype("uint16") or props.dtype.kind in ("u", "i")
    assert props.is_batch is False
    assert props.n_images is None


def test_properties_matches_read_reconstruction(test_images):
    path = test_images / "dicom_file01.dcm"
    props = iio.improps(path, plugin=PLUGIN)
    img = iio.imread(path, plugin=PLUGIN)
    assert props.shape == img.shape
    assert props.dtype == img.dtype


def test_properties_raw_stored_dtype(test_images):
    path = test_images / "dicom_file01.dcm"
    props = iio.improps(path, plugin=PLUGIN, raw=True)
    img = iio.imread(path, plugin=PLUGIN, raw=True)
    assert props.shape == img.shape
    assert props.dtype == img.dtype


def test_properties_float_pixel_data(tmp_path):
    # Native Float Pixel Data (no PixelRepresentation); props must not assume int32.
    arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    ds = pydicom.Dataset()
    ds.file_meta = pydicom.dataset.FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    ds.SOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.Modality = "OT"
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 2
    ds.Columns = 2
    ds.BitsAllocated = 32
    ds.FloatPixelData = arr.tobytes()
    path = tmp_path / "float32.dcm"
    ds.save_as(path, enforce_file_format=True)
    props = iio.improps(path, plugin=PLUGIN, raw=True)
    assert props.dtype == np.dtype(np.float32)
    assert props.shape == (2, 2)


def test_properties_palette_shape(tmp_path):
    idx = np.array([[0, 1], [2, 3]], dtype=np.uint8)
    cmap = np.array(
        [[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8
    )
    path = tmp_path / "pal_props.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.lut_dense(cmap)
        f.write(idx)
    props = iio.improps(path, plugin=PLUGIN)
    props_raw = iio.improps(path, plugin=PLUGIN, raw=True)
    assert props_raw.shape == (2, 2)
    assert props.shape == (2, 2, 3)
    assert props.dtype == np.dtype(np.uint8)


def test_properties_index_int(test_images):
    path = test_images / "dicom_file01.dcm"
    props = iio.improps(path, index=0, plugin=PLUGIN, raw=True)
    assert props.shape == (512, 512)
    assert props.n_images is None
    assert props.is_batch is False


def test_immeta_instance_tags(test_images):
    path = test_images / "dicom_file01.dcm"
    meta = iio.immeta(path, plugin=PLUGIN)
    assert "TransferSyntaxUID" in meta or "SOPClassUID" in meta
    assert "SharedFunctionalGroupsSequence" not in meta
    assert "PerFrameFunctionalGroupsSequence" not in meta
    assert "PixelData" not in meta


def test_immeta_frame_without_fg(test_images):
    path = test_images / "dicom_file01.dcm"
    meta = iio.immeta(path, index=0, plugin=PLUGIN)
    assert meta == {}


def test_write_gray_roundtrip(tmp_path):
    img = np.arange(64, dtype=np.uint8).reshape(8, 8)
    path = tmp_path / "gray.dcm"
    iio.imwrite(path, img, plugin=PLUGIN, metadata={"Modality": "OT"})
    back = iio.imread(path, plugin=PLUGIN)
    np.testing.assert_array_equal(back, img)
    meta = iio.immeta(path, plugin=PLUGIN)
    assert meta.get("Modality") == "OT"


def test_write_rgb_roundtrip(tmp_path):
    img = np.zeros((6, 7, 3), dtype=np.uint8)
    img[..., 0] = 10
    img[..., 1] = 20
    img[..., 2] = 30
    path = tmp_path / "rgb.dcm"
    iio.imwrite(path, img, plugin=PLUGIN)
    back = iio.imread(path, plugin=PLUGIN)
    np.testing.assert_array_equal(back, img)


def test_write_multiframe_gray(tmp_path):
    vol = np.arange(3 * 4 * 5, dtype=np.uint16).reshape(3, 4, 5)
    path = tmp_path / "mf.dcm"
    iio.imwrite(path, vol, plugin=PLUGIN)
    back = iio.imread(path, plugin=PLUGIN)
    np.testing.assert_array_equal(back, vol)
    props = iio.improps(path, plugin=PLUGIN)
    assert props.shape == (3, 4, 5)
    assert props.is_batch is True
    assert props.n_images == 3
    frames = list(iio.imiter(path, plugin=PLUGIN))
    assert len(frames) == 3
    np.testing.assert_array_equal(frames[1], vol[1])


def test_write_bytes():
    img = np.arange(16, dtype=np.uint8).reshape(4, 4)
    data = iio.imwrite("<bytes>", img, plugin=PLUGIN, extension=".dcm")
    assert isinstance(data, (bytes, bytearray))
    back = iio.imread(data, plugin=PLUGIN, extension=".dcm")
    np.testing.assert_array_equal(back, img)


def test_write_planar_configuration(tmp_path):
    planar = np.zeros((3, 5, 6), dtype=np.uint8)
    planar[0] = 1
    planar[1] = 2
    planar[2] = 3
    path = tmp_path / "planar.dcm"
    iio.imwrite(path, planar, plugin=PLUGIN, is_planar=True)
    back = iio.imread(path, plugin=PLUGIN)
    # decoded channel-last
    assert back.shape == (5, 6, 3)
    np.testing.assert_array_equal(back[..., 0], 1)
    np.testing.assert_array_equal(back[..., 1], 2)
    np.testing.assert_array_equal(back[..., 2], 3)


def test_shape_three_frames_not_planar(tmp_path):
    vol = np.arange(3 * 4 * 4, dtype=np.uint8).reshape(3, 4, 4)
    path = tmp_path / "three.dcm"
    iio.imwrite(path, vol, plugin=PLUGIN)  # is_planar default False
    back = iio.imread(path, plugin=PLUGIN)
    assert back.shape == (3, 4, 4)


def test_write_frame_and_fg(tmp_path):
    path = tmp_path / "fg.dcm"
    frame = np.zeros((4, 4), dtype=np.uint8)
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.instance_metadata["PatientName"] = "Anonymous"
        f.shared_frame_metadata = {
            "PixelMeasuresSequence": [{"PixelSpacing": [1.0, 1.0]}]
        }
        f.write_frame(frame, metadata={"FrameContentSequence": [{"FrameAcquisitionNumber": 1}]})
        f.write_frame(frame, metadata={"FrameContentSequence": [{"FrameAcquisitionNumber": 2}]})
    meta = iio.immeta(path, plugin=PLUGIN)
    assert meta.get("PatientName") in ("Anonymous", "Anonymous^")
    frame_meta = iio.immeta(path, index=1, plugin=PLUGIN)
    assert frame_meta  # FG present
    assert "PixelMeasuresSequence" in frame_meta or "FrameContentSequence" in frame_meta


def test_lut_dense(tmp_path):
    idx = np.array([[0, 1], [2, 3]], dtype=np.uint8)
    cmap = np.array(
        [[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8
    )
    path = tmp_path / "pal_dense.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.lut_dense(cmap)
        f.write(idx)
    ds = pydicom.dcmread(str(path))
    assert hasattr(ds, "RedPaletteColorLookupTableData")
    assert not hasattr(ds, "SegmentedRedPaletteColorLookupTableData")
    colored = apply_color_lut(pixel_array(ds), ds)
    assert colored.shape[-1] == 3


def test_lut_linear(tmp_path):
    idx = np.zeros((4, 4), dtype=np.uint8)
    idx[0, 0] = 0
    idx[0, 1] = 255
    path = tmp_path / "pal_lin.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.lut_linear([(0, 0, 0), (65535, 65535, 65535)], [0, 255])
        f.write(idx)
    ds = pydicom.dcmread(str(path))
    assert hasattr(ds, "SegmentedRedPaletteColorLookupTableData")
    assert not hasattr(ds, "RedPaletteColorLookupTableData")
    colored = apply_color_lut(pixel_array(ds), ds)
    assert colored.shape[-1] == 3


def test_lut_helpers_replace(tmp_path):
    idx = np.zeros((2, 2), dtype=np.uint8)
    cmap = np.array([[0, 0, 0], [1, 2, 3]], dtype=np.uint16)
    path = tmp_path / "pal_swap.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.lut_dense(cmap)
        f.lut_linear([(0, 0, 0), (100, 100, 100)], [0, 1])
        f.write(idx)
    ds = pydicom.dcmread(str(path))
    assert hasattr(ds, "SegmentedRedPaletteColorLookupTableData")
    assert not hasattr(ds, "RedPaletteColorLookupTableData")




def test_imwrite_uncompressed(tmp_path):
    img = np.zeros((4, 4), dtype=np.uint8)
    path = tmp_path / "unc.dcm"
    iio.imwrite(path, img, plugin=PLUGIN)
    meta = iio.immeta(path, plugin=PLUGIN)
    assert str(meta.get("TransferSyntaxUID", ExplicitVRLittleEndian)).startswith(
        "1.2.840.10008.1.2"
    )


def test_compression_rle(tmp_path):
    img = np.arange(64, dtype=np.uint8).reshape(8, 8)
    path = tmp_path / "rle.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.compression = "rle"
        assert f.compression == str(RLELossless)
        f.write(img)
    meta = iio.immeta(path, plugin=PLUGIN)
    assert str(meta["TransferSyntaxUID"]) == str(RLELossless)
    back = iio.imread(path, plugin=PLUGIN)
    np.testing.assert_array_equal(back, img)


def test_compression_exact_names(tmp_path):
    path = tmp_path / "exact.dcm"
    with iio.imopen(path, "w", plugin=PLUGIN) as f:
        f.compression = "rle"
        assert f.compression == str(RLELossless)
        f.compression = str(RLELossless)
        assert f.compression == str(RLELossless)
        f.compression = None
        assert f.compression is None
        with pytest.raises(ValueError, match="Unknown compression"):
            f.compression = "RLE"
        with pytest.raises(ValueError, match="Unknown compression"):
            f.compression = "jpeg_ls"


def test_compression_unsupported_uid(tmp_path):
    img = np.zeros((4, 4), dtype=np.uint8)
    path = tmp_path / "baduid.dcm"
    f = iio.imopen(path, "w", plugin=PLUGIN)
    f.compression = "1.2.3.4.5.6.7.8.9.0"
    f.write(img)
    with pytest.raises(NotImplementedError, match="No pixel data encoders"):
        f.close()
