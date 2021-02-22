# styletest: ignore E501
""" Tests specific to parsing ffmpeg info.
"""

from imageio.testing import run_tests_if_main, need_internet

import imageio


def dedent(text, dedent=8):
    lines = [line[dedent:] for line in text.splitlines()]
    text = "\n".join(lines)
    return text.strip() + "\n"


def test_webcam_parse_device_names():
    # Ensure that the device list parser returns all video devices (issue #283)

    sample = dedent(
        r"""
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
        """
    )

    # Parse the sample
    device_names = imageio.plugins.ffmpeg.parse_device_names(sample)

    # Assert that the device_names list has the correct length
    assert len(device_names) == 2


def test_overload_fps():
    need_internet()

    # Native
    r = imageio.get_reader("imageio:cockatoo.mp4")
    assert r.count_frames() == 280  # native
    assert int(r._meta["fps"] * r._meta["duration"] + 0.5) == 280
    ims = [im for im in r]
    assert len(ims) in (280, 281)
    # imageio.mimwrite('~/parot280.gif', ims[:30])

    # Less
    r = imageio.get_reader("imageio:cockatoo.mp4", fps=8)
    # assert r.count_frames() == 112  # cant :(
    assert int(r._meta["fps"] * r._meta["duration"] + 0.5) == 112  # note the mismatch
    ims = [im for im in r]
    assert len(ims) == 114
    # imageio.mimwrite('~/parot112.gif', ims[:30])

    # More
    r = imageio.get_reader("imageio:cockatoo.mp4", fps=24)
    # assert r.count_frames() == 336  # cant :(
    ims = [im for im in r]
    assert int(r._meta["fps"] * r._meta["duration"] + 0.5) == 336
    assert len(ims) in (336, 337)
    # imageio.mimwrite('~/parot336.gif', ims[:30])

    # Do we calculate nframes correctly? To be fair, the reader wont try to
    # read beyond what it thinks how many frames it has. But this at least
    # makes sure that this works.
    for fps in (8.0, 8.02, 8.04, 8.06, 8.08):
        r = imageio.get_reader("imageio:cockatoo.mp4", fps=fps)
        n = int(r._meta["fps"] * r._meta["duration"] + 0.5)
        i = 0
        try:
            while True:
                r.get_next_data()
                i += 1
        except (StopIteration, IndexError):
            pass
        # print(r._meta['duration'], r._meta['fps'], r._meta['duration'] * fps, r._meta['nframes'], n)
        assert n - 2 <= i <= n + 2


run_tests_if_main()
