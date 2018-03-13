# styletest: ignore E501
""" Tests specific to parsing ffmpeg info.
"""

from imageio.testing import run_tests_if_main, need_internet

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


def test_get_correct_fps1():
    # from issue #262
    
    sample = dedent(r"""
        fmpeg version 3.2.2 Copyright (c) 2000-2016 the FFmpeg developers
        built with Apple LLVM version 8.0.0 (clang-800.0.42.1)
        configuration: --prefix=/usr/local/Cellar/ffmpeg/3.2.2 --enable-shared --enable-pthreads --enable-gpl --enable-version3 --enable-hardcoded-tables --enable-avresample --cc=clang --host-cflags= --host-ldflags= --enable-ffplay --enable-frei0r --enable-libass --enable-libfdk-aac --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopus --enable-librtmp --enable-libschroedinger --enable-libspeex --enable-libtheora --enable-libvorbis --enable-libvpx --enable-libx264 --enable-libxvid --enable-opencl --disable-lzma --enable-libopenjpeg --disable-decoder=jpeg2000 --extra-cflags=-I/usr/local/Cellar/openjpeg/2.1.2/include/openjpeg-2.1 --enable-nonfree --enable-vda
        libavutil      55. 34.100 / 55. 34.100
        libavcodec     57. 64.101 / 57. 64.101
        libavformat    57. 56.100 / 57. 56.100
        libavdevice    57.  1.100 / 57.  1.100
        libavfilter     6. 65.100 /  6. 65.100
        libavresample   3.  1.  0 /  3.  1.  0
        libswscale      4.  2.100 /  4.  2.100
        libswresample   2.  3.100 /  2.  3.100
        libpostproc    54.  1.100 / 54.  1.100
        Input #0, mov,mp4,m4a,3gp,3g2,mj2, from '/Users/echeng/video.mp4':
        Metadata:
            major_brand     : mp42
            minor_version   : 1
            compatible_brands: isom3gp43gp5
        Duration: 00:16:05.80, start: 0.000000, bitrate: 1764 kb/s
            Stream #0:0(eng): Audio: aac (LC) (mp4a / 0x6134706D), 8000 Hz, mono, fltp, 40 kb/s (default)
            Metadata:
            handler_name    : soun
            Stream #0:1(eng): Video: mpeg4 (Simple Profile) (mp4v / 0x7634706D), yuv420p, 640x480 [SAR 1:1 DAR 4:3], 1720 kb/s, 29.46 fps, 26.58 tbr, 90k tbn, 1k tbc (default)
            Metadata:
            handler_name    : vide
        Output #0, image2pipe, to 'pipe:':
        Metadata:
            major_brand     : mp42
            minor_version   : 1
            compatible_brands: isom3gp43gp5
            encoder         : Lavf57.56.100
            Stream #0:0(eng): Video: rawvideo (RGB[24] / 0x18424752), rgb24, 640x480 [SAR 1:1 DAR 4:3], q=2-31, 200 kb/s, 26.58 fps, 26.58 tbn, 26.58 tbc (default)
            Metadata:
            handler_name    : vide
            encoder         : Lavc57.64.101 rawvideo
        Stream mapping:
        """)
    
    info = imageio.plugins.ffmpeg.parse_ffmpeg_info(sample)
    assert info['fps'] == 26.58


def test_get_correct_fps2():
    # from issue #262
    
    sample = dedent(r"""
        ffprobe version 3.2.2 Copyright (c) 2007-2016 the FFmpeg developers
        built with Apple LLVM version 8.0.0 (clang-800.0.42.1)
        configuration: --prefix=/usr/local/Cellar/ffmpeg/3.2.2 --enable-shared --enable-pthreads --enable-gpl --enable-version3 --enable-hardcoded-tables --enable-avresample --cc=clang --host-cflags= --host-ldflags= --enable-ffplay --enable-frei0r --enable-libass --enable-libfdk-aac --enable-libfreetype --enable-libmp3lame --enable-libopencore-amrnb --enable-libopencore-amrwb --enable-libopus --enable-librtmp --enable-libschroedinger --enable-libspeex --enable-libtheora --enable-libvorbis --enable-libvpx --enable-libx264 --enable-libxvid --enable-opencl --disable-lzma --enable-libopenjpeg --disable-decoder=jpeg2000 --extra-cflags=-I/usr/local/Cellar/openjpeg/2.1.2/include/openjpeg-2.1 --enable-nonfree --enable-vda
        libavutil      55. 34.100 / 55. 34.100
        libavcodec     57. 64.101 / 57. 64.101
        libavformat    57. 56.100 / 57. 56.100
        libavdevice    57.  1.100 / 57.  1.100
        libavfilter     6. 65.100 /  6. 65.100
        libavresample   3.  1.  0 /  3.  1.  0
        libswscale      4.  2.100 /  4.  2.100
        libswresample   2.  3.100 /  2.  3.100
        libpostproc    54.  1.100 / 54.  1.100
        Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':
        Metadata:
            major_brand     : mp42
            minor_version   : 1
            compatible_brands: isom3gp43gp5
        Duration: 00:08:44.53, start: 0.000000, bitrate: 1830 kb/s
            Stream #0:0(eng): Audio: aac (LC) (mp4a / 0x6134706D), 8000 Hz, mono, fltp, 40 kb/s (default)
            Metadata:
            handler_name    : soun
            Stream #0:1(eng): Video: mpeg4 (Simple Profile) (mp4v / 0x7634706D), yuv420p, 640x480 [SAR 1:1 DAR 4:3], 1785 kb/s, 29.27 fps, 1k tbr, 90k tbn, 1k tbc (default)
            Metadata:
            handler_name    : vide
        """)
    
    info = imageio.plugins.ffmpeg.parse_ffmpeg_info(sample)
    assert info['fps'] == 29.27


def test_overload_fps():
    
    need_internet()
    
    # Native
    r = imageio.get_reader('imageio:cockatoo.mp4')
    assert len(r) == 280  # native
    ims = [im for im in r]
    assert len(ims) == 280
    # imageio.mimwrite('~/parot280.gif', ims[:30])
    
    # Less
    r = imageio.get_reader('imageio:cockatoo.mp4', fps=8)
    assert len(r) == 112
    ims = [im for im in r]
    assert len(ims) == 112
    # imageio.mimwrite('~/parot112.gif', ims[:30])
    
    # More
    r = imageio.get_reader('imageio:cockatoo.mp4', fps=24)
    assert len(r) == 336
    ims = [im for im in r]
    assert len(ims) == 336
    # imageio.mimwrite('~/parot336.gif', ims[:30])
    
    # Do we calculate nframes correctly? To be fair, the reader wont try to
    # read beyond what it thinks how many frames it has. But this at least 
    # makes sure that this works.
    for fps in (8.0, 8.02, 8.04, 8.06, 8.08):
        r = imageio.get_reader('imageio:cockatoo.mp4', fps=fps)
        n = len(r)
        i = 0
        try:
            while True:
                r.get_next_data()
                i += 1
        except (StopIteration, IndexError):
            pass
        # print(r._meta['duration'], r._meta['fps'], r._meta['duration'] * fps, r._meta['nframes'], n)
        assert i == n


run_tests_if_main()
