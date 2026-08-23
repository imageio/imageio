#!/usr/bin/python3
import sys
import struct

import atheris  # type: ignore

try:
    with atheris.instrument_imports():
        import imageio.v3 as iio
except Exception:
    iio = None


def TestOneInput(data):
    if iio is None or len(data) < 10:
        return
    try:
        iio.imread(data)
    except (ValueError, RuntimeError, struct.error):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
