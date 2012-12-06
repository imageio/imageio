""" 

To be able to access the freeimage lib also from frozen applications,
we need some special care. On the cx_freeze mailing list there's
currently a discussion going to think of a plan to automate this. This
file illustrates one possible way it could work. At the same time, this
file implements a solution to the freezing problem for the time being.

To cx_freeze an app that uses imageio, in the freeze script do: from
imageio.freeze import freeze_copy_resources. Signature:
freeze_copy_resources('path/to/frozen/app', 'imageio')


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
themselves specify the includes, as well as any required resources. In
theory, this allows package maintainers to support freezing (for their
package) that Just Works.


How to hook
-----------

We propose to allow a package to place a module called 'freeze.py' in
the root of the package directory. The presence of this file tells the
freezer that the package wants to specify includes or resources. The
freezer can then import this file without having to import the whole
package, and look for a couple of functions.


Includes and excludes
---------------------

One such function is called "get_includes" which has no input arguments
and should return a list of module/package names to include. Along the
same line "get_excludes" specifies a list of excludes.


Resources
---------

Another function is called "get_resources" which accepts no input
arguments and returns a list of resources, which can be files or
directories. If a specified resource is relative, the structure is
copied one-on-one to the resource directory. If the specified resource
is absolute, the resource is copied to the root of the resource
directory.

1) In the non-frozen situation, the resources should be in a
sub-directory of the package. This subdirectory may have an arbitrary
name. The recommended name is 'resources', but sometimes 'lib' may be
more appropriate. Let's call this <subdir>.

2) In the frozen situation, there should at runtime be a directory for
which the location can be reliably detected. For cx_freeze this can
simply be the directory containing the executable. This directory has
a subdirectory called 'resources', which has subdirectories
corresponding to package names that hold the resources for the packages.
e.g. a package somepackage.subpackage has its resources in
'path/to/app/resources/somepackage/subpackage/<subdir>'.

3) The package maintainer can use arelatively simple function that will
determine the location of the package resources, regardless of being
frozen or not. This function can be placed somewhere in the cx_freeze
documentation for easy reference. (~30 lines of code)

"""

## This is what helps the user retrieve the location of the resources

import sys
import os
import imp


def resource_dir(package_name, subdir=None):
    """ resource_dir(package_name, subdir=None)
    
    Get the directory containing the resources for the given package, also 
    for frozen applications. 
    
    Example: resource_dir('imageio', 'lib')
    """
    def _find_module(fullname, path=None):
        # Similar to imp.find_module, but can deal with subpackages.
        parts = fullname.split('.')
        file, filename, dummy = imp.find_module(parts.pop(0), path)
        if parts:
            return _find_module('.'.join(parts), [filename])
        elif os.path.isfile(filename):
            return os.path.dirname(filename)
        else:
            return filename
    
    subdir = subdir or ''
    if getattr(sys, 'frozen', None):
        # In frozen app we always look in resources dir
        # Code to get application dir from pyzolib.paths.applicationdir()
        package_parts = os.path.join(*package_name.split('.'))
        application_dir = os.path.abspath(os.path.dirname(sys.path[0]))
        return os.path.join(application_dir, 'resources', package_parts, subdir)
    else:
        # Find location of given module. The module does not have to be
        # imported (making life easier for freezers), but must be "importable".
        package_dir = _find_module(package_name)
        return os.path.join(package_dir, subdir)


## This is what cx_freeze should look for and call


def get_includes():
    if sys.version_info[0] == 3:
        urllib = ['email', 'urllib.request',]
    else:
        urllib = ['urllib2']
    return urllib + ['numpy', 'zipfile', 'io']


def get_excludes():
    return []


def get_resources():
    """ returns a list of resources that should be frozen along.
    """
    import imageio
    libfile = imageio.fi._lib_fname
    if os.path.isfile(libfile):
        return ['lib', libfile]
    else:
        return ['lib']


## This is what cx_freeze should do

# todo: yet untested

import shutil
def freeze_copy_resources(app_path, package_name):
    """ Copy resources from a source directory to
    the frozen destination directory.
    
    app_path should be the full path that contains the frozen app.
    package_name should be the full name of the package (may include dots).
    """
    
    # Get source and destination resource directory
    package_parts = package_name.split('.')
    src_path = resource_dir(package_name)
    dst_path = os.path.join(app_path, 'resources', *package_parts)    
    
    # Create resources directory if necessary
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    
    def copy_item(src, dst):
        if os.path.isfile(src):
            if not os.path.isdir(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst))
            shutil.copy(src, dst)
        elif os.path.isdir(src):
            for item in os.listdir(src):
                copy_item(os.path.join(src, item), os.path.join(dst, item))
    
    for res in get_resources():
        # Determine source and destination.
        if os.path.isabs(res):
            # res absolute: destination is in root of resource dir
            src = res
            dst = os.path.join(dst_path, os.path.basename(res))
        else:
            # res relative: both source and destination are relative
            src = os.path.join(src_path, res)
            dst = os.path.join(dst_path, res)
        # Copy
        copy_item(src, dst)
