
import os
import sys
import ctypes

LOCALDIR = os.path.abspath(os.path.dirname(__file__))


def looks_lib(fname):
    """ Returns True of the given filename looks like a dynamic library.
    Based on extension, but cross-platform and more flexible. 
    """
    fname = fname.lower()
    if sys.platform.startswith('win'):
        return fname.endswith('.dll')
    elif sys.platform == 'darwin':
        return fname.endswith('.dylib')
    else:
        return '.so' in fname


def generate_candidate_libs(lib_names):
    """ Generate a list of candidate filenames of what might be the dynamic
    library corresponding with the given list of names.
    Returns (lib_dirs, lib_paths)
    """
    
    # look for likely library files in the following dirs:
    potential_lib_dirs = [
                LOCALDIR,
                os.path.join(LOCALDIR, 'lib'),
                '/lib',
                '/usr/lib',
                '/usr/local/lib',
                '/opt/local/lib',
                os.path.join(sys.prefix, 'lib'),
                os.path.join(sys.prefix, 'DLLs')
                ]
    if 'HOME' in os.environ:
        potential_lib_dirs.append(os.path.join(os.environ['HOME'], 'lib'))
    
    # Select only the dirs for which a directory exists, and remove duplicates
    lib_dirs = []
    for ld in potential_lib_dirs:
        if os.path.isdir(ld) and ld not in lib_dirs:
            lib_dirs.append(ld)
    
    # Now attempt to find libraries of that name in the given directory
    # (case-insensitive and without regard for extension)
    lib_paths = []
    for lib_dir in lib_dirs:
        files = os.listdir(lib_dir)
        for lib_name in lib_names:
            # Test all filenames for name and ext (prefer short names)
            for fname in sorted(files, key=len):
                if fname.lower().startswith(lib_name) and looks_lib(fname):
                    lib_paths.append(os.path.join(lib_dir, fname))
    
    # Return (only the items which are files)
    lib_paths = [lp for lp in lib_paths if os.path.isfile(lp)]
    return lib_dirs, lib_paths


def load_lib(exact_lib_names, lib_names):
    """ Load a dynamic library. 
    
    This function first tries to just load
    the library from the given exact names. When that fails, it tries to
    load find the library in common locations. It searches for files that 
    start with one of the names given in lib_names (case insensitive).
    
    Returns (ctypes_library, library_path)
    """
    
    # Get reference name (for better messages)
    if lib_names:
        the_lib_name = lib_names[0]
    elif exact_lib_names:
        the_lib_name = the_lib_name[0]
    else:
        raise ValueError("No library name given.")
    
    # Collect filenames of potential libraries
    # First try a few bare library names that ctypes might be able to find
    # in the default locations for each platform. 
    lib_dirs, lib_paths = generate_candidate_libs(lib_names)
    lib_paths = exact_lib_names + lib_paths
    
    # Select loader 
    if sys.platform.startswith('win'):
        loader = ctypes.windll
    else:
        loader = ctypes.cdll
    
    # Try to load until success
    the_lib = None
    errors = []
    for fname in lib_paths:
        try:
            the_lib = loader.LoadLibrary(fname)
            break
        except Exception:
            # Don't record errors when it couldn't load the library from an
            # exact name -- this fails often, and doesn't provide any useful
            # debugging information anyway, beyond "couldn't find library..."
            if fname not in exact_lib_names:
                # Get exception instance in Python 2.x/3.x compatible manner
                e_type, e_value, e_tb = sys.exc_info()
                del e_tb
                errors.append((fname, e_value))
    
    # No success ...
    if the_lib is None:
        if errors:
            # No library loaded, and load-errors reported for some
            # candidate libs
            err_txt = ['%s:\n%s'%(l, str(e)) for l, e in errors]
            raise OSError('One or more %s libraries were found, but '%the_lib_name + 
                          'could not be loaded due to the following errors:\n' +
                          '\n\n'.join(err_txt))
        else:
            # No errors, because no potential libraries found at all!
            raise OSError('Could not find a %s library in any of:\n'%the_lib_name +
                          '\n'.join(lib_dirs))
    
    # Done
    return the_lib, fname


## Freeimage stuff
# The above is all generic. Below is code specific for freeimage. By 
# including it in this module, it becomes easy to use it both from
# freeimage.py and setup.py. Note, however, that the freeimage_install
# is required, but which should be imported in different ways; therefore
# it is passed as an argument. Not very beautiful, but practicallity beats
# purity.

# Store some messages as constants
MSG_NOLIB_DOWNLOAD = 'Attempting to download the FreeImage library.'
MSG_NOLIB_LINUX = 'Install FreeImage (libfreeimage3) via your package manager or build from source.'
MSG_NOLIB_OTHER = 'Please install the FreeImage library.'


def load_freeimage(freeimage_install, raise_if_not_available=True):
    # Load library
    lib_names = ['freeimage', 'libfreeimage']
    exact_lib_names = ['FreeImage', 'libfreeimage.dylib', 
                        'libfreeimage.so', 'libfreeimage.so.3']
    
    try:
        lib, fname = load_lib(exact_lib_names, lib_names)
    except OSError:
        # Could not load. Get why
        e_type, e_value, e_tb = sys.exc_info(); del e_tb
        load_error = str(e_value)
        # Can we download? If not, raise error.
        if freeimage_install.get_key_for_available_lib() is None:
            if sys.platform.startswith('linux'):
                err_msg = load_error + '\n' + MSG_NOLIB_LINUX
            else:
                err_msg = load_error + '\n' + MSG_NOLIB_OTHER
            if raise_if_not_available:
                raise OSError(err_msg)
            else:
                print('Warning:' + err_msg)
                return
        # Yes, it seems so! Try it and then try loading again
        print(load_error + '\n' + MSG_NOLIB_DOWNLOAD)
        freeimage_install.retrieve_files()
        lib, fname = load_lib(exact_lib_names, lib_names)
        # If we get here, we did a good job!
        print('FreeImage library deployed succesfully.')
    
    # Return library and the filename where it's loaded
    return lib, fname
