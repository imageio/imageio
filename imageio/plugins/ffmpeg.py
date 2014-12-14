# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
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
import struct
import subprocess as sp

import numpy as np

from .. import formats
from ..core import (Format, get_remote_file, string_types, read_n_bytes, 
                    image_as_uint8)


def get_exe():
    """ Get ffmpeg exe
    """
    NBYTES = struct.calcsize('P') * 8
    if sys.platform.startswith('linux'):
        fname = 'ffmpeg.linux%i' % NBYTES
    elif sys.platform.startswith('win'):
        fname = 'ffmpeg.win32.exe'
    elif sys.platform.startswith('darwin'):
        fname = 'ffmpeg.osx.snowleopardandabove'
    else:  # pragma: no cover
        fname = 'ffmpeg'  # hope for the best
    #
    FFMPEG_EXE = 'ffmpeg'
    if fname:
        FFMPEG_EXE = get_remote_file('ffmpeg/' + fname)
        os.chmod(FFMPEG_EXE, os.stat(FFMPEG_EXE).st_mode | stat.S_IEXEC)  # exe
    return FFMPEG_EXE

# Get camera format
if sys.platform.startswith('win'):
    CAM_FORMAT = 'dshow'  # dshow or vfwcap
elif sys.platform.startswith('linux'):
    CAM_FORMAT = 'video4linux2'
elif sys.platform.startswith('darwin'):
    CAM_FORMAT = '??'
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
    
    Parameters for reading
    ----------------------
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
    print_info : bool
        Print information about the video file as reported by ffmpeg.
    
    Parameters for saving
    ---------------------
    fps : scalar
        The number of frames per second. Default 10.
    codec : str
        the video codec to use. Default 'libx264', which represents the
        widely available mpeg4.
    bitrate : int
        A measure for quality. Default 400000
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
        for ext in self.extensions:
            if request.filename.endswith('.' + ext):
                return True
    
    def _can_save(self, request):
        if request.mode[1] in (self.modes + '?'):
            for ext in self.extensions:
                if request.filename.endswith('.' + ext):
                    return True
    
    # --
    
    class Reader(Format.Reader):
        
        def _get_cam_inputname(self, index):
            if sys.platform.startswith('linux'):
                return '/dev/' + self.request._video[1:-1]
            
            elif sys.platform.startswith('win'):
                # Ask ffmpeg for list of dshow device names
                cmd = [self._exe, '-list_devices', 'true',
                       '-f', CAM_FORMAT, '-i', 'dummy']
                proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, 
                                stderr=sp.PIPE)
                proc.stdout.readline()
                proc.terminate()
                infos = proc.stderr.read().decode('utf-8')
                # Parse the result
                device_names = []
                in_video_devices = False
                for line in infos.splitlines():
                    if line.startswith('[dshow'):
                        line = line.split(']', 1)[1].strip()
                        if line.startswith('"'):
                            if in_video_devices:
                                device_names.append(line[1:-1])
                        elif 'video devices' in line:
                            in_video_devices = True
                        else:
                            in_video_devices = False
                # Return device name at index
                try:
                    name = device_names[index]
                except IndexError:
                    raise IndexError('No ffdshow camera at index %i.' % index)
                return 'video=%s' % name
            else:  # pragma: no cover
                return '??'
        
        def _open(self, loop=False, size=None, pixelformat=None, 
                  print_info=False):
            # Get exe
            self._exe = get_exe()
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
            self._meta = {'plugin': 'ffmpeg', 
                          'nframes': float('inf'), 'nframes': float('inf')}
            self._lastread = None
            # Start ffmpeg subprocess and get meta information
            self._initialize()
            self._load_infos()
            
            # For cameras, create thread that keeps reading the images
            self._frame_catcher = None
            if self.request._video:
                w, h = self._meta['size']
                framesize = self._depth * w * h
                self._frame_catcher = FrameCatcher(self._proc.stdout, 
                                                   framesize)
        
        def _close(self):
            self._terminate(0.05)  # Short timeout
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
                    index = index % self._meta['nframes']
            
            if index == self._pos:
                return self._lastread, {}
            elif index < 0:
                raise IndexError('Frame index must be > 0') 
            elif index >= self._meta['nframes']:
                raise IndexError('Reached end of video')
            else:
                if (index < self._pos) or (index > self._pos+100):
                    self._reinitialize(index)
                else:
                    self._skip_frames(index-self._pos-1)
                result = self._read_frame()
                self._pos = index
                return result, {}
        
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
            # Create process
            cmd = [self._exe] + iargs + ['-i', self._filename] + oargs + ['-']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
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
                offset = min(1, starttime)
                # Create input args -> start time
                iargs = ['-ss', "%.03f" % (starttime-offset)]
                # Output args, for writing to pipe
                oargs = ['-f', 'image2pipe',
                         '-pix_fmt', self._pix_fmt,
                         '-vcodec', 'rawvideo']
                oargs.extend(['-s', self._arg_size] if self._arg_size else [])
                # Create process
                cmd = [self._exe]
                cmd += iargs + ['-i', self._filename] + oargs + ['-']
                self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                      stdout=sp.PIPE, stderr=sp.PIPE)
                # Create thread that keeps reading from stderr
                self._stderr_catcher = StreamCatcher(self._proc.stderr)
        
        def _terminate(self, timeout=1.0):
            """ Terminate the sub process.
            """
            # Check
            if self._proc is None:  # pragma: no cover
                return  # no process
            if self._proc.poll() is not None:
                return  # process already dead
            # Terminate process
            self._proc.terminate()
            # Wait for it to close (but do not get stuck)
            etime = time.time() + timeout
            while time.time() < etime:
                time.sleep(0.01)
                if self._proc.poll() is not None:
                    break
        
#         def _close_streams(self):
#             for std in (self._proc.stdin, 
#                         self._proc.stdout, 
#                         self._proc.stderr):
#                 try:
#                     std.close()
#                 except Exception:  # pragma: no cover
#                     pass
        
        def _load_infos(self):
            """ reads the FFMPEG info on the file and sets size fps
            duration and nframes. """
            
            # Wait for the catcher to get the meta information
            etime = time.time() + 4.0
            while (not self._stderr_catcher.header) and time.time() < etime:
                time.sleep(0.01)
            
            # Check whether we have the information
            infos = self._stderr_catcher.header
            if not infos:
                self._terminate()
                if self.request._video:
                    raise IndexError('No video4linux camera at %s.' % 
                                     self.request._video)
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
            
            # Get version
            ver = lines[0].split('version', 1)[-1].split('Copyright')[0]
            self._meta['ffmpeg_version'] = ver.strip() + ' ' + lines[1].strip()
            
            # get the output line that speaks about video
            videolines = [l for l in lines if ' Video: ' in l]
            line = videolines[0]
            
            # get the frame rate
            match = re.search("( [0-9]*.| )[0-9]* (tbr|fps)", line)
            fps = float(line[match.start():match.end()].split(' ')[1])
            self._meta['fps'] = fps
            
            # get the size of the original stream, of the form 460x320 (w x h)
            match = re.search(" [0-9]*x[0-9]*(,| )", line)
            parts = line[match.start():match.end()-1].split('x')
            self._meta['source_size'] = tuple(map(int, parts))
            
            # get the size of what we receive, of the form 460x320 (w x h)
            line = videolines[-1]  # Pipe output
            match = re.search(" [0-9]*x[0-9]*(,| )", line)
            parts = line[match.start():match.end()-1].split('x')
            self._meta['size'] = tuple(map(int, parts))
            
            # Check the two sizes
            if self._meta['source_size'] != self._meta['size']:
                print('Warning: the frame size for reading %s is different '
                      'from the source frame size %s.' % 
                      (self._meta['size'], self._meta['source_size'], ))
            
            # get duration (in seconds)
            line = [l for l in lines if 'Duration: ' in l][0]
            match = re.search(" [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9]",
                              line)
            if match is not None:
                hms = map(float, line[match.start()+1:match.end()].split(':'))
                self._meta['duration'] = duration = cvsecs(*hms)
                self._meta['nframes'] = int(duration*fps)
        
        def _read_frame_data(self):
            # Init and check
            w, h = self._meta['size']
            framesize = self._depth * w * h
            assert self._proc is not None
            
            try:
                # Read framesize bytes
                if self._frame_catcher:  # pragma: no cover - camera thing
                    s = self._frame_catcher.get_frame()
                else:
                    s = read_n_bytes(self._proc.stdout, framesize)
                # Check
                assert len(s) == framesize
            except Exception as err:
                self._terminate()
                err1 = str(err)
                err2 = self._stderr_catcher.get_text(0.4)
                fmt = 'Could not read frame:\n%s\n=== stderr ===\n%s'
                raise RuntimeError(fmt % (err1, err2))
            return s
        
        def _skip_frames(self, n=1):
            """ Reads and throws away n frames """
            w, h = self._meta['size']
            for i in range(n):
                self._read_frame_data()
            self._pos += n
        
        def _read_frame(self):
            # Read and convert to numpy array
            w, h = self._meta['size']
            #t0 = time.time()
            s = self._read_frame_data()
            result = np.fromstring(s, dtype='uint8')
            result = result.reshape((h, w, self._depth))
            #t1 = time.time()
            #print('etime', t1-t0)
            
            # Store and return
            self._lastread = result
            return result
    
    # --
    
    class Writer(Format.Writer):
        
        def _open(self, fps=10, codec='libx264', bitrate=400000):
            self._exe = get_exe()
            # Get local filename
            self._filename = self.request.get_local_filename()
            # Determine pixel format and depth
            self._pix_fmt = None
            # Initialize parameters
            self._proc = None
            self._size = None
        
        def _close(self):
            # Close subprocess
            if self._proc is not None:
                self._proc.stdin.close()
                self._proc.stderr.close()
                self._proc.wait()
                self._proc = None
        
        def _append_data(self, im, meta):
            
            # Get props of image
            size = im.shape[:2]
            depth = 1 if im.ndim == 2 else im.shape[2]
            
            # Ensure that image is in uint8
            im = image_as_uint8(im)
            
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
            self._proc.stdin.write(im.tostring())
        
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
            codec = self.request.kwargs.get('codec', 'libx264')
            bitrate = self.request.kwargs.get('bitrate', 400000)
            
            # Get command
            cmd = [self._exe, '-y',
                   "-f", 'rawvideo',
                   "-vcodec", "rawvideo",
                   '-s', sizestr,
                   '-pix_fmt', self._pix_fmt,
                   '-r', "%.02f" % fps,
                   '-i', '-', '-an',
                   '-vcodec', codec] 
            cmd += ['-b', str(bitrate)] if (bitrate is not None) else [] 
            cmd += ['-r', "%d" % fps, self._filename]
            
            # Launch process
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)


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


def limit_lines(lines, N=32):
    """ When number of lines > 2*N, reduce to N.
    """
    if len(lines) > 2*N:
        lines = [b'... showing only last few lines ...'] + lines[-N:]
    return lines


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
        self._bytes_read = 0
        #self._lock = threading.RLock()
        threading.Thread.__init__(self)
        self.setDaemon(True)  # do not let this thread hold up Python shutdown
        self.start()
    
    def get_frame(self):
        while self._frame is None:  # pragma: no cover - an init thing
            time.sleep(0.001)
        return self._frame
    
    def _read(self, n):
        try:
            return self._file.read(n)
        except ValueError:
            return b''
    
    def run(self):
        framesize = self._framesize
        
        while True:
            time.sleep(0.001)
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
            self._frame = s


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
        self.start()
    
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
                time.sleep(0.025)
        # Return str
        lines = b'\n'.join(self._lines)
        return self._header + '\n' + lines.decode('utf-8', 'ignore')
    
    def run(self):
        while True:
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
            for line in lines:
                self._lines.append(line)
                if line.startswith(b'Stream mapping'):
                    header = b'\n'.join(self._lines)
                    self._header += header.decode('utf-8', 'ignore')
                    self._lines = []
            self._lines = limit_lines(self._lines)


# Register. You register an *instance* of a Format class.
format = FfmpegFormat('ffmpeg', 'Many video formats and cameras (via ffmpeg)', 
                      '.mov .avi .mpg .mpeg .mp4 .mkv', 'I')
formats.add_format(format)
