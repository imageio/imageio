# Launch maker

import os
import sys

START_DIR = os.path.abspath(os.getcwd())
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from make import Maker

try:
    Maker(sys.argv)
finally:
    os.chdir(START_DIR)
