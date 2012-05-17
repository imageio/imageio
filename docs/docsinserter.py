from pyzolib import insertdocs
import subprocess
import sys

# Imports to fill the global namespace
import imageio

# Insert docs
insertdocs.parse_rst_files(NS=globals())

# Tell Sphinx to build the docs
if sys.platform.startswith('win'):
    p = subprocess.check_call(['make.bat', 'html'])
else:
    p = subprocess.check_call(['make', 'html']) # ?
