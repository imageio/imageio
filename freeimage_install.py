import os
import sys
import shutil
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen # Py3k

# update base_address to tagged, scikits-image-hosted fork as needed
# todo: chose an address that is http (not https), some might not have SSL
BASE_ADDRESS = 'https://raw.github.com/zachrahan/freeimage-sharedlib/master/'

FILES = {
    'README': 'FreeImage-README.txt',
    'license-fi.txt': 'FreeImage-License.txt'
}

LIBRARIES = {
    ('darwin', 32): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('darwin', 64): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('win32', 32): 'FreeImage-3.15.1-win32.dll',
    ('win32', 64): 'FreeImage-3.15.1-win64.dll'
}

def _download(url, dest, timeout=20):
    print('Downloading: %s' % url)
    dest_f = open(dest, 'wb')
    remote = urlopen(url, timeout=timeout)
    try:
        shutil.copyfileobj(remote, dest_f)
    except:
        dest_f.close()
        os.remove(dest)
        raise RuntimeError('Could not download %s to %s.' %(url, dest))
    finally:
        remote.close()
    dest_f.close()


def retrieve_files(retrieve_all=False):
    
    if retrieve_all:
        # We want to download all files
        files = dict(FILES)
        for key, library in LIBRARIES.items():
            files[library] = library
    else:
        # We only want to download the one for this system
        bits = 64 if sys.maxsize > 2**32 else 32
        key = (sys.platform, bits)
        if key not in LIBRARIES:
            raise RuntimeError('No precompiled FreeImage libraries are available '
                            'for %d-bit %s systems.'%(bits, sys.platform))
        library = LIBRARIES[key]
        print('Found: %s for %d-bit %s systems at %s' % (library, bits, 
                sys.platform, BASE_ADDRESS))
        # Select files to download
        files = dict(FILES)
        files[library] = library
    
    # Download all files and put them in the lib dir
    for src, dst in files.items():
        dest = os.path.join(os.path.dirname(__file__), 'lib', dst)
        if not os.path.exists(dest):
            _download(BASE_ADDRESS+src, dest)


if __name__ == '__main__':
    retrieve_files()
