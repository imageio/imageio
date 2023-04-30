"""
Make this module itself executable as an alias for invoke.
"""

import sys
import subprocess
import warnings


warnings.warn(
    "Invoke scripts are deprecated and will be removed in ImageIO v3. They"
    " have been superseeded by CI scripts and there is currently no plan to"
    " keep invoke. If you want to keep them, please open a new issue so"
    " that we can discuss.",
    DeprecationWarning,
)

cmd = ["invoke"]
if len(sys.argv) == 1:
    cmd.append("help")
else:
    cmd.extend(sys.argv[1:])

subprocess.check_call(cmd)
