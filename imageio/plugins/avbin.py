# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin for reading videos via AvBin
"""

from __future__ import absolute_import, print_function, division

import numpy as np
import ctypes
import sys

from imageio import formats
from imageio.core import Format, get_platform, get_remote_file


AVBIN_RESULT_ERROR = -1
AVBIN_RESULT_OK = 0
AVbinResult = ctypes.c_int


def AVbinResult(x):
    if x != AVBIN_RESULT_OK:
        raise RuntimeError
    return x

AVBIN_STREAM_TYPE_UNKNOWN = 0
AVBIN_STREAM_TYPE_VIDEO = 1
AVBIN_STREAM_TYPE_AUDIO = 2
AVbinStreamType = ctypes.c_int

AVBIN_SAMPLE_FORMAT_U8 = 0
AVBIN_SAMPLE_FORMAT_S16 = 1
AVBIN_SAMPLE_FORMAT_S24 = 2
AVBIN_SAMPLE_FORMAT_S32 = 3
AVBIN_SAMPLE_FORMAT_FLOAT = 4
AVbinSampleFormat = ctypes.c_int

AVBIN_LOG_QUIET = -8
AVBIN_LOG_PANIC = 0
AVBIN_LOG_FATAL = 8
AVBIN_LOG_ERROR = 16
AVBIN_LOG_WARNING = 24
AVBIN_LOG_INFO = 32
AVBIN_LOG_VERBOSE = 40
AVBIN_LOG_DEBUG = 48
AVbinLogLevel = ctypes.c_int

AVbinFileP = ctypes.c_void_p
AVbinStreamP = ctypes.c_void_p

Timestamp = ctypes.c_int64


class AVbinFileInfo(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('n_streams', ctypes.c_int),
        ('start_time', Timestamp),
        ('duration', Timestamp),
        ('title', ctypes.c_char * 512),
        ('author', ctypes.c_char * 512),
        ('copyright', ctypes.c_char * 512),
        ('comment', ctypes.c_char * 512),
        ('album', ctypes.c_char * 512),
        ('year', ctypes.c_int),
        ('track', ctypes.c_int),
        ('genre', ctypes.c_char * 32),
    ]


class _AVbinStreamInfoVideo8(ctypes.Structure):
    _fields_ = [
        ('width', ctypes.c_uint),
        ('height', ctypes.c_uint),
        ('sample_aspect_num', ctypes.c_uint),
        ('sample_aspect_den', ctypes.c_uint),
        ('frame_rate_num', ctypes.c_uint),
        ('frame_rate_den', ctypes.c_uint),
    ]


class _AVbinStreamInfoAudio8(ctypes.Structure):
    _fields_ = [
        ('sample_format', ctypes.c_int),
        ('sample_rate', ctypes.c_uint),
        ('sample_bits', ctypes.c_uint),
        ('channels', ctypes.c_uint),
    ]


class _AVbinStreamInfoUnion8(ctypes.Union):
    _fields_ = [
        ('video', _AVbinStreamInfoVideo8),
        ('audio', _AVbinStreamInfoAudio8),
    ]


class AVbinStreamInfo8(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('type', ctypes.c_int),
        ('u', _AVbinStreamInfoUnion8)
    ]


class AVbinPacket(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('timestamp', Timestamp),
        ('stream_index', ctypes.c_int),
        ('data', ctypes.POINTER(ctypes.c_uint8)),
        ('size', ctypes.c_size_t),
    ]


AVbinLogCallback = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, 
                                    ctypes.c_char_p)


def timestamp_from_avbin(timestamp):
    return float(timestamp) / 1000000


def get_avbin_lib():
    """ Get avbin .dll/.dylib/.so
    """

    LIBRARIES = {
        'osx64': 'libavbin-11alpha4-osx.dylib',
        'win32': 'avbin-10-win32.dll',
        'win64': 'avbin-10-win64.dll',
        'linux32': 'libavbin-10-linux32.so',
        'linux64': 'libavbin-10-linux64.so',
    }
    
    platform = get_platform()
    
    try:
        lib = LIBRARIES[platform]
    except KeyError:  # pragma: no cover
        raise RuntimeError('Avbin plugin is not supported on platform %s' % 
                           platform)
    
    return get_remote_file('avbin/' + lib)
    

class AvBinFormat(Format):
    """ 
    The AvBinFormat uses the AvBin library (based on libav) to read video files
    
    
    Parameters for reading
    ----------------------
    stream : int
        specifies which video stream to read
    videoformat : str
        specifies the video format, or None (default) for auto-detect
        
    Parameters for get_data
    ----------------------
    out : np.ndarray
        destination for the data retrieved. This can be used to save 
        time-consuming memory allocations when reading multiple image
        sequntially. The shape of out must be (width, height, 3), the
        dtype must be np.uint8 and out must be C-contiguous.
        
        Use the create_empty_image() object of the reader object
        to create an array that is suitable for get_data.
        
        
    """
    
    def __init__(self, *args, **kwargs):
        self._avbin = None
        Format.__init__(self, *args, **kwargs)
    
    def _can_read(self, request):
        # This method is called when the format manager is searching
        # for a format to read a certain image. Return True if this format
        # can do it.
        #
        # The format manager is aware of the extensions and the modes
        # that each format can handle. However, the ability to read a
        # format could be more subtle. Also, the format would ideally
        # check the request.firstbytes and look for a header of some
        # kind. Further, the extension might not always be known.
        #
        # The request object has:
        # request.filename: a representation of the source (only for reporing)
        # request.firstbytes: the first 256 bytes of the file.
        # request.mode[0]: read or write mode
        # request.mode[1]: what kind of data the user expects: one of 'iIvV?'
        
        if request.mode[1] in (self.modes + '?'):
            for ext in self.extensions:
                if request.filename.endswith('.' + ext):
                    return True
    
    def _can_save(self, request):
        return False  # AvBin does not support writing videos
    
    def avbinlib(self, libpath=None):
        if self._avbin is not None and libpath is None:
            # Already loaded
            return self._avbin
        
        if libpath is None:
            libpath = get_avbin_lib()
            
        self._avbin = avbin = ctypes.cdll.LoadLibrary(libpath)
       
        avbin.avbin_get_version.restype = ctypes.c_int
        avbin.avbin_get_ffmpeg_revision.restype = ctypes.c_int
        avbin.avbin_get_audio_buffer_size.restype = ctypes.c_size_t
        avbin.avbin_have_feature.restype = ctypes.c_int
        avbin.avbin_have_feature.argtypes = [ctypes.c_char_p]
        
        avbin.avbin_init.restype = AVbinResult
        avbin.avbin_set_log_level.restype = AVbinResult
        avbin.avbin_set_log_level.argtypes = [AVbinLogLevel]
        avbin.avbin_set_log_callback.argtypes = [AVbinLogCallback]
        
        avbin.avbin_open_filename.restype = AVbinFileP
        avbin.avbin_open_filename.argtypes = [ctypes.c_char_p]
        avbin.avbin_open_filename_with_format.restype = AVbinFileP
        avbin.avbin_open_filename_with_format.argtypes = [ctypes.c_char_p,
                                                          ctypes.c_char_p]
        avbin.avbin_close_file.argtypes = [AVbinFileP]
        avbin.avbin_seek_file.argtypes = [AVbinFileP, Timestamp]
        avbin.avbin_file_info.argtypes = [AVbinFileP, 
                                          ctypes.POINTER(AVbinFileInfo)]
        avbin.avbin_stream_info.argtypes = [AVbinFileP, ctypes.c_int,
                                            ctypes.POINTER(AVbinStreamInfo8)]
        
        avbin.avbin_open_stream.restype = ctypes.c_void_p
        avbin.avbin_open_stream.argtypes = [AVbinFileP, ctypes.c_int]
        avbin.avbin_close_stream.argtypes = [AVbinStreamP]
        
        avbin.avbin_read.argtypes = [AVbinFileP, ctypes.POINTER(AVbinPacket)]
        avbin.avbin_read.restype = AVbinResult
        avbin.avbin_decode_audio.restype = ctypes.c_int
        avbin.avbin_decode_audio.argtypes = [AVbinStreamP, ctypes.c_void_p,
                                             ctypes.c_size_t, ctypes.c_void_p,
                                             ctypes.POINTER(ctypes.c_int)]
        avbin.avbin_decode_video.restype = ctypes.c_int
        avbin.avbin_decode_video.argtypes = [AVbinStreamP, ctypes.c_void_p,
                                             ctypes.c_size_t, ctypes.c_void_p]
                
        avbin.avbin_init()
        avbin.avbin_set_log_level(AVBIN_LOG_QUIET)
    
        return self._avbin
    
    # -- reader
    
    class Reader(Format.Reader):
    
        def _open(self, stream=0, videoformat=None):
            # Specify kwargs here. Optionally, the user-specified kwargs
            # can also be accessed via the request.kwargs object.
            #
            # The request object provides two ways to get access to the
            # data. Use just one:
            #  - Use request.get_file() for a file object (preferred)
            #  - Use request.get_local_filename() for a file on the system
            
            avbin = self.format.avbinlib()
            
            filename = self.request.get_local_filename()
            filename_bytes = filename.encode(
                sys.getfilesystemencoding())
            
            if videoformat is not None:
                self._file = avbin.avbin_open_filename_with_format(
                    filename_bytes, videoformat.encode('ascii'))
                
            else:
                self._file = avbin.avbin_open_filename(filename_bytes)
                
            if not self._file:
                raise IOError('Could not open "%s"' % filename)
            
            self._info = AVbinFileInfo()
            self._info.structure_size = ctypes.sizeof(self._info)        
            avbin.avbin_file_info(self._file, ctypes.byref(self._info))
            self._duration = timestamp_from_avbin(self._info.duration)
            
            # Parse through the available streams in the file and find
            # the video stream specified by stream
    
            video_stream_counter = 0
            
            for i in range(self._info.n_streams):
                info = AVbinStreamInfo8()
                info.structure_size = ctypes.sizeof(info)
                avbin.avbin_stream_info(self._file, i, info)
            
                if info.type != AVBIN_STREAM_TYPE_VIDEO:
                    continue
                
                if video_stream_counter != stream:
                    video_stream_counter += 1
                    continue
                
                # We have the n-th (n=stream number specified) video stream
                self._stream = avbin.avbin_open_stream(self._file, i)
    
                self._width = info.u.video.width
                self._height = info.u.video.height
                
                self._stream_index = i
                break
            else:
                raise IOError('Stream #%d not found in %r' % 
                              (stream, filename))
            
            self._packet = AVbinPacket()
            self._packet.structure_size = ctypes.sizeof(self._packet)
                
            self._framecounter = 0
            
        def _close(self):
            avbin = self.format.avbinlib()
            if self._file is not None:
                avbin.avbin_close_file(self._file)
        
        def _get_length(self):
            # Return the number of images. Can be np.inf
            return np.inf
            
        def create_empty_image(self):
            return np.zeros((self._height, self._width, 3), dtype=np.uint8)
        
        def _get_data(self, index, out=None):
            avbin = self.format.avbinlib()
            
            # Return the data and meta data for the given index
            if index != self._framecounter:
                raise IndexError('Avbin format cannot seek')
            self._framecounter += 1            
            
            if out is None:
                out = self.create_empty_image()
            
            assert (out.dtype == np.uint8 and out.flags.c_contiguous and
                    out.shape == (self._height, self._width, 3))
            
            # Read from the file until the next packet of our video
            # stream is found
            while True:
                avbin.avbin_read(self._file, ctypes.byref(self._packet))
                if self._packet.stream_index == self._stream_index:
                    break
            
            # Decode the image, storing data in the out array
            avbin.avbin_decode_video(self._stream, self._packet.data, 
                                     self._packet.size, out.ctypes.data)
            
            # Return array and dummy meta data
            return out, {}
            
        def _get_meta_data(self, index):
            # Get the meta data for the given index. If index is None, it
            # should return the global meta data.
            return {}  # This format does not support meta data
    
# Register. You register an *instance* of a Format class. Here specify:
format = AvBinFormat('AvBin',  # short name
                     'Reading videos using AvBin (libav libraries)',  
                     'mov avi mp4 mpg mpeg',  # list of extensions
                     'I'  # modes, characters in iIvV
                     )
formats.add_format(format)
