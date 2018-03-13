# styletest: ignore E501
""" Tests specific to parsing ffmpeg info.
"""

from imageio.testing import run_tests_if_main

import imageio


def dedent(text, dedent=8):
    lines = [line[dedent:] for line in text.splitlines()]
    text = '\n'.join(lines)
    return text.strip() + '\n'


def test_webcam_parse_device_names():
    # Ensure that the device list parser returns all video devices (issue #283)
    
    sample = dedent(r"""
        ffmpeg version 3.2.4 Copyright (c) 2000-2017 the FFmpeg developers
        built with gcc 6.3.0 (GCC)
        configuration: --enable-gpl --enable-version3 --enable-d3d11va --enable-dxva2 --enable-libmfx --enable-nvenc --enable-avisynthlibswresample   2.  3.100 /  2.  3.100
        libpostproc    54.  1.100 / 54.  1.100
        [dshow @ 039a7e20] DirectShow video devices (some may be both video and audio devices)
        [dshow @ 039a7e20]  "AVerMedia USB Polaris Analog Capture"
        [dshow @ 039a7e20]     Alternative name "@device_pnp_\\?\usb#vid_07ca&pid_c039&mi_01#8&55f1102&0&0001#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\{9b365890-165f-11d0-a195-0020afd156e4}"
        [dshow @ 039a7e20]  "Lenovo EasyCamera"
        [dshow @ 039a7e20]     Alternative name "@device_pnp_\\?\usb#vid_04f2&pid_b50f&mi_00#6&bbc4ae1&1&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global"
        [dshow @ 039a7e20] DirectShow audio devices
        [dshow @ 039a7e20]  "Microphone (2- USB Multimedia Audio Device)"
        [dshow @ 039a7e20]     Alternative name "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\wave_{73C17834-AA57-4CA1-847A-6BBEB1E0F2E6}"
        [dshow @ 039a7e20]  "SPDIF Interface (Multimedia Audio Device)"
        [dshow @ 039a7e20]     Alternative name "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\wave_{617B63FB-CFC0-4D10-AE30-42A66CAF6A4E}"
        dummy: Immediate exit requested
        """)
    
    # Parse the sample
    device_names = imageio.plugins.ffmpeg.parse_device_names(sample)

    # Assert that the device_names list has the correct length
    assert len(device_names) == 2


run_tests_if_main()
