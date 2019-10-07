"""
Helper functions for freezing imageio.
"""

import sys


def get_includes():
    return urllib + ["email", "urllib.request", "numpy", "zipfile", "io"]


def get_excludes():
    return []
