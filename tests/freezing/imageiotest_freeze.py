""" FREEZING WITH CX_FREEZE

"""

# styletest: ignore E251 (spaces around keyword, 

import os

from cx_Freeze import Executable, Freezer

from imageio import freeze

# Define app name and such
name = "imageiotest"
srcDir = os.path.abspath('')
distDir = os.path.join(srcDir, 'frozen')
scriptFile = os.path.join(srcDir, name + '.py')
iconFile = ''

## includes and excludes

# you usually do not need these
excludes = ["_ssl", "pyreadline", "pdb",
            "matplotlib", "doctest", 
            "scipy.linalg", "scipy.special", "Pyrex", 
            "numpy.core._dotblas", "PIL", "wx",
            ]
# excludes for tk
tk_excludes = ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
               "pywin.dialogs", "pywin.dialogs.list",
               "Tkconstants", "Tkinter", "tcl",
               ]
excludes.extend(tk_excludes)

includes = freeze.get_includes()
excludes.extend(freeze.get_excludes())


## Freeze  


ex = Executable(scriptFile, 
                #icon=iconFile,
                #appendScriptToExe = True,
                #base = 'Win32GUI', # this is what hides the console
                )

f = Freezer({ex: True}, 
            includes = includes,
            excludes = excludes,
            targetDir = distDir,
            #copyDependentFiles = True,
            #appendScriptToExe=True,
            optimizeFlag = 1, 
            compress = False,
            silent = True, 
            )

f.Freeze()

# Copy resources.
# Some day, cx_Freeze should do this automatically ...
freeze.freeze_copy_resources(distDir, 'imageio')
