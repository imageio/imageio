from pyzolib import insertdocs
import subprocess
import sys

# Imports to fill the global namespace
import imageio

# Auto generate docs for each format
imageio._format_docs = imageio.formats.create_docs_for_all_formats()

# Insert docs
insertdocs.parse_rst_files(NS=globals())

# Set version
text = open('conf.py','rb').read().decode('utf-8')
lines = []
for line in text.splitlines():
    if line.startswith('version = '):
        line = "version  = '%s'" % '.'.join(imageio.__version__.split('.')[:2])
    elif line.startswith('release = '):
        line = "release = '%s'" % imageio.__version__
    lines.append(line)
text = '\n'.join(lines)
open('conf.py','wb').write(text.encode('utf-8'))

# Tell Sphinx to build the docs
if sys.platform.startswith('win'):
    p = subprocess.check_call(['make.bat', 'html'])
else:
    p = subprocess.check_call(['make', 'html']) # ?
