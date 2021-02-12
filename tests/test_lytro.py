""" Test npz plugin functionality.
"""
from __future__ import division
import numpy as np
import json

from pytest import raises
from imageio.testing import run_tests_if_main, need_internet
import imageio
from imageio.core import get_remote_file, Request


# Set file names for test images in imageio-binaries repo
LFR_FILENAME = "images/Ankylosaurus_&_Stegosaurus.LFR"
THUMB_FILENAME = "images/Ankylosaurus_&_Stegosaurus_Thumbnail.jpg"
RAW_ILLUM_FILENAME = "images/lenslet_whiteimage.RAW"
RAW_ILLUM_META_FILENAME = "images/lenslet_whiteimage.TXT"
LFP_FILENAME = "images/Guitar.lfp"
RAW_F0_FILENAME = "images/IMG_0001__frame.raw"
RAW_F0_META_FILENAME = "images/IMG_0001__frame.json"
PNG_FILENAME = "images/chelsea.png"


def test_lytro_lfr_format():
    """
    Test basic read/write properties of LytroLfrFormat
    """
    # Get test images
    need_internet()
    lfr_file = get_remote_file(LFR_FILENAME)
    raw_illum_file = get_remote_file(RAW_ILLUM_FILENAME)
    lfp_file = get_remote_file(LFP_FILENAME)
    raw_f01_file = get_remote_file(RAW_F0_FILENAME)
    png_file = get_remote_file(PNG_FILENAME)

    # Test lytro lfr format
    format = imageio.formats["lytro-lfr"]
    assert format.name == "LYTRO-LFR"
    assert format.__module__.endswith("lytro")

    # Test can read
    assert format.can_read(Request(lfr_file, "ri"))

    # Test cannot read, cannot write
    assert not format.can_read(Request(lfr_file, "rv"))
    assert not format.can_read(Request(lfr_file, "rI"))
    assert not format.can_read(Request(lfr_file, "rV"))
    assert not format.can_read(Request(lfp_file, "ri"))
    assert not format.can_read(Request(raw_illum_file, "ri"))
    assert not format.can_read(Request(raw_f01_file, "ri"))
    assert not format.can_read(Request(png_file, "ri"))

    assert not format.can_write(Request(lfr_file, "wi"))
    assert not format.can_write(Request(lfp_file, "wi"))
    assert not format.can_write(Request(raw_f01_file, "wi"))
    assert not format.can_write(Request(raw_illum_file, "wi"))
    assert not format.can_write(Request(png_file, "wi"))


def test_lytro_illum_raw_format():
    """
    Test basic read/write properties of LytroRawFormat
    """
    # Get test images
    need_internet()
    lfr_file = get_remote_file(LFR_FILENAME)
    raw_illum_file = get_remote_file(RAW_ILLUM_FILENAME)
    lfp_file = get_remote_file(LFP_FILENAME)
    raw_f01_file = get_remote_file(RAW_F0_FILENAME)
    png_file = get_remote_file(PNG_FILENAME)

    # Test lytro raw format
    format = imageio.formats["lytro-illum-raw"]
    assert format.name == "LYTRO-ILLUM-RAW"
    assert format.__module__.endswith("lytro")

    # Test can read, cannot write
    assert format.can_read(Request(raw_illum_file, "ri"))

    # Test cannot read, cannot write
    assert not format.can_read(Request(raw_illum_file, "rv"))
    assert not format.can_read(Request(raw_illum_file, "rI"))
    assert not format.can_read(Request(raw_illum_file, "rV"))
    assert not format.can_read(Request(lfr_file, "ri"))
    assert not format.can_read(Request(lfp_file, "ri"))
    assert not format.can_read(Request(png_file, "ri"))

    assert not format.can_write(Request(raw_illum_file, "wi"))
    assert not format.can_write(Request(lfr_file, "wi"))
    assert not format.can_write(Request(lfp_file, "wi"))
    assert not format.can_write(Request(raw_f01_file, "wi"))
    assert not format.can_write(Request(png_file, "wi"))


def test_lytro_f01_raw_format():
    """
    Test basic read/write properties of LytroRawFormat
    """
    # Get test images
    need_internet()
    lfr_file = get_remote_file(LFR_FILENAME)
    raw_illum_file = get_remote_file(RAW_ILLUM_FILENAME)
    lfp_file = get_remote_file(LFP_FILENAME)
    raw_f01_file = get_remote_file(RAW_F0_FILENAME)
    png_file = get_remote_file(PNG_FILENAME)

    # Test lytro raw format
    format = imageio.formats["lytro-illum-raw"]
    assert format.name == "LYTRO-ILLUM-RAW"
    assert format.__module__.endswith("lytro")

    # Test can read, cannot write
    assert format.can_read(Request(raw_f01_file, "ri"))

    # Test cannot read, cannot write
    assert not format.can_read(Request(raw_f01_file, "rv"))
    assert not format.can_read(Request(raw_f01_file, "rI"))
    assert not format.can_read(Request(raw_f01_file, "rV"))
    assert not format.can_read(Request(lfr_file, "ri"))
    assert not format.can_read(Request(lfp_file, "ri"))
    assert not format.can_read(Request(png_file, "ri"))

    assert not format.can_write(Request(raw_f01_file, "wi"))
    assert not format.can_write(Request(lfr_file, "wi"))
    assert not format.can_write(Request(lfp_file, "wi"))
    assert not format.can_write(Request(raw_illum_file, "wi"))
    assert not format.can_write(Request(png_file, "wi"))


def test_lytro_lfp_format():
    """
    Test basic read/write properties of LytroRawFormat
    """
    # Get test images
    need_internet()
    lfr_file = get_remote_file(LFR_FILENAME)
    raw_illum_file = get_remote_file(RAW_ILLUM_FILENAME)
    lfp_file = get_remote_file(LFP_FILENAME)
    raw_f01_file = get_remote_file(RAW_F0_FILENAME)
    png_file = get_remote_file(PNG_FILENAME)

    # Test lytro raw format
    format = imageio.formats["lytro-lfp"]
    assert format.name == "LYTRO-LFP"
    assert format.__module__.endswith("lytro")

    # Test can read, cannot write
    assert format.can_read(Request(lfp_file, "ri"))

    # Test cannot read, cannot write
    assert not format.can_read(Request(lfp_file, "rv"))
    assert not format.can_read(Request(lfp_file, "rI"))
    assert not format.can_read(Request(lfp_file, "rV"))
    assert not format.can_read(Request(lfr_file, "ri"))
    assert not format.can_read(Request(raw_f01_file, "ri"))
    assert not format.can_read(Request(raw_illum_file, "ri"))
    assert not format.can_read(Request(png_file, "ri"))

    assert not format.can_write(Request(lfp_file, "wi"))
    assert not format.can_write(Request(lfr_file, "wi"))
    assert not format.can_write(Request(raw_f01_file, "wi"))
    assert not format.can_write(Request(raw_illum_file, "wi"))
    assert not format.can_write(Request(png_file, "wi"))


def test_lytro_lfr_reading():
    """Test reading of lytro .lfr file"""
    # Get test images
    need_internet()
    lfr_file = get_remote_file(LFR_FILENAME)
    thumb_file = get_remote_file(THUMB_FILENAME)

    # Read image and thumbnail
    img = imageio.imread(lfr_file, format="lytro-lfr")
    thumb_gt = imageio.imread(thumb_file)

    # Test image shape and some pixel values
    # Pixel values are extracted from the Matlab reference implementation
    assert img.shape == (5368, 7728)
    assert round(img[14, 32], 15) == 0.100684261974585
    assert round(img[1531, 95], 15) == 0.250244379276637
    assert round(img[1619, 94], 15) == 0.286412512218964
    assert round(img[1619, 3354], 15) == 0.345063538611926
    assert round(img[1747, 3660], 15) == 0.222873900293255
    assert round(img[1813, 5789], 15) == 0.079178885630499
    assert round(img[4578, 7352], 15) == 0.256109481915934
    assert round(img[5086, 7568], 15) == 0.106549364613881
    assert round(img[4951, 2025], 15) == 0.348973607038123

    # Test extracted thumbnail against downloaded one
    assert np.array_equal(img._meta["thumbnail"]["image"], thumb_gt)

    # Test metadata and privateMetadata against ground truth data
    metadata_gt = {
        "image": {
            "width": 7728,
            "orientation": 1,
            "modulationExposureBias": 0.2689966559410095,
            "pixelPacking": {"bitsPerPixel": 10, "endianness": "little"},
            "limitExposureBias": 0.0,
            "height": 5368,
            "pixelFormat": {
                "white": {"gr": 1023, "r": 1023, "b": 1023, "gb": 1023},
                "black": {"gr": 64, "r": 64, "b": 64, "gb": 64},
                "rightShift": 0,
            },
            "iso": 80,
            "originOnSensor": {"x": 0, "y": 0},
            "mosaic": {"tile": "r,gr:gb,b", "upperLeftPixel": "gr"},
            "color": {
                "whiteBalanceGain": {
                    "gr": 1.0,
                    "r": 1.378859281539917,
                    "b": 1.1484659910202026,
                    "gb": 1.0,
                },
                "ccm": [
                    2.2271547317504883,
                    -1.055293321609497,
                    -0.1718614399433136,
                    -0.4269128441810608,
                    1.7458617687225342,
                    -0.3189488351345062,
                    -0.20497213304042816,
                    -0.7469924688339233,
                    1.9519646167755127,
                ],
            },
        },
        "generator": "lightning",
        "schema": "http://schema.lytro.com/lfp/lytro_illum_public/"
        + "1.3.5/lytro_illum_public_schema.json",
        "camera": {"make": "Lytro, Inc.", "model": "ILLUM", "firmware": "1.1.1 (23)"},
        "devices": {
            "clock": {"zuluTime": "2015-05-17T13:31:37.412Z", "isTimeValid": True},
            "sensor": {
                "pixelPitch": 1.4e-06,
                "normalizedResponses": [
                    {
                        "b": 0.7344976663589478,
                        "gb": 1.0,
                        "cct": 5100,
                        "gr": 1.0,
                        "r": 0.7761663198471069,
                    }
                ],
                "perCcm": [
                    {
                        "ccm": [
                            2.006272077560425,
                            -0.5362802147865295,
                            -0.46999192237854004,
                            -0.6019303798675537,
                            1.836044430732727,
                            -0.23411400616168976,
                            -0.8173090815544128,
                            -1.6435128450393677,
                            3.4608218669891357,
                        ],
                        "cct": 2850.0,
                    },
                    {
                        "ccm": [
                            2.4793264865875244,
                            -1.2747985124588013,
                            -0.20452789962291718,
                            -0.5189455151557922,
                            1.6118407249450684,
                            -0.09289517253637314,
                            -0.3602483570575714,
                            -1.0115599632263184,
                            2.3718082904815674,
                        ],
                        "cct": 4150.0,
                    },
                    {
                        "ccm": [
                            2.1902196407318115,
                            -1.0231428146362305,
                            -0.16707684099674225,
                            -0.4134329855442047,
                            1.7654914855957031,
                            -0.3520585000514984,
                            -0.18222910165786743,
                            -0.7082417607307434,
                            1.8904708623886108,
                        ],
                        "cct": 6500.0,
                    },
                ],
                "pixelWidth": 7728,
                "bitsPerPixel": 10,
                "mosaic": {"tile": "r,gr:gb,b", "upperLeftPixel": "gr"},
                "pixelHeight": 5368,
                "baseIso": 80,
                "analogGain": {"gr": 1.0, "r": 1.0, "b": 1.0, "gb": 1.0},
            },
            "shutter": {
                "mechanism": "focalPlaneCurtain",
                "frameExposureDuration": 0.000784054514952004,
                "pixelExposureDuration": 0.000784054514952004,
                "maxSyncSpeed": 0.004,
            },
            "mla": {
                "config": "com.lytro.mla.3",
                "rotation": -0.0005426123971119523,
                "tiling": "hexUniformRowMajor",
                "scaleFactor": {"x": 1.0, "y": 1.0003429651260376},
                "lensPitch": 2e-05,
                "sensorOffset": {
                    "x": 8.421777725219726e-06,
                    "y": -9.545820355415345e-07,
                    "z": 3.7e-05,
                },
            },
            "lens": {
                "fNumber": 2.199776378914589,
                "exitPupilOffset": {"z": 0.09728562164306641},
                "zoomStep": -297,
                "focusStep": 309,
                "opticalCenterOffset": {
                    "x": 1.48461913340725e-05,
                    "y": 3.083264164160937e-05,
                },
                "focalLength": 0.024199465511189833,
                "infinityLambda": 33.89023289728373,
            },
            "battery": {
                "make": "Lytro",
                "chargeLevel": 8,
                "model": "B01-3760",
                "cycleCount": 5,
            },
            "accelerometer": {
                "samples": [
                    {
                        "x": -0.3689117431640625,
                        "y": 9.022918701171875,
                        "time": 0.0,
                        "z": -1.339324951171875,
                    }
                ]
            },
        },
        "settings": {
            "exposure": {
                "bracketCount": 3,
                "compensation": 0.30000001192092896,
                "mode": "program",
                "meter": {
                    "mode": "evaluative",
                    "roiMode": "af",
                    "roi": [{"top": 0.0, "left": 0.0, "bottom": 1.0, "right": 1.0}],
                },
                "bracketEnable": False,
                "bracketStep": 1.0,
                "bracketOffset": 0.0,
                "aeLock": False,
            },
            "whiteBalance": {"tint": -76.0, "mode": "auto", "cct": 6199},
            "shutter": {
                "selfTimerEnable": False,
                "selfTimerDuration": 2.0,
                "driveMode": "single",
            },
            "focus": {
                "afActuationMode": "single",
                "mode": "auto",
                "ringLock": False,
                "bracketCount": 3,
                "bracketEnable": False,
                "afDriveMode": "single",
                "bracketStep": 3.0,
                "bracketOffset": 0.0,
                "roi": [{"top": 0.0, "left": 0.0, "bottom": 1.0, "right": 1.0}],
                "captureLambda": -4.0,
            },
            "zoom": {"ringLock": False},
            "flash": {
                "mode": "unknown",
                "exposureCompensation": 0.0,
                "zoomMode": "auto",
                "curtainTriggerSync": "front",
                "afAssistMode": "auto",
            },
            "depth": {"assist": "on", "histogram": "on", "overlay": "on"},
        },
        "algorithms": {
            "awb": {
                "roi": "fullFrame",
                "computed": {
                    "cct": 6199,
                    "gain": {
                        "gr": 1.0,
                        "r": 1.378859281539917,
                        "b": 1.1484659910202026,
                        "gb": 1.0,
                    },
                },
            },
            "ae": {"computed": {"ev": 1.0}, "roi": "followAf", "mode": "live"},
            "af": {"computed": {"focusStep": 309}, "roi": "focusRoi"},
        },
        "picture": {
            "totalFrames": 1,
            "frameIndex": 0,
            "dcfDirectory": "100PHOTO",
            "dcfFile": "IMG_0813",
        },
    }
    private_metadata_gt = {
        "generator": "lightning",
        "schema": "http://schema.lytro.com/lfp/lytro_illum_private/"
        + "1.1.1/lytro_illum_private_schema.json",
        "devices": {"sensor": {"serialNumber": "0C220593"}},
        "camera": {"serialNumber": "B5143909630"},
    }

    assert img._meta["metadata"] == metadata_gt
    assert img._meta["privateMetadata"] == private_metadata_gt

    # Read metadata only (with thumbnail)
    img = imageio.imread(lfr_file, format="lytro-lfr", meta_only=True)
    assert np.array_equal(img, [])
    assert img._meta["metadata"] == metadata_gt
    assert img._meta["privateMetadata"] == private_metadata_gt
    assert np.array_equal(img._meta["thumbnail"]["image"], thumb_gt)

    # Read metadata only (without thumbnail)
    img = imageio.imread(
        lfr_file, format="lytro-lfr", meta_only=True, include_thumbnail=False
    )
    assert np.array_equal(img, [])
    assert img._meta["metadata"] == metadata_gt
    assert img._meta["privateMetadata"] == private_metadata_gt
    assert "thumbnail" not in img._meta.keys()

    # Test fail
    test_reader = imageio.read(lfr_file, "lytro-lfr")
    raises(IndexError, test_reader.get_data, -1)
    raises(IndexError, test_reader.get_data, 3)


def test_lytro_lfp_reading():
    """Test reading of lytro .lfr file"""
    # Get test images
    need_internet()
    lfp_file = get_remote_file(LFP_FILENAME)

    # Read image and thumbnail
    img = imageio.imread(lfp_file, format="lytro-lfp")

    # Test image shape and some pixel values
    # Pixel values are extracted from the Matlab reference implementation
    assert img.shape == (3280, 3280)
    assert round(img[171, 94], 15) == 0.284249084249084
    assert round(img[701, 292], 15) == 0.289865689865690
    assert round(img[1280, 94], 15) == 0.065201465201465
    assert round(img[2364, 2640], 15) == 0.056166056166056
    assert round(img[2733, 1549], 15) == 0.100366300366300
    assert round(img[2739, 2585], 15) == 0.078388278388278
    assert round(img[1032, 2230], 15) == 0.354578754578755
    assert round(img[1480, 1758], 15) == 0.098656898656899

    # Test metadata and privateMetadata against ground truth data
    metadata_gt = {
        "type": "lightField",
        "image": {
            "width": 3280,
            "height": 3280,
            "orientation": 1,
            "representation": "rawPacked",
            "rawDetails": {
                "pixelFormat": {
                    "rightShift": 0,
                    "black": {"r": 168, "gr": 168, "gb": 168, "b": 168},
                    "white": {"r": 4095, "gr": 4095, "gb": 4095, "b": 4095},
                },
                "pixelPacking": {"endianness": "big", "bitsPerPixel": 12},
                "mosaic": {"tile": "r,gr:gb,b", "upperLeftPixel": "b"},
            },
            "color": {
                "ccmRgbToSrgbArray": [
                    3.1115827560424805,
                    -1.9393929243087769,
                    -0.172189861536026,
                    -0.3629055917263031,
                    1.6408803462982178,
                    -0.27797481417655945,
                    0.07896701246500015,
                    -1.1558042764663696,
                    2.0768373012542725,
                ],
                "gamma": 0.41666001081466675,
                "applied": {},
                "whiteBalanceGain": {"r": 1, "gr": 1, "gb": 1, "b": 1.2578125},
            },
            "modulationExposureBias": -1.1139298677444458,
            "limitExposureBias": 0,
        },
        "devices": {
            "clock": {"zuluTime": "2014-05-16T13:31:21.000Z"},
            "sensor": {
                "bitsPerPixel": 12,
                "mosaic": {"tile": "r,gr:gb,b", "upperLeftPixel": "b"},
                "iso": 207,
                "analogGain": {"r": 5.625, "gr": 4.125, "gb": 4.125, "b": 4.75},
                "pixelPitch": 1.3999999761581417e-06,
            },
            "lens": {
                "infinityLambda": 18.033008575439453,
                "focalLength": 0.006840000152587891,
                "zoomStep": 943,
                "focusStep": 672,
                "fNumber": 1.9199999570846558,
                "temperature": 23.642822265625,
                "temperatureAdc": 2896,
                "zoomStepperOffset": -2,
                "focusStepperOffset": 25,
                "exitPupilOffset": {"z": 0.22357696533203125},
            },
            "ndfilter": {"exposureBias": 0},
            "shutter": {
                "mechanism": "sensorOpenApertureClose",
                "frameExposureDuration": 0.016554275527596474,
                "pixelExposureDuration": 0.016554275527596474,
            },
            "soc": {"temperature": 27.0545654296875, "temperatureAdc": 3319},
            "accelerometer": {
                "sampleArray": [
                    {
                        "x": -0.019607843831181526,
                        "y": 1.015686273574829,
                        "z": 0.03529411926865578,
                        "time": 0,
                    }
                ]
            },
            "mla": {
                "tiling": "hexUniformRowMajor",
                "lensPitch": 1.3999999999999998e-05,
                "rotation": -0.0008588103810325265,
                "defectArray": [],
                "config": "com.lytro.mla.11",
                "scaleFactor": {"x": 1, "y": 1.0003734827041626},
                "sensorOffset": {
                    "x": -8.177771568298344e-06,
                    "y": 8.002278804779054e-07,
                    "z": 2.5e-05,
                },
            },
        },
        "modes": {
            "creative": "tap",
            "regionOfInterestArray": [
                {"type": "exposure", "x": 0.5125047564506531, "y": 0.723964273929596},
                {"type": "creative", "x": 0.5125047564506531, "y": 0.723964273929596},
            ],
            "manualControls": False,
            "exposureDurationMode": "auto",
            "isoMode": "auto",
            "ndFilterMode": "auto",
            "exposureLock": False,
            "overscan": 1.0526316165924072,
        },
        "camera": {
            "make": "Lytro, Inc.",
            "model": "F01",
            "firmware": "v1.0a208, vv1.2.2, Wed Sep  4 14:43:36 PDT 2013, "
            "fec5f2a239a2823b391a385b94ec6fc8c56bb5b1, "
            "mods=0, ofw=0",
        },
    }
    private_metadata_gt = {
        "devices": {"sensor": {"sensorSerial": "0x408F1FB8B3515D9A"}},
        "camera": {"serialNumber": "A303134643"},
    }

    assert img._meta["metadata"] == metadata_gt
    assert img._meta["privateMetadata"] == private_metadata_gt

    # Read metadata only
    img = imageio.imread(lfp_file, format="lytro-lfp", meta_only=True)
    assert np.array_equal(img, [])
    assert img._meta["metadata"] == metadata_gt
    assert img._meta["privateMetadata"] == private_metadata_gt

    # Test fail
    test_reader = imageio.read(lfp_file, "lytro-lfp")
    raises(IndexError, test_reader.get_data, -1)
    raises(IndexError, test_reader.get_data, 3)


def test_lytro_raw_illum_reading():
    """Test reading of lytro .raw file"""
    # Get test images
    need_internet()
    raw_file = get_remote_file(RAW_ILLUM_FILENAME)
    raw_meta_file = get_remote_file(RAW_ILLUM_META_FILENAME)

    # Read image and metadata file
    img = imageio.imread(raw_file, format="lytro-illum-raw")
    meta_gt = json.load(open(raw_meta_file))

    # Test image shape and some pixel values
    # Pixel values are extracted from the Matlab reference implementation
    assert img.shape == (5368, 7728)
    assert round(img[24, 48], 15) == 0.738025415444770
    assert round(img[3692, 86], 15) == 0.132942326490714
    assert round(img[258, 1658], 15) == 0.687194525904203
    assert round(img[1349, 6765], 15) == 0.113391984359726
    assert round(img[210, 6761], 15) == 0.162267839687195
    assert round(img[5231, 6459], 15) == 0.784946236559140
    assert round(img[5213, 7477], 15) == 0.095796676441838
    assert round(img[2745, 3789], 15) == 0.760508308895406
    assert round(img[1428, 4192], 15) == 0.621700879765396

    # Test extracted metadata against extracted metadata from .txt file
    assert img._meta == meta_gt

    # Read metadata only
    img = imageio.imread(raw_file, format="lytro-illum-raw", meta_only=True)
    assert np.array_equal(img, [])
    assert img._meta == meta_gt

    # Test fail
    test_reader = imageio.read(raw_file, "lytro-illum-raw")
    raises(IndexError, test_reader.get_data, -1)
    raises(IndexError, test_reader.get_data, 3)


def test_lytro_raw_f0_reading():
    """Test reading of lytro .raw file"""
    # Get test images
    need_internet()
    raw_file = get_remote_file(RAW_F0_FILENAME)
    raw_meta_file = get_remote_file(RAW_F0_META_FILENAME)

    # Read image and metadata file
    img = imageio.imread(raw_file, format="lytro-f01-raw")
    meta_gt = json.load(open(raw_meta_file))

    # Test image shape and some pixel values
    # Pixel values are extracted from the Matlab reference implementation
    assert img.shape == (3280, 3280)
    assert round(img[16, 7], 15) == 0.044688644688645
    assert round(img[803, 74], 15) == 0.064713064713065
    assert round(img[599, 321], 15) == 0.059340659340659
    assert round(img[1630, 665], 15) == 0.198046398046398
    assert round(img[940, 2030], 15) == 0.130647130647131
    assert round(img[3164, 2031], 15) == 0.129914529914530
    assert round(img[3235, 3250], 15) == 0.136019536019536
    assert round(img[2954, 889], 15) == 0.159706959706960
    assert round(img[1546, 1243], 15) == 0.227350427350427

    # Test extracted metadata against extracted metadata from .txt file
    assert img._meta == meta_gt

    # Read metadata only
    img = imageio.imread(raw_file, format="lytro-f01-raw", meta_only=True)
    assert np.array_equal(img, [])
    assert img._meta == meta_gt

    # Test fail
    test_reader = imageio.read(raw_file, "lytro-f01-raw")
    raises(IndexError, test_reader.get_data, -1)
    raises(IndexError, test_reader.get_data, 3)


run_tests_if_main()
