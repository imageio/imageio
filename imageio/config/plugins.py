from typing import Any, Dict
import importlib

from imageio.core.legacy_plugin_wrapper import LegacyPlugin


class PluginConfig:
    def __init__(
        self,
        name: str,
        class_name: str = "LegacyPlugin",
        module_name: str = "imageio.code.imopen",
        *,
        is_legacy: bool = False,
        package_name: str = None,
    ) -> None:
        self.name = name
        self.class_name = class_name
        self.module_name = module_name
        self.package_name = package_name
        self.is_legacy = is_legacy

    @property
    def plugin_class(self) -> Any:
        """Get the plugin class (import if needed)

        Returns
        -------
        plugin_class : Any
            The class that can be used to instantiate plugins.

        """

        module = importlib.import_module(self.module_name, self.package_name)
        clazz = getattr(module, self.class_name)

        if self.is_legacy:
            legacy_plugin = clazz(self.name, "A legacy plugin")

            def partial_legacy_plugin(request):
                return LegacyPlugin(request, legacy_plugin)

            clazz = partial_legacy_plugin

        return clazz


_plugin_list = [
    PluginConfig(
        name="pillow", class_name="PillowPlugin", module_name="imageio.plugins.pillow"
    ),
    # legacy plugins (and their many names)
    PluginConfig(
        name="BSDF",
        class_name="BsdfFormat",
        module_name="imageio.plugins.bsdf",
        is_legacy=True,
    ),
    PluginConfig(
        name="DICOM",
        class_name="DicomFormat",
        module_name="imageio.plugins.dicom",
        is_legacy=True,
    ),
    PluginConfig(
        name="FEI",
        class_name="FEISEMFormat",
        module_name="imageio.plugins.feisem",
        is_legacy=True,
    ),
    PluginConfig(
        name="FFMPEG",
        class_name="FfmpegFormat",
        module_name="imageio.plugins.ffmpeg",
        is_legacy=True,
    ),
    PluginConfig(
        name="fits",
        class_name="FitsFormat",
        module_name="imageio.plugins.fits",
        is_legacy=True,
    ),
    PluginConfig(
        name="GDAL",
        class_name="GdalFormat",
        module_name="imageio.plugins.gdal",
        is_legacy=True,
    ),
    PluginConfig(
        name="itk",
        class_name="ItkFormat",
        module_name="imageio.plugins.simpleitk",
        is_legacy=True,
    ),
    PluginConfig(
        name="npz",
        class_name="NpzFormat",
        module_name="imageio.plugins.npz",
        is_legacy=True,
    ),
    PluginConfig(
        name="SPE",
        class_name="SpeFormat",
        module_name="imageio.plugins.spe",
        is_legacy=True,
    ),
    PluginConfig(
        name="SWF",
        class_name="SWFFormat",
        module_name="imageio.plugins.swf",
        is_legacy=True,
    ),
    PluginConfig(
        name="tiff",
        class_name="TiffFormat",
        module_name="imageio.plugins.tifffile",
        is_legacy=True,
    ),
    *[
        PluginConfig(
            name=name,
            class_name="LytroFormat",
            module_name="imageio.plugins.lytro",
            is_legacy=True,
        )
        for name in ["LYTRO-F01-RAW", "LYTRO-ILLUM-RAW", "LYTRO-LFP", "LYTRO-LFR"]
    ],
    *[
        PluginConfig(
            name=name,
            class_name="FreeimageFormat",
            module_name="imageio.plugins.freeimage",
            is_legacy=True,
        )
        for name in [
            "BMP-FI",
            "CUT-FI",
            "DDS-FI",
            "EXR-FI",
            "PNG-FI",
            "G3-FI",
            "G3-FI",
            "GIF-FI",
            "HDR-FI",
            "ICO-FI",
            "IFF-FI",
            "J2K-FI",
            "JNG-FI",
            "JP2-FI",
            "JPEG-FI",
            "JPEG-XR-FI",
            "KOALA-FI",
            "PBM-FI",
            "PBMRAW-FI",
            "PCD-FI",
            "PCX-FI",
            "PFM-FI",
            "PGM-FI",
            "PGMRAW-FI",
            "PPM-FI",
            "PPMRAW-FI",
            "PSD-FI",
            "RAS-FI",
            "RAW-FI",
            "SGI-FI",
            "TARGA-FI",
            "TIFF-FI",
            "WBMP-FI",
            "WEBP-FI",
            "XBM-FI",
            "XPM-FI",
        ]
    ],
    *[
        PluginConfig(
            name=name,
            class_name="PillowFormat",
            module_name="imageio.plugins.pillow_legacy",
            is_legacy=True,
        )
        for name in [
            "BMP-PIL",
            "BUFR-PIL",
            "CUR-PIL",
            "DCX-PIL",
            "DDS-PIL",
            "DIB-PIL",
            "EPS-PIL",
            "FITS-PIL",
            "FLI-PIL",
            "FPX-PIL",
            "FTEX-PIL",
            "GBR-PIL",
            "GIF-PIL",
            "GRIB-PIL",
            "HDF5-PIL",
            "ICNS-PIL",
            "ICO-PIL",
            "IM-PIL",
            "IMT-PIL",
            "IPTC-PIL",
            "JPEG-PIL",
            "JPEG2000-PIL",
            "MCIDAS-PIL",
            "MIC-PIL",
            "MPO-PIL",
            "MSP-PIL",
            "PCD-PIL",
            "PCX-PIL",
            "PICT-PIL",
            "PIXAR-PIL",
            "PNG-PIL",
            "PPM-PIL",
            "PSD-PIL",
            "SGI-PIL",
            "SPIDER-PIL",
            "SUN-PIL",
            "TGA-PIL",
            "TIFF-PIL",
            "WMF-PIL",
            "XBM-PIL",
            "XPM-PIL",
            "XVTHUMB-PIL",
        ]
    ],
]

known_plugins = {x.name: x for x in _plugin_list}
