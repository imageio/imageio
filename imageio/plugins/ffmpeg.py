# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

Code inspired/based on code from moviepy: https://github.com/Zulko/moviepy/
by Zulko

"""

import os
import re
import time
import subprocess as sp

import numpy as np

import imageio
from imageio import formats
from imageio.base import Format

FFMPEG_BINARY = '/home/almar/Videos/ffmpeg'

class FfmpegFormat(Format):
    """ The ffmpeg format provides reading and writing for a wide range of
    movie formats such as .avi, .mpeg, .mp4, etc.
    """
    
    def _can_read(self, request):
        # The request object has:
        # request.filename: the filename
        # request.firstbytes: the first 256 bytes of the file.
        # request.expect: what kind of data the user expects
        # request.kwargs: the keyword arguments specified by the user
        if (request.expect is not None) and request.expect != imageio.EXPECT_MIM:
            return False
        ext = os.path.splitext(request.filename)[1].lower()
        if ext in '.avi .mpg .mpeg .mp4':
            return True
    
    def _can_save(self, request):
        return self._can_read(request)
    
    
    class Reader(Format.Reader):
    
        def _open(self):
            # Get local filename
            self._filename = self.request.get_local_filename()
            # Determine pixel format and depth
            self._pix_fmt = self.request.kwargs.get('pix_fmt', 'rgb24')
            self._depth = 4 if self._pix_fmt=="rgba" else 3
            # Initialize parameters
            self._proc = None
            self._pos = -1
            self._meta = {'nframes': float('inf')}
            self._load_infos()
            self._lastread = None
            # Start ffmpeg subprocess
            self._initialize()
        
        def _close(self):
            # Close subprocess
            if self._proc is not None:
                self._proc.terminate()
                for std in (self._proc.stdin, self._proc.stdout, self._proc.stderr):
                    std.close()
                self._proc = None
        
        def _get_length(self):
            return self._meta['nframes']
        
        def _get_data(self, index):
            """ Reads a frame at index. Note for coders: getting an
            arbitrary frame in the video with ffmpeg can be painfully
            slow if some decoding has to be done. This function tries
            to avoid fectching arbitrary frames whenever possible, by
            moving between adjacent frames. """
           
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
            
            cmd = [ FFMPEG_BINARY, '-i', self._filename,
                    '-f', 'image2pipe',
                    "-pix_fmt", self._pix_fmt,
                    '-vcodec', 'rawvideo', '-']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        
        
        def _load_infos(self):
            """ reads the FFMPEG info on the file and sets size fps
            duration and nframes. """
            # open the file in a pipe, provoke an error, read output
            proc = sp.Popen([FFMPEG_BINARY,"-i",self._filename, "-"],
                    stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            proc.stdout.readline()
            proc.terminate()
            infos = proc.stderr.read().decode('utf-8')
            if self.request.kwargs.get('print_infos', False):
                # print the whole info text returned by FFMPEG
                print(infos)
                print('-'*80)
            lines = infos.splitlines()
            if "No such file or directory" in lines[-1]:
                raise IOError("%s not found ! Wrong path ?" % self._filename)
            
            # get the output line that speaks about video
            line = [l for l in lines if ' Video: ' in l][0]
            
            # get the size, of the form 460x320 (w x h)
            match = re.search(" [0-9]*x[0-9]*(,| )",line)
            self._meta['size'] = tuple(map(int,line[match.start():match.end()-1].split('x')))
            
            # get the frame rate
            match = re.search("( [0-9]*.| )[0-9]* (tbr|fps)",line)
            self._meta['fps'] = fps = float(line[match.start():match.end()].split(' ')[1])
            
            # get duration (in seconds)
            line = [l for l in lines if 'Duration: ' in l][0]
            match = re.search(" [0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9]",line)
            hms = map(float,line[match.start()+1:match.end()].split(':'))
            self._meta['duration'] = duration = cvsecs(*hms)
            self._meta['nframes'] = int(duration*fps)
        
        def _skip_frames(self, n=1):
            """ Reads and throws away n frames """
            w, h = self._meta['size']
            for i in range(n):
                self._proc.stdout.read(self._depth*w*h)
                self._proc.stdout.flush()
            self._pos += n
        
        def _read_frame(self):
            w, h = self._meta['size']
            if self._proc is None:
                raise RuntimeError('No active ffmpeg process, maybe the reader is closed?')
            try:
                # Normally, the readr should not read after the last frame...
                # if it does, raise an error.
                t0 = time.time()
                s = self._proc.stdout.read(self._depth*w*h)
                result = np.fromstring(s,
                                dtype='uint8').reshape((h,w,len(s)/(w*h)))
                t1 = time.time()
                #print('etime', t1-t0)
                self._proc.stdout.flush()
            except Exception:
                if self._proc is not None:
                    self._proc.terminate()
                    serr = self._proc.stderr.read()  # todo: this can block
                    print("Could not read frame. stderr: %s" % serr)
                raise
            # Store and return
            self._lastread = result
            return result
        
        def _reinitialize(self, index=0):
            """ Restarts the reading, starts at an arbitrary location
            (!! SLOW !!) """
            self._close()
            if index == 0:
                self._initialize()
            else:
                starttime = index / self._meta['fps']
                offset = min(1, starttime)
                cmd = [ FFMPEG_BINARY, '-ss',"%.03f"%(starttime-offset),
                        '-i', self._filename,
                        '-ss', "%.03f"%offset,
                        '-f', 'image2pipe',
                        "-pix_fmt", self._pix_fmt,
                        '-vcodec','rawvideo', '-']
                self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                      stdout=sp.PIPE, stderr=sp.PIPE)
    
    
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
            sizestr = "%dx%d" % (self._size[1], self._size[0])
            fps = self.request.kwargs.get('fps', 10)
            codec = self.request.kwargs.get('codec', 'libx264') # libx264 mpeg4 msmpeg4v2
            bitrate = self.request.kwargs.get('bitrate', 400000)
            
            # Get command
            cmd = [FFMPEG_BINARY, '-y',
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


# Register. You register an *instance* of a Format class.
format = FfmpegFormat('ffmpeg', 'Many video formats via ffmpeg.', 
                      '.avi .mpg .mpeg .mp4')
formats.add_format(format)
