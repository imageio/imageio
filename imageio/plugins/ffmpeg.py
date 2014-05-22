# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

Code inspired/based on code from moviepy: https://github.com/Zulko/moviepy/
by Zulko

"""

import sys
import os
import re
import time
import threading
import subprocess as sp

import numpy as np

import imageio
from imageio import formats
from imageio.base import Format

# todo: select an exe!
FFMPEG_EXE = os.path.join(os.path.dirname(imageio.__file__), 'lib', 'ffmpeg')
if sys.platform.startswith('win'):
    FFMPEG_EXE += '.exe'


if sys.platform.startswith('win'):
    CAM_FORMAT = 'dshow'  # dshow or vfwcap
elif sys.platform.startswith('linux'):
    CAM_FORMAT ='video4linux2'
elif sys.platform.startswith('darwin'):
    CAM_FORMAT ='??'
else:
    CAM_FORMAT = 'unknown-cam-format'


class FfmpegFormat(Format):
    """ The ffmpeg format provides reading and writing for a wide range
    of movie formats such as .avi, .mpeg, .mp4, etc. And also to read
    streams from webcams and USB cameras. 
    
    To read from camera streams, supply "<video0>" as the filename,
    where the "0" can be replaced with any index of cameras known to
    the system.
    
    Keyword arguments for reading
    -----------------------------
    loop : bool
        If True, the video will rewind as soon as a frame is requested
        beyond the last frame. Otherwise, IndexError is raised.
    size : str
        The frame size (i.e. resolution) to read the images, e.g. "640x480". 
        For camera streams, this allows setting the capture resolution. 
        For normal video data, ffmpeg will rescale the data.
    pixelformat : str
        The pixel format for the camera to use (e.g. "yuyv422" or
        "gray"). The camera needs to support the format in order for
        this to take effect. Note that the images produced by this
        reader are always rgb8.
    
    """
    
    def _can_read(self, request):
        # The request object has:
        # request.filename: the filename
        # request.firstbytes: the first 256 bytes of the file.
        # request.expect: what kind of data the user expects
        # request.kwargs: the keyword arguments specified by the user
        if (request.expect is not None) and request.expect != imageio.EXPECT_MIM:
            return False
        
        # Read from video stream?
        # Note that we could write the _video flag here, but a user might
        # select this format explicitly (and this code is not run)
        if request.filename in ['<video%i>' % i for i in range(10)]:
            return True
        
        # Read from file that we know?
        ext = os.path.splitext(request.filename)[1].lower()
        if ext in '.avi .mpg .mpeg .mp4':
            return True
    
    def _can_save(self, request):
        return self._can_read(request)
    
    
    class Reader(Format.Reader):
        
        def _get_cam_inputname(self, index):
            if sys.platform.startswith('linux'):
                return '/dev/' + self.request._video[1:-1]
            
            elif sys.platform.startswith('win'):
                # Ask ffmpeg for list of dshow device names
                cmd = [FFMPEG_EXE, '-list_devices', 'true',
                                '-f', CAM_FORMAT, '-i', 'dummy']
                proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
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
            else:
                return '??'
        
        def _open(self, loop=False, size=None, pixelformat=None):
            # Process input args
            self._arg_loop = loop
            self._arg_size = size
            self._arg_pxelformat = pixelformat
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
            self._depth = 4 if self._pix_fmt=="rgba" else 3
            # Initialize parameters
            self._proc = None
            self._pos = -1
            self._meta = {'nframes': float('inf'), 'nframes': float('inf')}
            self._lastread = None
            # Start ffmpeg subprocess and get meta information
            self._initialize()
            self._load_infos()
            
            # For cameras, create thread that keeps reading the images
            self._frame_catcher = None
            if self.request._video:
                w, h = self._meta['size']
                framesize = self._depth * w * h
                self._frame_catcher = FrameCatcher(self._proc.stdout, framesize)
        
        def _close(self):
            self._terminate()
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
        
        def _get_next_data(self):
            result = self._read_frame()
            self._pos += 1
            return result, {}
        
        
        def _initialize(self):
            """ Opens the file, creates the pipe. """
            # Create input args
            if self.request._video:
                iargs = ['-f', CAM_FORMAT]
                if self._arg_pxelformat:
                    iargs.extend(['-pix_fmt', self._arg_pxelformat])
                if self._arg_size:
                    iargs.extend(['-s', self._arg_size])
            else:
                iargs = []
            # Output args, for writing to pipe
            oargs = ['-f', 'image2pipe',
                     '-pix_fmt', self._pix_fmt,
                     '-vcodec', 'rawvideo']
            if 'size' in self.request.kwargs:
                oargs.extend(['-s', self.request.kwargs['size']])
            # Create process
            cmd = [FFMPEG_EXE] + iargs + ['-i', self._filename] + oargs + ['-']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
            # Create thread that keeps reading from stderr
            self._stderr_catcher = StreamCatcher(self._proc.stderr)
        
        
        def _reinitialize(self, index=0):
            """ Restarts the reading, starts at an arbitrary location
            (!! SLOW !!) """
            if self.request._video:
                raise RuntimeError('No random access when streaming from camera.')
            self._close()
            if index == 0:
                self._initialize()
            else:
                starttime = index / self._meta['fps']
                offset = min(1, starttime)
                # Create input args -> start time
                iargs = ['-ss', "%.03f"%(starttime-offset)]
                # Output args, for writing to pipe
                oargs = ['-f', 'image2pipe',
                        '-pix_fmt', self._pix_fmt,
                        '-vcodec', 'rawvideo']
                if 'size' in self.request.kwargs:
                    oargs.extend(['-s', self.request.kwargs['size']])
                # Create process
                cmd = [FFMPEG_EXE] + iargs + ['-i', self._filename] + oargs + ['-']
                self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                      stdout=sp.PIPE, stderr=sp.PIPE)
                # Create thread that keeps reading from stderr
                self._stderr_catcher = StreamCatcher(self._proc.stderr)
        
        
        def _terminate(self):
            """ Terminate the sub process.
            """
            # Check
            if self._proc is None:
                return  # no process
            if self._proc.poll() is not None:
                return  # process already dead
            # Close, terminate
            for std in (self._proc.stdin, self._proc.stdout, self._proc.stderr):
                std.close()
            self._proc.terminate()
            # Wait for it to close (but do not get stuck)
            etime = time.time() + 1.0
            while time.time() < etime:
                time.sleep(0.01)
                if self._proc.poll() is not None:
                    break
        
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
                err2 = self._stderr_catcher.get_text(0.2)
                fmt = 'Could not load meta information\n=== stderr ===\n%s'
                raise RuntimeError(fmt % err2)
            
            if self.request.kwargs.get('print_infos', False):
                # print the whole info text returned by FFMPEG
                print(infos)
                print('-'*80)
            lines = infos.splitlines()
            if "No such file or directory" in lines[-1]:
                if self.request._video:
                    raise IOError("Could not open steam %s." % self._filename)
                else:
                    raise IOError("%s not found! Wrong path?" % self._filename)
            
            # Get version
            ver = lines[0].split('version', 1)[-1].split('Copyright')[0]
            self._meta['ffmpeg_version'] = ver.strip() + ' ' + lines[1].strip()
            
            # get the output line that speaks about video
            videolines = [l for l in lines if ' Video: ' in l]
            line = videolines[0]
            
            # get the frame rate
            match = re.search("( [0-9]*.| )[0-9]* (tbr|fps)",line)
            self._meta['fps'] = fps = float(line[match.start():match.end()].split(' ')[1])
            
            # get the size of the original stream, of the form 460x320 (w x h)
            match = re.search(" [0-9]*x[0-9]*(,| )", line)
            self._meta['source_size'] = tuple(map(int,line[match.start():match.end()-1].split('x')))
            
            # get the size of what we receive, of the form 460x320 (w x h)
            line = videolines[-1]  # Pipe output
            match = re.search(" [0-9]*x[0-9]*(,| )", line)
            self._meta['size'] = tuple(map(int,line[match.start():match.end()-1].split('x')))
            
            # Check the two sizes
            if self._meta['source_size'] != self._meta['size']:
                print('Warning: the frame size for reading %s is different '
                      'from the source frame size %s.' % 
                      (self._meta['size'], self._meta['source_size'], ))
            
            # get duration (in seconds)
            line = [l for l in lines if 'Duration: ' in l][0]
            match = re.search(" [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9]",line)
            if match is not None:
                hms = map(float,line[match.start()+1:match.end()].split(':'))
                self._meta['duration'] = duration = cvsecs(*hms)
                self._meta['nframes'] = int(duration*fps)
        
        def _read_frame_data(self):
            # Init and check
            w, h = self._meta['size']
            framesize = self._depth * w * h
            if self._proc is None:
                raise RuntimeError('No active ffmpeg process, maybe the reader is closed?')
            
            try:
                # Read framesize bytes
                if self._frame_catcher:
                    s = self._frame_catcher.get_frame()
                else:
                    s = self._proc.stdout.read(framesize)
                    while len(s) < framesize:
                        need = framesize - len(s)
                        part = self._proc.stdout.read(need)
                        if not part:
                            break
                        s += part
                # Check
                assert len(s) == framesize
            except Exception as err:
                if not s:
                    raise IndexError('Stream ended')
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
            t0 = time.time()
            s = self._read_frame_data()
            result = np.fromstring(s, dtype='uint8').reshape((h,w,self._depth))
            t1 = time.time()
            #print('etime', t1-t0)
            
            # Store and return
            self._lastread = result
            return result
    
    
    class Writer(Format.Writer):
        
        def _open(self):        
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
            im = im.astype(np.uint8, copy=False)
            
            # Set size and initialize if not initialized yet
            if self._size is None:
                self._size = size
                self._depth = depth
                map = {1:'gray', 2:'gray8a', 3:'rgb24', 4:'rgba'}
                self._pix_fmt = map.get(depth, None)
                if self._pix_fmt is None:
                    raise ValueError('Image data must have 1, 2, 3 or 4 channels.')
                self._initialize()
            
            # Check size of image
            if size != self._size:
                raise ValueError('All images in a movie should have the same size.')
            if depth != self._depth:
                raise ValueError('All images in a movie should have the same number of channels.')
            
            # Check status
            if self._proc is None:
                raise RuntimeError('No active ffmpeg process, maybe writer is closed?')
            
            # Write
            self._proc.stdin.write(im.tostring())
        
        def set_meta_data(self, meta):
            raise RuntimeError('The ffmpeg format does not support setting meta data.')
        
        def _initialize(self):
            """ Creates the pipe to ffmpeg. Open the file to write to. """
            
            # Get parameters
            # Note that H264 is a widespread and very good codec, but if we
            # do not specify a bitrate, we easily get crap results.
            sizestr = "%dx%d" % (self._size[1], self._size[0])
            fps = self.request.kwargs.get('fps', 10)
            codec = self.request.kwargs.get('codec', 'libx264') # libx264 mpeg4 msmpeg4v2
            bitrate = self.request.kwargs.get('bitrate', 400000)
            
            # Get command
            cmd = [FFMPEG_EXE, '-y',
                "-f", 'rawvideo',
                "-vcodec", "rawvideo",
                '-s', sizestr,
                '-pix_fmt', self._pix_fmt,
                '-r', "%.02f" % fps,
                '-i', '-', '-an',
                '-vcodec', codec] 
            cmd += ['-b', str(bitrate)] if (bitrate!=None) else [] 
            cmd += ['-r', "%d" % fps, self._filename]
            
            # Launch process
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)


def cvsecs(*args):
    """ converts a time to second. Either cvsecs(min,secs) or
    cvsecs(hours,mins,secs).
    """
    if len(args) == 1:
        return args[0]
    elif len(args) == 2:
        return 60*args[0]+args[1]
    elif len(args) ==3:
        return 3600*args[0]+60*args[1]+args[2]



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
        #self._lock = threading.RLock()
        threading.Thread.__init__(self)
        self.setDaemon(True)  # do not let this thread hold up Python shutdown
        self.start()
    
    def get_frame(self):
        while self._frame is None:
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
            while self.isAlive() and time.time() < etime:
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
            except ValueError:
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
            # Check lines
            N = 32
            if len(self._lines) > 2*N:
                self._lines = [b'... showing only last few lines ...'] + self._lines[N:]
            


# Register. You register an *instance* of a Format class.
format = FfmpegFormat('ffmpeg', 'Many video formats and cameras via ffmpeg.', 
                      '.avi .mpg .mpeg .mp4')
formats.add_format(format)
