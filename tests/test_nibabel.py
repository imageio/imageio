"""Tests for the nibabel plugin."""

import numpy as np
import pytest

import imageio.v3 as iio

nib = pytest.importorskip("nibabel")


def save_nifti(path, data, affine=None):
    """Write ``data`` to ``path`` using nibabel directly."""

    affine = np.eye(4) if affine is None else affine
    nib.save(nib.Nifti1Image(data, affine), str(path))
    return path


@pytest.mark.parametrize("extension", [".nii", ".nii.gz"])
def test_read(tmp_path, extension):
    """Read a NIfTI file and compare it to what nibabel returns."""

    data = np.arange(2 * 3 * 4, dtype=np.int16).reshape(2, 3, 4)
    path = save_nifti(tmp_path / f"image{extension}", data)

    actual = iio.imread(path, plugin="nibabel")
    expected = np.asanyarray(nib.load(str(path)).dataobj)

    assert actual.dtype == np.int16
    assert np.array_equal(actual, expected)
    assert np.array_equal(actual, data)


def test_read_4d(tmp_path):
    """The time axis of a 4D file is part of the ndimage."""

    data = np.arange(2 * 3 * 4 * 5, dtype=np.float32).reshape(2, 3, 4, 5)
    path = save_nifti(tmp_path / "image4d.nii", data)

    actual = iio.imread(path, plugin="nibabel")

    assert actual.shape == (2, 3, 4, 5)
    assert np.array_equal(actual, data)


def test_read_from_bytes(tmp_path):
    """A file can be read from a byte string, too."""

    data = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    path = save_nifti(tmp_path / "image.nii", data)

    actual = iio.imread(path.read_bytes(), extension=".nii", plugin="nibabel")

    assert np.array_equal(actual, data)


def test_read_uses_registered_extension(tmp_path):
    """The plugin is selected from the file extension alone."""

    data = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    path = save_nifti(tmp_path / "image.nii.gz", data)

    assert np.array_equal(iio.imread(path), data)


def test_read_invalid_file(tmp_path):
    """Reading something that is not a neuroimaging file raises."""

    path = tmp_path / "not_an_image.nii"
    path.write_bytes(b"this is not a nifti file, not even close" * 4)

    with pytest.raises(OSError):
        iio.imread(path, plugin="nibabel")


def test_index(tmp_path):
    """``index`` selects the single image or the batch of one image."""

    data = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    path = save_nifti(tmp_path / "image.nii", data)

    assert np.array_equal(iio.imread(path, index=0, plugin="nibabel"), data)

    batch = iio.imread(path, index=..., plugin="nibabel")
    assert batch.shape == (1, 2, 3, 4)
    assert np.array_equal(batch[0], data)

    with pytest.raises(ValueError):
        iio.imread(path, index=1, plugin="nibabel")


def test_iter(tmp_path):
    """A neuroimaging file holds a single ndimage."""

    data = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    path = save_nifti(tmp_path / "image.nii", data)

    images = list(iio.imiter(path, plugin="nibabel"))

    assert len(images) == 1
    assert np.array_equal(images[0], data)


def test_properties(tmp_path):
    """Properties are taken from the image and its affine."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)
    affine = np.diag([2.0, 3.0, 4.0, 1.0])
    path = save_nifti(tmp_path / "image.nii", data, affine)

    properties = iio.improps(path, plugin="nibabel")

    assert properties.shape == (2, 3, 4)
    assert properties.dtype == np.uint8
    assert properties.is_batch is False
    assert properties.spacing == (2.0, 3.0, 4.0)

    batched = iio.improps(path, index=..., plugin="nibabel")
    assert batched.shape == (1, 2, 3, 4)
    assert batched.is_batch is True


def test_metadata(tmp_path):
    """Metadata exposes the affine and the human-readable header fields."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)
    affine = np.diag([2.0, 3.0, 4.0, 1.0])
    path = save_nifti(tmp_path / "image.nii", data, affine)

    metadata = iio.immeta(path, plugin="nibabel")

    assert np.array_equal(metadata["affine"], affine)
    assert metadata["datatype"] == 2  # NIFTI_TYPE_UINT8
    assert metadata["descrip"] == ""


def test_write(tmp_path):
    """Writing a NIfTI file stores both the data and the affine."""

    data = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    affine = np.diag([2.0, 3.0, 4.0, 1.0])
    path = tmp_path / "written.nii"

    iio.imwrite(path, data, plugin="nibabel", affine=affine)

    image = nib.load(str(path))
    assert image.shape == (2, 3, 4)
    assert np.array_equal(np.asanyarray(image.dataobj), data)
    assert np.allclose(image.affine, affine)


def test_write_gzip(tmp_path):
    """The compressed variant is recognized from the filename."""

    data = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    path = tmp_path / "written.nii.gz"

    iio.imwrite(path, data, plugin="nibabel")

    assert path.read_bytes()[:2] == b"\x1f\x8b"  # gzip magic
    assert np.array_equal(iio.imread(path, plugin="nibabel"), data)


def test_write_default_affine(tmp_path):
    """Without an affine the image gets an identity affine."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)
    path = tmp_path / "written.nii"

    iio.imwrite(path, data, plugin="nibabel")

    assert np.allclose(nib.load(str(path)).affine, np.eye(4))


def test_write_4d(tmp_path):
    """A 4D ndimage is written as a 4D NIfTI file."""

    data = np.arange(2 * 3 * 4 * 5, dtype=np.int16).reshape(2, 3, 4, 5)
    path = tmp_path / "written4d.nii"

    iio.imwrite(path, data, plugin="nibabel")

    assert np.array_equal(iio.imread(path, plugin="nibabel"), data)


def test_write_list(tmp_path):
    """A list of ndimages is stacked along a new trailing axis."""

    images = [np.full((2, 3, 4), value, dtype=np.int16) for value in (1, 2, 3)]
    path = tmp_path / "stacked.nii"

    iio.imwrite(path, images, plugin="nibabel")

    actual = iio.imread(path, plugin="nibabel")
    assert actual.shape == (2, 3, 4, 3)
    assert np.array_equal(actual, np.stack(images, axis=-1))


@pytest.mark.parametrize("extension", [".mgh", ".mgz"])
def test_write_mgh(tmp_path, extension):
    """MGH files can be written and read back."""

    data = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    path = tmp_path / f"written{extension}"

    iio.imwrite(path, data, plugin="nibabel")

    assert np.array_equal(iio.imread(path, plugin="nibabel"), data)


def test_write_to_bytes():
    """Writing to the special ``<bytes>`` target returns the encoded file."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)

    encoded = iio.imwrite("<bytes>", data, extension=".nii", plugin="nibabel")

    assert encoded[:4] == b"\x5c\x01\x00\x00"  # NIfTI-1 header size


def test_write_unsupported_extension(tmp_path):
    """The plugin refuses to write formats it cannot create."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)

    with pytest.raises(OSError):
        iio.imwrite(tmp_path / "image.png", data, plugin="nibabel")


def test_write_invalid_affine(tmp_path):
    """An affine that is not a 4x4 matrix is rejected."""

    data = np.zeros((2, 3, 4), dtype=np.uint8)

    with pytest.raises(ValueError):
        iio.imwrite(tmp_path / "image.nii", data, plugin="nibabel", affine=np.eye(3))


def test_read_non_image_format(tmp_path):
    """Formats that are not images (e.g. GIFTI surfaces) are rejected."""

    from nibabel.gifti import GiftiDataArray, GiftiImage

    path = tmp_path / "surface.gii"
    surface = GiftiImage(darrays=[GiftiDataArray(np.zeros((4, 3), dtype=np.float32))])
    surface.to_filename(str(path))

    with pytest.raises(OSError):
        iio.imread(path, plugin="nibabel")


def test_metadata_mgh(tmp_path):
    """MGH headers have no NIfTI fields, so only the affine is reported."""

    path = tmp_path / "image.mgz"
    iio.imwrite(path, np.zeros((2, 3, 4), dtype=np.float32), plugin="nibabel")

    metadata = iio.immeta(path, plugin="nibabel")

    assert np.array_equal(metadata["affine"], np.eye(4))
    assert "datatype" not in metadata
