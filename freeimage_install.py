import os
import sys
import shutil
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen # Py3k

LOCALDIR = os.path.abspath(os.path.dirname(__file__))

# Where to get the downloadable files
# Note that we hardcode the filenames. In theory we could make a text file
# that lists the most up-to-date libraries, but the current approach is
# much easier, and its probably enough to just change the filenames to
# the latest libs available at each release.
BASE_ADDRESS = 'http://bitbucket.org/almarklein/imageio/downloads/'

FILES = ['README.txt', 'FreeImage-License.txt']

LIBRARIES = {
    ('darwin', 32): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('darwin', 64): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('win32', 32): 'FreeImage-3.15.1-win32.dll',
    ('win32', 64): 'FreeImage-3.15.1-win64.dll'
}

def _download(url, dest, timeout=20):
    print('Downloading: %s' % url)
    dest_f = open(dest, 'wb')
    # Open connection
    try:
        remote = urlopen(url, timeout=timeout)
    except IOError:
        dest_f.close()
        os.remove(dest)
        raise RuntimeError('Could not find %s.' % url)
    # Download
    try:
        shutil.copyfileobj(remote, dest_f)
    except:
        dest_f.close()
        os.remove(dest)
        raise RuntimeError('Could not download %s to %s.' %(url, dest))
    finally:
        remote.close()
    # Close local file
    dest_f.flush()
    dest_f.close()


def get_key_for_available_lib():
    """ Get key (platform, bits) for the current system.
    Returns None if there is no downloadable lib for this key.
    """
    bits = 64 if sys.maxsize > 2**32 else 32
    key = (sys.platform, bits)
    if key in LIBRARIES:
        return key
    else:
        return None


def retrieve_files(retrieve_all=False):
    
    if retrieve_all:
        # We want to download all files
        files = list(FILES)
        for key, library in LIBRARIES.items():
            files.append(library)
    else:
        # We only want to download the one for this system
        key = get_key_for_available_lib()
        if key is None:
            raise RuntimeError('No precompiled FreeImage libraries are available '
                            'for this system.')
        library = LIBRARIES[key]
        print('Found: %s for %d-bit %s systems at %s' % (library, key[1], 
                key[0], BASE_ADDRESS))
        # Select files to download
        files = list(FILES)
        files.append(library)
    
    # Download all files and put them in the lib dir
    for fname in files:
        src = BASE_ADDRESS+fname
        dest = os.path.join(LOCALDIR, 'lib', fname)
        if not os.path.exists(dest):
            _download(src, dest)


if __name__ == '__main__':
    retrieve_files(True)
