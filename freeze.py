""" 

To be able to access the freeimage lib also from frozen applications,
we need some special care. On the cx_freeze mailing list there's currently
a discussion going to think of a plan to automate this. This file
illustrates one possible way it could work. At the same time, this file
implements a solution to the freezing problem for the time being.

To cx_freeze an app that uses imageio, in the freeze script do: 
from imageio.freeze import freeze_copy_resources.
Signature: freeze_copy_resources('path/to/frozen/app', 'imageio')


------------------------------------------------------------
Proposal to allow packages to specify includes and resources
------------------------------------------------------------

Introduction
------------

Some packages use lazy/dynamic imports or use resources such as binary
files or external libraries. Currently, to freeze an application that
uses such a package requires specifying includes and explicitly copying
all resources, as well as applying tricks to retrieve these resources
at runtime.

For the case of the includes, cx_freeze currently has some hooks to
specify includes on a per-package basis. We propose to let the packages
themselves specify the includes, as well as any required resources.
In theory, this allows package maintainers to support freezing (for
their package) that Just Works.


How to hook
-----------

We propose to allow a package to place a module called 'freeze.py' in
the root of the package directory. The presence of this file tells the
freezer that the package wants to specify includes or resources. The 
freezer can then import this file with out having to import the whole 
package, and look for a couple of functions.

Includes and excludes
---------------------

One such function is called "get_includes" which has no input arguments
and should return a list of module/package names to include. Along the 
same line "get_excludes" specifies a list of excludes.


Resources
---------

Another function is called "get_resources" which accepts no input arguments
and returns a list of tuples. Before going into detail how these tuples
look like, lets first specify a few other things ...

1) In the non-frozen situation, the resources should be in a sub-directory 
of the package. This subdirectory may have an arbitrary name. The recommended 
name is 'resources', but sometimes 'lib' may be more appropriate. Let's call 
this <subdir>.

2) In the frozen situation, there should at runtime be a directory
for which the location can be reliably detected. For cx_freeze this
can simply be the directory containing the executable. This directory
has a subdirectory called 'resources', which has subdirectories corresponding
to package names that hold the resources for the packages. e.g. a package
somepackage.subpackage has its resources in 
'path/to/app/resources/somepackage/subpackage/<subdir>'.

3) In the tuples returned by get_resource, the first element is the 
<subdir> to put the resource in. The second element is the full path
to the resource. If this path is a directory, all files and subdirectories
are copied. In the simplest case this function would return 
``[(<subdir>, 'path/to/subdir')]``.

4) The package maintainer can define a relatively simple function that
will determine the location of the package resources, regardless of 
being frozen or not. This function can be placed somewhere in the 
cx_freeze documentation for easy reference. (~50 lines of code)

"""

## This is what helps the user retrieve the location of the resources


import sys
import os
import imp

def is_frozen():
    return bool( getattr(sys, 'frozen', None) )


def application_dir():
    """ application_dir()
    
    Get the directory in which the current application is located. 
    The "application" can be a Python script or a frozen application. 
    Raises a RuntimeError if in interpreter mode.
    """
    # Test if the current process can be considered an "application"
    if not sys.path or not sys.path[0]:
        raise RuntimeError('Cannot determine app path because sys.path[0] is empty!')
    # Get the path. If frozen, sys.path[0] is the name of the executable,
    # otherwise it is the path to the directory that contains the script.
    thepath = sys.path[0]
    if is_frozen():
        thepath = os.path.dirname(thepath)
    # Return absolute version, or symlinks may not work
    return os.path.abspath(thepath)


def _find_module(fullname, path=None):
    """ Similar to imp.find_module, but can deal with subpackages.
    """
    parts = fullname.split('.')
    file, filename, dummy = imp.find_module(parts.pop(0), path)
    if parts:
        return _find_module('.'.join(parts), [filename])
    elif os.path.isfile(filename):
        return os.path.dirname(filename)
    else:
        return filename


def resource_dir(package_name=None, subdir=None):
    """ resource_dir(package_name=None, subdir=None)
    
    Get the directory containing the resources for the given package.
    This function deals with frozen and non-frozen applications.
    
    Example: resource_dir('imageio', 'lib')
    """
    
    # Init
    package_name = package_name or ''
    subdir = subdir or ''
    
    # Build directory based on whether we're in a frozen app or not
    if is_frozen() or not package_name:
        package_parts = os.path.join(*package_name.split('.'))
        return os.path.join(application_dir(), 'resources', package_parts, subdir)
    else:
        # Get dir and append subdir
        package_dir = _find_module(package_name)
        return os.path.join(package_dir, subdir)


## This is what cx_freeze should look for and call


def get_includes():
    return []


def get_resources():
    """ returns a list of resources that should be frozen along.
    """ 
    from imageio.freeimage_install import load_freeimage
    return  [
            ('lib', load_freeimage()[1]), # If not in resource dir, put it there now
            ('lib', resource_dir('imageio', 'lib')), # This overwrites the previous
            ]


## This is what cx_freeze should do


import shutil
def freeze_copy_resources(app_path, package_name):
    """ Copy resources from a source directory to
    the frozen destination directory.
    
    app_path should be the full path that contains the frozen app.
    package_name should be the full name of the package (may include dots).
    """
    
    # Create resources directory
    package_parts = package_name.split('.')
    dest_path = os.path.join(app_path, 'resources', *package_parts)
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path)
    
    def copy_item(base_path, rel_path, subdir):
        full_path1 = os.path.join(base_path, rel_path)
        full_path2 = os.path.join(dest_path, subdir, rel_path)
        if os.path.isfile(full_path1):
            shutil.copy(full_path1, full_path2)
        elif os.path.isdir(full_path1):
            if not os.path.isdir(full_path2):
                os.makedirs(full_path2)
            for item in os.listdir(full_path1):
                copy_item(base_path, os.path.join(rel_path, item), subdir)
    
    resources = get_resources()
    for subdir, res in resources:
        copy_item(res, '', subdir)
