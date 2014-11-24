# -*- coding: utf-8 -*-
# Copyright (c) 2014, imageio contributors
# Based on code from the vispy project
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

"""Data downloading and reading functions
"""

from __future__ import absolute_import, print_function, division

from math import log
import os
from os import path as op
import sys
import shutil
import time

from . import appdata_dir, resource_dirs
from . import StdoutProgressIndicator, string_types, urlopen


def get_remote_file(fname, directory=None, force_download=False):
    """ Get a the filename for the local version of a file from the web

    Parameters
    ----------
    fname : str
        The relative filename on the remote data repository to download.
        These correspond to paths on
        ``https://github.com/imageio/imageio-binaries/``.
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

    Returns
    -------
    fname : str
        The path to the file on the local system.
    """
    _url_root = 'https://github.com/imageio/imageio-binaries/raw/master/'
    url = _url_root + fname
    fname = op.normcase(fname)  # convert to native
    # Get dirs to look for the resource
    directory = directory or appdata_dir('imageio')
    dirs = resource_dirs()
    dirs.insert(0, appdata_dir('imageio'))
    dirs.insert(0, directory)  # Given dir has preference
    # Try to find the resource locally
    for dir in dirs:
        filename = op.join(dir, fname)
        if op.isfile(filename):
            if not force_download:  # we're done
                return filename
            if isinstance(force_download, string_types):
                ntime = time.strptime(force_download, '%Y-%m-%d')
                ftime = time.gmtime(op.getctime(filename))
                if ftime >= ntime:
                    return filename
                else:
                    print('File older than %s, updating...' % force_download)
                    break
    
    # If we get here, we're going to try to download the file
    if os.getenv('IMAGEIO_NO_INTERNET', '').lower() in ('1', 'true', 'yes'):
        raise IOError('Cannot download resource from the internet')
    # Get filename to store to and make sure the dir exists
    filename = op.join(directory, fname)
    if not op.isdir(op.dirname(filename)):
        os.makedirs(op.abspath(op.dirname(filename)))
    # let's go get the file
    if os.getenv('CONTINUOUS_INTEGRATION', False):  # pragma: no cover
        # On Travis, we retry a few times ...
        for i in range(2):
            try:
                _fetch_file(url, filename)
                return filename
            except IOError:
                time.sleep(0.5)
        else:
            _fetch_file(url, filename)
            return filename
    else:  # pragma: no cover
        _fetch_file(url, filename)
        return filename


def _fetch_file(url, file_name, print_destination=True):
    """Load requested file, downloading it if needed or requested

    Parameters
    ----------
    url: string
        The url of file to be downloaded.
    file_name: string
        Name, along with the path, of where downloaded file will be saved.
    print_destination: bool, optional
        If true, destination of where file was saved will be printed after
        download finishes.
    resume: bool, optional
        If true, try to resume partially downloaded files.
    """
    # Adapted from NISL:
    # https://github.com/nisl/tutorial/blob/master/nisl/datasets.py

    temp_file_name = file_name + ".part"
    local_file = None
    initial_size = 0
    try:
        # Checking file size and displaying it alongside the download url
        remote_file = urlopen(url, timeout=5.)
        file_size = int(remote_file.headers['Content-Length'].strip())
        print('Downloading data from %s (%s)' % (url, _sizeof_fmt(file_size)))
        # Downloading data (can be extended to resume if need be)
        local_file = open(temp_file_name, "wb")
        _chunk_read(remote_file, local_file, initial_size=initial_size)
        # temp file must be closed prior to the move
        if not local_file.closed:
            local_file.close()
        shutil.move(temp_file_name, file_name)
        if print_destination is True:
            sys.stdout.write('File saved as %s.\n' % file_name)
    except Exception as e:
        raise IOError('Error while fetching file %s.\n'
                      'Dataset fetching aborted (%s)' % (url, e))
    finally:
        if local_file is not None:
            if not local_file.closed:
                local_file.close()


def _chunk_read(response, local_file, chunk_size=8192, initial_size=0):
    """Download a file chunk by chunk and show advancement

    Can also be used when resuming downloads over http.

    Parameters
    ----------
    response: urllib.response.addinfourl
        Response to the download request in order to get file size.
    local_file: file
        Hard disk file where data should be written.
    chunk_size: integer, optional
        Size of downloaded chunks. Default: 8192
    initial_size: int, optional
        If resuming, indicate the initial size of the file.
    """
    # Adapted from NISL:
    # https://github.com/nisl/tutorial/blob/master/nisl/datasets.py

    bytes_so_far = initial_size
    # Returns only amount left to download when resuming, not the size of the
    # entire file
    total_size = int(response.headers['Content-Length'].strip())
    total_size += initial_size
    
    progress = StdoutProgressIndicator('Downloading')
    progress.start('', 'bytes', total_size)
    
    while True:
        chunk = response.read(chunk_size)
        bytes_so_far += len(chunk)
        if not chunk:
            break
        _chunk_write(chunk, local_file, progress)
    progress.finish('Done')


def _chunk_write(chunk, local_file, progress):
    """Write a chunk to file and update the progress bar"""
    local_file.write(chunk)
    progress.increase_progress(len(chunk))
    time.sleep(0.0001)


def _sizeof_fmt(num):
    """Turn number of bytes into human-readable str"""
    units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']
    decimals = [0, 0, 1, 2, 2, 2]
    """Human friendly file size"""
    if num > 1:
        exponent = min(int(log(num, 1024)), len(units) - 1)
        quotient = float(num) / 1024 ** exponent
        unit = units[exponent]
        num_decimals = decimals[exponent]
        format_string = '{0:.%sf} {1}' % (num_decimals)
        return format_string.format(quotient, unit)
    return '0 bytes' if num == 0 else '1 byte'
