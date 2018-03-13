# -*- coding: utf-8 -*-
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

Code inspired/based on code from moviepy: https://github.com/Zulko/moviepy/
by Zulko

"""

from __future__ import absolute_import, print_function, division

import sys
import os
import stat
import re
import time
import threading
import subprocess as sp
import logging

import numpy as np

from .. import formats
from ..core import (Format, get_remote_file, string_types, read_n_bytes,
                    image_as_uint, get_platform, CannotReadFrameError,
                    InternetNotAllowedError, NeedDownloadError)


ISWIN = sys.platform.startswith('win')

FNAME_PER_PLATFORM = {
    'osx32': 'ffmpeg-osx-v3.2.4',
    'osx64': 'ffmpeg-osx-v3.2.4',
    'win32': 'ffmpeg-win32-v3.2.4.exe',
    'win64': 'ffmpeg-win32-v3.2.4.exe',
    'linux32': 'ffmpeg-linux32-v3.3.1',
    'linux64': 'ffmpeg-linux64-v3.3.1',
}


def limit_lines(lines, N=32):
    """ When number of lines > 2*N, reduce to N.
    """
    if len(lines) > 2*N:
        lines = [b'... showing only last few lines ...'] + lines[-N:]
    return lines


def download(directory=None, force_download=False):
    """ Download the ffmpeg exe to your computer.

    Parameters
    ----------
    directory : str | None
        The directory where the file will be cached if a download was
        required to obtain the file. By default, the appdata directory
        is used. This is also the first directory that is checked for
        a local version of the file.
    force_download : bool | str
        If True, the file will be downloaded even if a local copy exists
        (and this copy will be overwritten). Can also be a YYYY-MM-DD date
        to ensure a file is up-to-date (modified date of a file on disk,
        if present, is checked).
    """
    plat = get_platform()
    if not (plat and plat in FNAME_PER_PLATFORM):
        raise RuntimeError("FFMPEG exe isn't available for platform %s" % plat)
    fname = 'ffmpeg/' + FNAME_PER_PLATFORM[plat]
    get_remote_file(fname=fname,
                    directory=directory,
                    force_download=force_download)


def get_exe():
    """ Get ffmpeg exe
    """
    # Try ffmpeg exe in order of priority.
    # 1. Try environment variable.
    exe = os.getenv('IMAGEIO_FFMPEG_EXE', None)
    if exe:
        return exe

    plat = get_platform()

    # 2. Try our own version from the imageio-binaries repository
    if plat and plat in FNAME_PER_PLATFORM:
        try:
            exe = get_remote_file('ffmpeg/' + FNAME_PER_PLATFORM[plat],
                                  auto=False)
            os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)  # executable
            return exe
        except (NeedDownloadError, InternetNotAllowedError):
            pass
            
    # 3. Try binary from conda package
    # (installed e.g. via `conda install ffmpeg -c conda-forge`)
    if plat.startswith('win'):
        exe = os.path.join(sys.prefix, 'Library', 'bin', 'ffmpeg.exe')
    else:
        exe = os.path.join(sys.prefix, 'bin', 'ffmpeg')
    if exe and os.path.isfile(exe):
        try:
            with open(os.devnull, "w") as null:
                sp.check_call([exe, "-version"], stdout=null, stderr=sp.STDOUT)
                return exe
        except (OSError, ValueError, sp.CalledProcessError):
            pass
    
    # 4. Try system ffmpeg command
    exe = "ffmpeg"
    try:
        with open(os.devnull, "w") as null:
            sp.check_call([exe, "-version"], stdout=null, stderr=sp.STDOUT)
            return exe
    except (OSError, ValueError, sp.CalledProcessError):
        pass

    # Nothing was found so far
    raise NeedDownloadError('Need ffmpeg exe. '
                            'You can obtain it with either:\n'
                            '  - install using conda: '
                            'conda install ffmpeg -c conda-forge\n'
                            '  - download using the command: '
                            'imageio_download_bin ffmpeg\n'
                            '  - download by calling (in Python): '
                            'imageio.plugins.ffmpeg.download()\n'
                            )


# Get camera format
if sys.platform.startswith('win'):
    CAM_FORMAT = 'dshow'  # dshow or vfwcap
elif sys.platform.startswith('linux'):
    CAM_FORMAT = 'video4linux2'
elif sys.platform.startswith('darwin'):
    CAM_FORMAT = 'avfoundation'
else:  # pragma: no cover
    CAM_FORMAT = 'unknown-cam-format'


class FfmpegFormat(Format):
    """ The ffmpeg format provides reading and writing for a wide range
    of movie formats such as .avi, .mpeg, .mp4, etc. And also to read
    streams from webcams and USB cameras. 
    
    To read from camera streams, supply "<video0>" as the filename,
    where the "0" can be replaced with any index of cameras known to
    the system.
    
    Note that for reading regular video files, the avbin plugin is more
    efficient.
    
    The ffmpeg plugin requires an ``ffmpeg`` binary. Imageio searches
    this binary in the following locations (order of priority):
    
    - The path stored in the ``IMAGEIO_FFMPEG_EXE`` environment
      variable, which can be set using e.g.
      ``os.environ['IMAGEIO_FFMPEG_EXE'] = '/path/to/my/ffmpeg'``
    - The binary downloaded from the "imageio-binaries" repository
      (see below) which is stored either in the "imageio/resources"
      directory or in the user directory.
    - A binary installed as an anaconda package (see below).
    - The system ``ffmpeg`` command.
    
    If the binary is not available on the system, it can be downloaded
    manually from <https://github.com/imageio/imageio-binaries> by
    either
    
    - the command line script ``imageio_download_bin ffmpeg``,
    - the Python method ``imageio.plugins.ffmpeg.download()``, or
    - anaconda: ``conda install ffmpeg -c conda-forge``.
    
    Parameters for reading
    ----------------------
    fps : scalar
        The number of frames per second to read the data at. Default None (i.e.
        read at the file's own fps). One can use this for files with a
        variable fps, or in cases where imageio is unable to correctly detect
        the fps.
    loop : bool
        If True, the video will rewind as soon as a frame is requested
        beyond the last frame. Otherwise, IndexError is raised. Default False.
    size : str | tuple
        The frame size (i.e. resolution) to read the images, e.g. 
        (100, 100) or "640x480". For camera streams, this allows setting
        the capture resolution. For normal video data, ffmpeg will
        rescale the data.
    pixelformat : str
        The pixel format for the camera to use (e.g. "yuyv422" or
        "gray"). The camera needs to support the format in order for
        this to take effect. Note that the images produced by this
        reader are always rgb8.
    input_params : list
        List additional arguments to ffmpeg for input file options.
        (Can also be provided as ``ffmpeg_params`` for backwards compatibility)
        Example ffmpeg arguments to use aggressive error handling:
        ['-err_detect', 'aggressive']
    output_params : list
        List additional arguments to ffmpeg for output file options (i.e. the
        stream being read by imageio).
    print_info : bool
        Print information about the video file as reported by ffmpeg.
    
    Parameters for saving
    ---------------------
    fps : scalar
        The number of frames per second. Default 10.
    codec : str
        the video codec to use. Default 'libx264', which represents the
        widely available mpeg4. Except when saving .wmv files, then the
        defaults is 'msmpeg4' which is more commonly supported for windows
    quality : float | None
        Video output quality. Default is 5. Uses variable bit rate. Highest
        quality is 10, lowest is 0. Set to None to prevent variable bitrate
        flags to FFMPEG so you can manually specify them using output_params
        instead. Specifying a fixed bitrate using 'bitrate' disables this
        parameter.
    bitrate : int | None
        Set a constant bitrate for the video encoding. Default is None causing
        'quality' parameter to be used instead.  Better quality videos with
        smaller file sizes will result from using the 'quality'  variable
        bitrate parameter rather than specifiying a fixed bitrate with this
        parameter.
    pixelformat: str
        The output video pixel format. Default is 'yuv420p' which most widely
        supported by video players.
    input_params : list
        List additional arguments to ffmpeg for input file options (i.e. the
        stream that imageio provides).
    output_params : list
        List additional arguments to ffmpeg for output file options.
        (Can also be provided as ``ffmpeg_params`` for backwards compatibility)
        Example ffmpeg arguments to use only intra frames and set aspect ratio:
        ['-intra', '-aspect', '16:9']
    ffmpeg_log_level: str
        Sets ffmpeg output log level.  Default is "warning".
        Values can be "quiet", "panic", "fatal", "error", "warning", "info"
        "verbose", or "debug". Also prints the FFMPEG command being used by
        imageio if "info", "verbose", or "debug".
    macro_block_size: int
        Size constraint for video. Width and height, must be divisible by this
        number. If not divisible by this number imageio will tell ffmpeg to
        scale the image up to the next closest size
        divisible by this number. Most codecs are compatible with a macroblock
        size of 16 (default), some can go smaller (4, 8). To disable this
        automatic feature set it to None, however be warned many players can't
        decode videos that are odd in size and some codecs will produce poor
        results or fail. See https://en.wikipedia.org/wiki/Macroblock.
    """

    def _can_read(self, request):
        if request.mode[1] not in 'I?':
            return False

        # Read from video stream?
        # Note that we could write the _video flag here, but a user might
        # select this format explicitly (and this code is not run)
        if request.filename in ['<video%i>' % i for i in range(10)]:
            return True

        # Read from file that we know?
        if request.extension in self.extensions:
            return True

    def _can_write(self, request):
        if request.mode[1] in (self.modes + '?'):
            if request.extension in self.extensions:
                return True

    # --

    class Reader(Format.Reader):

        _exe = None
        _frame_catcher = None

        @classmethod
        def _get_exe(cls):
            cls._exe = cls._exe or get_exe()
            return cls._exe

        def _get_cam_inputname(self, index):
            if sys.platform.startswith('linux'):
                return '/dev/' + self.request._video[1:-1]

            elif sys.platform.startswith('win'):
                # Ask ffmpeg for list of dshow device names
                cmd = [self._exe, '-list_devices', 'true',
                       '-f', CAM_FORMAT, '-i', 'dummy']
                # Set `shell=True` in sp.Popen to prevent popup of
                # a command line window in frozen applications.
                proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE,
                                stderr=sp.PIPE, shell=True)
                proc.stdout.readline()
                proc.terminate()
                infos = proc.stderr.read().decode('utf-8')
                # Return device name at index
                try:
                    name = parse_device_names(infos)[index]
                except IndexError:
                    raise IndexError('No ffdshow camera at index %i.' % index)
                return 'video=%s' % name

            elif sys.platform.startswith('darwin'):
                # Appears that newer ffmpeg builds don't support -list-devices
                # on OS X. But you can directly open the camera by index.
                name = str(index)
                return name

            else:  # pragma: no cover
                return '??'

        def _open(self, loop=False, size=None, pixelformat=None,
                  print_info=False, ffmpeg_params=None,
                  input_params=None, output_params=None, fps=None):
            # Get exe
            self._exe = self._get_exe()
            # Process input args
            self._arg_loop = bool(loop)
            if size is None:
                self._arg_size = None
            elif isinstance(size, tuple):
                self._arg_size = "%ix%i" % size
            elif isinstance(size, string_types) and 'x' in size:
                self._arg_size = size
            else:
                raise ValueError('FFMPEG size must be tuple of "NxM"')
            if pixelformat is None:
                pass
            elif not isinstance(pixelformat, string_types):
                raise ValueError('FFMPEG pixelformat must be str')
            self._arg_pixelformat = pixelformat
            self._arg_input_params = input_params or []
            self._arg_output_params = output_params or []
            self._arg_input_params += ffmpeg_params or []  # backward compat
            # Write "_video"_arg
            self.request._video = None
            if self.request.filename in ['<video%i>' % i for i in range(10)]:
                self.request._video = self.request.filename
            # Get local filename
            if self.request._video:
                index = int(self.request._video[-2])
                self._filename = self._get_cam_inputname(index)
            else:
                self._filename = self.request.get_local_filename()
            # Determine pixel format and depth
            self._pix_fmt = 'rgb24'
            self._depth = 4 if self._pix_fmt == "rgba" else 3
            # Initialize parameters
            self._proc = None
            self._pos = -1
            self._meta = {'plugin': 'ffmpeg', 'nframes': float('inf')}
            self._lastread = None
            # Start ffmpeg subprocess and get meta information
            self._initialize()
            self._load_infos()

            # For cameras, create thread that keeps reading the images
            if self.request._video:
                w, h = self._meta['size']
                framesize = self._depth * w * h
                self._frame_catcher = FrameCatcher(self._proc.stdout,
                                                   framesize)

        def _close(self):
            self._terminate()  # Short timeout
            self._proc = None

        def _get_length(self):
            return self._meta['nframes']

        def _get_data(self, index):
            """ Reads a frame at index. Note for coders: getting an
            arbitrary frame in the video with ffmpeg can be painfully
            slow if some decoding has to be done. This function tries
            to avoid fectching arbitrary frames whenever possible, by
            moving between adjacent frames. """
            # Modulo index (for looping)
            if self._meta['nframes'] and self._meta['nframes'] < float('inf'):
                if self._arg_loop:
                    index %= self._meta['nframes']

            if index == self._pos:
                return self._lastread, dict(new=False)
            elif index < 0:
                raise IndexError('Frame index must be > 0')
            elif index >= self._meta['nframes']:
                raise IndexError('Reached end of video')
            else:
                if (index < self._pos) or (index > self._pos+100):
                    self._reinitialize(index)
                else:
                    self._skip_frames(index-self._pos-1)
                result, is_new = self._read_frame()
                self._pos = index
                return result, dict(new=is_new)

        def _get_meta_data(self, index):
            return self._meta

        def _initialize(self):
            """ Opens the file, creates the pipe. """
            # Create input args
            if self.request._video:
                iargs = ['-f', CAM_FORMAT]
                if self._arg_pixelformat:
                    iargs.extend(['-pix_fmt', self._arg_pixelformat])
                if self._arg_size:
                    iargs.extend(['-s', self._arg_size])
            else:
                iargs = []
            # Output args, for writing to pipe
            oargs = ['-f', 'image2pipe',
                     '-pix_fmt', self._pix_fmt,
                     '-vcodec', 'rawvideo']
            oargs.extend(['-s', self._arg_size] if self._arg_size else [])
            if self.request.kwargs.get('fps', None):
                fps = float(self.request.kwargs['fps'])
                oargs += ['-r', "%.02f" % fps]
            # Create process
            cmd = [self._exe] + self._arg_input_params
            cmd += iargs + ['-i', self._filename]
            cmd += oargs + self._arg_output_params + ['-']
            # For Windows, set `shell=True` in sp.Popen to prevent popup
            # of a command line window in frozen applications.
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE,
                                  shell=ISWIN)

            # Create thread that keeps reading from stderr
            self._stderr_catcher = StreamCatcher(self._proc.stderr)

        def _reinitialize(self, index=0):
            """ Restarts the reading, starts at an arbitrary location
            (!! SLOW !!) """
            if self.request._video:
                raise RuntimeError('No random access when streaming from cam.')
            self._close()
            if index == 0:
                self._initialize()
            else:
                starttime = index / self._meta['fps']

                # Create input args -> start time
                # Need minimum 6 significant digits accurate frame seeking
                # and to support higher fps videos
                # Also appears this epsilon below is needed to ensure frame
                # accurate seeking in some cases
                epsilon = -1/self._meta['fps']*0.1
                iargs = ['-ss', "%.06f" % (starttime+epsilon)]
                iargs += ['-i', self._filename]

                # Output args, for writing to pipe
                oargs = ['-f', 'image2pipe',
                         '-pix_fmt', self._pix_fmt,
                         '-vcodec', 'rawvideo']
                oargs.extend(['-s', self._arg_size] if self._arg_size else [])
                if self.request.kwargs.get('fps', None):
                    fps = float(self.request.kwargs['fps'])
                    oargs += ['-r', "%.02f" % fps]
                
                # Create process
                cmd = [self._exe] + self._arg_input_params + iargs
                cmd += oargs + self._arg_output_params + ['-']
                # For Windows, set `shell=True` in sp.Popen to prevent popup
                # of a command line window in frozen applications.
                self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                      stdout=sp.PIPE, stderr=sp.PIPE,
                                      shell=ISWIN)

                # Create thread that keeps reading from stderr
                self._stderr_catcher = StreamCatcher(self._proc.stderr)

        def _terminate(self):
            """ Terminate the sub process.
            """
            # Check
            if self._proc is None:  # pragma: no cover
                return  # no process
            if self._proc.poll() is not None:
                return  # process already dead
            # Terminate process
            # Using kill since self._proc.terminate() does not seem
            # to work for ffmpeg, leaves processes hanging
            self._proc.kill()
            
            # Tell threads to stop when they have a chance. They are probably
            # blocked on reading from their file, but let's play it safe.
            if self._stderr_catcher:
                self._stderr_catcher.stop_me()
            if self._frame_catcher:
                self._frame_catcher.stop_me()

        def _load_infos(self):
            """ reads the FFMPEG info on the file and sets size fps
            duration and nframes. """

            # Wait for the catcher to get the meta information
            etime = time.time() + 10.0
            while (not self._stderr_catcher.header) and time.time() < etime:
                time.sleep(0.01)

            # Check whether we have the information
            infos = self._stderr_catcher.header
            if not infos:
                self._terminate()
                if self.request._video:
                    ffmpeg_err = 'FFMPEG STDERR OUTPUT:\n' + \
                                 self._stderr_catcher.get_text(.1)+"\n"
                    if "darwin" in sys.platform:
                        if "Unknown input format: 'avfoundation'" in \
                                ffmpeg_err:
                            ffmpeg_err += "Try installing FFMPEG using " \
                                          "home brew to get a version with " \
                                          "support for cameras."
                    raise IndexError('No video4linux camera at %s.\n\n%s' %
                                     (self.request._video, ffmpeg_err))
                else:
                    err2 = self._stderr_catcher.get_text(0.2)
                    fmt = 'Could not load meta information\n=== stderr ===\n%s'
                    raise IOError(fmt % err2)

            if self.request.kwargs.get('print_info', False):
                # print the whole info text returned by FFMPEG
                print(infos)
                print('-'*80)
            lines = infos.splitlines()
            if "No such file or directory" in lines[-1]:
                if self.request._video:
                    raise IOError("Could not open steam %s." % self._filename)
                else:  # pragma: no cover - this is checked by Request
                    raise IOError("%s not found! Wrong path?" % self._filename)
            
            # Go!
            self._meta.update(parse_ffmpeg_info(lines))
            
            # Update with fps with user-value?
            if self.request.kwargs.get('fps', None):
                self._meta['fps'] = float(self.request.kwargs['fps'])
            
            # Estimate nframes
            self._meta['nframes'] = np.inf
            if self._meta['fps'] > 0 and 'duration' in self._meta:
                n = int(round(self._meta['duration'] * self._meta['fps']))
                self._meta['nframes'] = n
        
        def _read_frame_data(self):
            # Init and check
            w, h = self._meta['size']
            framesize = self._depth * w * h
            assert self._proc is not None

            try:
                # Read framesize bytes
                if self._frame_catcher:  # pragma: no cover - camera thing
                    s, is_new = self._frame_catcher.get_frame()
                else:
                    s = read_n_bytes(self._proc.stdout, framesize)
                    is_new = True
                # Check
                if len(s) != framesize:
                    raise RuntimeError('Frame is %i bytes, but expected %i.' %
                                       (len(s), framesize))
            except Exception as err:
                self._terminate()
                err1 = str(err)
                err2 = self._stderr_catcher.get_text(0.4)
                fmt = 'Could not read frame %i:\n%s\n=== stderr ===\n%s'
                raise CannotReadFrameError(fmt % (self._pos, err1, err2))
            return s, is_new

        def _skip_frames(self, n=1):
            """ Reads and throws away n frames """
            w, h = self._meta['size']
            for i in range(n):
                self._read_frame_data()
            self._pos += n

        def _read_frame(self):
            # Read and convert to numpy array
            w, h = self._meta['size']
            # t0 = time.time()
            s, is_new = self._read_frame_data()
            result = np.fromstring(s, dtype='uint8')
            result = result.reshape((h, w, self._depth))
            # t1 = time.time()
            # print('etime', t1-t0)

            # Store and return
            self._lastread = result
            return result, is_new

    # --

    class Writer(Format.Writer):

        _exe = None

        @classmethod
        def _get_exe(cls):
            cls._exe = cls._exe or get_exe()
            return cls._exe

        def _open(self, fps=10, codec='libx264', bitrate=None,
                  pixelformat='yuv420p', ffmpeg_params=None,
                  input_params=None, output_params=None,
                  ffmpeg_log_level="quiet", quality=5,
                  macro_block_size=16):
            self._exe = self._get_exe()
            # Get local filename
            self._filename = self.request.get_local_filename()
            # Determine pixel format and depth
            self._pix_fmt = None
            # Initialize parameters
            self._proc = None
            self._size = None
            self._cmd = None

        def _close(self):
            if self._proc is None:  # pragma: no cover
                return  # no process
            if self._proc.poll() is not None:
                return  # process already dead
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.wait()
            self._proc = None

        def _append_data(self, im, meta):

            # Get props of image
            size = im.shape[:2]
            depth = 1 if im.ndim == 2 else im.shape[2]

            # Ensure that image is in uint8
            im = image_as_uint(im, bitdepth=8)

            # Set size and initialize if not initialized yet
            if self._size is None:
                map = {1: 'gray', 2: 'gray8a', 3: 'rgb24', 4: 'rgba'}
                self._pix_fmt = map.get(depth, None)
                if self._pix_fmt is None:
                    raise ValueError('Image must have 1, 2, 3 or 4 channels')
                self._size = size
                self._depth = depth
                self._initialize()

            # Check size of image
            if size != self._size:
                raise ValueError('All images in a movie should have same size')
            if depth != self._depth:
                raise ValueError('All images in a movie should have same '
                                 'number of channels')

            assert self._proc is not None  # Check status

            # Write
            try:
                self._proc.stdin.write(im.tostring())
            except IOError as e:
                # Show the command and stderr from pipe
                msg = '{0:}\n\nFFMPEG COMMAND:\n{1:}\n\nFFMPEG STDERR ' \
                      'OUTPUT:\n'.format(e, self._cmd)
                raise IOError(msg)

        def set_meta_data(self, meta):
            raise RuntimeError('The ffmpeg format does not support setting '
                               'meta data.')

        def _initialize(self):
            """ Creates the pipe to ffmpeg. Open the file to write to. """

            # Get parameters
            # Note that H264 is a widespread and very good codec, but if we
            # do not specify a bitrate, we easily get crap results.
            sizestr = "%dx%d" % (self._size[1], self._size[0])
            fps = self.request.kwargs.get('fps', 10)
            default_codec = 'libx264'
            if self._filename.lower().endswith('.wmv'):
                # This is a safer default codec on windows to get videos that
                # will play in powerpoint and other apps. H264 is not always
                # available on windows.
                default_codec = 'msmpeg4'
            codec = self.request.kwargs.get('codec', default_codec)
            bitrate = self.request.kwargs.get('bitrate', None)
            quality = self.request.kwargs.get('quality', 5)
            ffmpeg_log_level = self.request.kwargs.get('ffmpeg_log_level',
                                                       'warning')
            input_params = self.request.kwargs.get('input_params') or []
            output_params = self.request.kwargs.get('output_params') or []
            output_params += self.request.kwargs.get('ffmpeg_params') or []
            # You may need to use -pix_fmt yuv420p for your output to work in
            # QuickTime and most other players. These players only supports
            # the YUV planar color space with 4:2:0 chroma subsampling for
            # H.264 video. Otherwise, depending on your source, ffmpeg may
            # output to a pixel format that may be incompatible with these
            # players. See
            # https://trac.ffmpeg.org/wiki/Encode/H.264#Encodingfordumbplayers
            pixelformat = self.request.kwargs.get('pixelformat', 'yuv420p')

            # Get command
            cmd = [self._exe, '-y',
                   "-f", 'rawvideo',
                   "-vcodec", "rawvideo",
                   '-s', sizestr,
                   '-pix_fmt', self._pix_fmt,
                   '-r', "%.02f" % fps] + input_params
            cmd += ['-i', '-']
            cmd += ['-an',
                    '-vcodec', codec,
                    '-pix_fmt', pixelformat,
                    ]
            # Add fixed bitrate or variable bitrate compression flags
            if bitrate is not None:
                cmd += ['-b:v', str(bitrate)]
            elif quality is not None:  # If None, then we don't add anything
                if quality < 0 or quality > 10:
                    raise ValueError("ffpmeg writer quality parameter out of"
                                     "range. Expected range 0 to 10.")
                quality = 1 - quality / 10.0
                if codec == "libx264":
                    # crf ranges 0 to 51, 51 being worst.
                    quality = int(quality * 51)
                    cmd += ['-crf', str(quality)]  # for h264
                else:  # Many codecs accept q:v
                    # q:v range can vary, 1-31, 31 being worst
                    # But q:v does not always have the same range.
                    # May need a way to find range for any codec.
                    quality = int(quality*30)+1
                    cmd += ['-qscale:v', str(quality)]  # for others

            # Note, for most codecs, the image dimensions must be divisible by
            # 16 the default for the macro_block_size is 16. Check if image is
            # divisible, if not have ffmpeg upsize to nearest size and warn
            # user they should correct input image if this is not desired.
            macro_block_size = self.request.kwargs.get('macro_block_size', 16)
            if macro_block_size is not None and macro_block_size > 1 and \
                    (self._size[1] % macro_block_size > 0 or
                        self._size[0] % macro_block_size > 0):
                out_w = self._size[1]
                if self._size[1] % macro_block_size > 0:
                    out_w += macro_block_size - \
                        (self._size[1] % macro_block_size)
                out_h = self._size[0]
                if self._size[0] % macro_block_size > 0:
                    out_h += macro_block_size - \
                        (self._size[0] % macro_block_size)
                cmd += ['-vf', 'scale={}:{}'.format(out_w, out_h)]
                logging.warning(
                    "IMAGEIO FFMPEG_WRITER WARNING: input image is not"
                    " divisible by macro_block_size={}, resizing from {} "
                    "to {} to ensure video compatibility with most codecs "
                    "and players. To prevent resizing, make your input "
                    "image divisible by the macro_block_size or set the "
                    "macro_block_size to None (risking incompatibility). You "
                    "may also see a FFMPEG warning concerning "
                    "speedloss due to "
                    "data not being aligned.".format(macro_block_size,
                                                     self._size[:2],
                                                     (out_h, out_w)))

            if ffmpeg_log_level:
                # Rather than redirect stderr to a pipe, just set minimal
                # output from ffmpeg by default. That way if there are warnings
                # the user will see them.
                cmd += ['-v', ffmpeg_log_level]
            cmd += output_params
            cmd.append(self._filename)
            self._cmd = " ".join(cmd)  # For showing command if needed
            if any([level in ffmpeg_log_level for level in
                    ("info", "verbose", "debug", "trace")]):
                print("RUNNING FFMPEG COMMAND:", self._cmd, file=sys.stderr)

            # Launch process
            # For Windows, set `shell=True` in sp.Popen to prevent popup
            # of a command line window in frozen applications.
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None,
                                  shell=ISWIN)
            # Warning, directing stderr to a pipe on windows will cause ffmpeg
            # to hang if the buffer is not periodically cleared using
            # StreamCatcher or other means.


def cvsecs(*args):
    """ converts a time to second. Either cvsecs(min, secs) or
    cvsecs(hours, mins, secs).
    """
    if len(args) == 1:
        return args[0]
    elif len(args) == 2:
        return 60*args[0] + args[1]
    elif len(args) == 3:
        return 3600*args[0] + 60*args[1] + args[2]


class FrameCatcher(threading.Thread):
    """ Thread to keep reading the frame data from stdout. This is
    useful when streaming from a webcam. Otherwise, if the user code
    does not grab frames fast enough, the buffer will fill up, leading
    to lag, and ffmpeg can also stall (experienced on Linux). The
    get_frame() method always returns the last available image.
    """

    def __init__(self, file, framesize):
        self._file = file
        self._framesize = framesize
        self._frame = None
        self._frame_is_new = False
        self._bytes_read = 0
        self._lock = threading.RLock()
        threading.Thread.__init__(self)
        self.setDaemon(True)  # do not let this thread hold up Python shutdown
        self._should_stop = False
        self.start()
    
    def stop_me(self):
        self._should_stop = True
    
    def get_frame(self):
        # This runs in the main thread
        while self._frame is None:  # pragma: no cover - an init thing
            time.sleep(0.001)
        with self._lock:
            is_new = self._frame_is_new
            self._frame_is_new = False  # reset
            return self._frame, is_new

    def _read(self, n):
        # This runs in the worker thread
        try:
            return self._file.read(n)
        except ValueError:
            return b''

    def run(self):
        # This runs in the worker thread
        framesize = self._framesize

        while not self._should_stop:
            time.sleep(0)  # give control to other threads
            s = self._read(framesize)
            while len(s) < framesize:
                need = framesize - len(s)
                part = self._read(need)
                if not part:
                    break
                s += part
                self._bytes_read += len(part)
            # Stop?
            if not s:
                return
            # Store frame
            with self._lock:
                # Lock ensures that _frame and frame_is_new remain consistent
                self._frame = s
                self._frame_is_new = True
            # NOTE: could add a threading.Condition to facilitate blocking


class StreamCatcher(threading.Thread):
    """ Thread to keep reading from stderr so that the buffer does not
    fill up and stalls the ffmpeg process. On stderr a message is send
    on every few frames with some meta information. We only keep the
    last ones.
    """

    def __init__(self, file):
        self._file = file
        self._header = ''
        self._lines = []
        self._remainder = b''
        threading.Thread.__init__(self)
        self.setDaemon(True)  # do not let this thread hold up Python shutdown
        self._should_stop = False
        self.start()

    def stop_me(self):
        self._should_stop = True
    
    @property
    def header(self):
        """ Get header text. Empty string if the header is not yet parsed.
        """
        return self._header

    def get_text(self, timeout=0):
        """ Get the whole text printed to stderr so far. To preserve
        memory, only the last 50 to 100 frames are kept.

        If a timeout is givem, wait for this thread to finish. When
        something goes wrong, we stop ffmpeg and want a full report of
        stderr, but this thread might need a tiny bit more time.
        """

        # Wait?
        if timeout > 0:
            etime = time.time() + timeout
            while self.isAlive() and time.time() < etime:  # pragma: no cover
                time.sleep(0.01)
        # Return str
        lines = b'\n'.join(self._lines)
        return self._header + '\n' + lines.decode('utf-8', 'ignore')

    def run(self):
        
        # Create ref here so it still exists even if Py is shutting down
        limit_lines_local = limit_lines
        
        while not self._should_stop:
            time.sleep(0.001)
            # Read one line. Detect when closed, and exit
            try:
                line = self._file.read(20)
            except ValueError:  # pragma: no cover
                break
            if not line:
                break
            # Process to divide in lines
            line = line.replace(b'\r', b'\n').replace(b'\n\n', b'\n')
            lines = line.split(b'\n')
            lines[0] = self._remainder + lines[0]
            self._remainder = lines.pop(-1)
            # Process each line
            self._lines.extend(lines)
            if not self._header:
                if get_output_video_line(self._lines):
                    header = b'\n'.join(self._lines)
                    self._header += header.decode('utf-8', 'ignore')
            elif self._lines:
                self._lines = limit_lines_local(self._lines)


def parse_device_names(ffmpeg_output):
    """ Parse the output of the ffmpeg -list-devices command"""
    device_names = []
    in_video_devices = False
    for line in ffmpeg_output.splitlines():
        if line.startswith('[dshow'):
            logging.debug(line)
            line = line.split(']', 1)[1].strip()
            if in_video_devices and line.startswith('"'):
                device_names.append(line[1:-1])
            elif 'video devices' in line:
                in_video_devices = True
            elif 'devices' in line:
                # set False for subsequent "devices" sections
                in_video_devices = False
    return device_names


def parse_ffmpeg_info(text):
    meta = {}
    
    if isinstance(text, list):
        lines = text
    else:
        lines = text.splitlines()
    
    # Get version
    ver = lines[0].split('version', 1)[-1].split('Copyright')[0]
    meta['ffmpeg_version'] = ver.strip() + ' ' + lines[1].strip()

    # get the output line that speaks about video
    videolines = [l for l in lines if l.lstrip().startswith('Stream ')
                  and ' Video: ' in l]
    line = videolines[0]
    
    # get the frame rate.
    # matches can be empty, see #171, assume nframes = inf
    # the regexp omits values of "1k tbr" which seems a specific edge-case #262
    # it seems that tbr is generally to be preferred #262
    matches = re.findall(" ([0-9]+\.?[0-9]*) (tbr|fps)", line)
    fps = 0
    matches.sort(key=lambda x: x[1] == 'tbr', reverse=True)
    if matches:
        fps = float(matches[0][0].strip())
    meta['fps'] = fps

    # get the size of the original stream, of the form 460x320 (w x h)
    match = re.search(" [0-9]*x[0-9]*(,| )", line)
    parts = line[match.start():match.end()-1].split('x')
    meta['source_size'] = tuple(map(int, parts))

    # get the size of what we receive, of the form 460x320 (w x h)
    line = videolines[-1]  # Pipe output
    match = re.search(" [0-9]*x[0-9]*(,| )", line)
    parts = line[match.start():match.end()-1].split('x')
    meta['size'] = tuple(map(int, parts))

    # Check the two sizes
    if meta['source_size'] != meta['size']:
        logging.warning('Warning: the frame size for reading %s is '
                        'different from the source frame size %s.' %
                        (meta['size'], meta['source_size']))

    # get duration (in seconds)
    line = [l for l in lines if 'Duration: ' in l][0]
    match = re.search(" [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9]",
                      line)
    if match is not None:
        hms = map(float, line[match.start()+1:match.end()].split(':'))
        meta['duration'] = cvsecs(*hms)
    
    return meta


def get_output_video_line(lines):
    """Get the line that defines the video stream that ffmpeg outputs,
    and which we read.
    """
    in_output = False
    for line in lines:
        sline = line.lstrip()
        if sline.startswith(b'Output '):
            in_output = True
        elif in_output:
            if sline.startswith(b'Stream ') and b' Video:' in sline:
                return line


# Register. You register an *instance* of a Format class.
format = FfmpegFormat('ffmpeg', 'Many video formats and cameras (via ffmpeg)',
                      '.mov .avi .mpg .mpeg .mp4 .mkv .wmv', 'I')
formats.add_format(format)
