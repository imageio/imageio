#!/usr/bin/python3
import os
import sys
import atheris

import imageio


def TestOneInput(data):
    with open("/tmp/img1.file", "wb+") as img1_f:
        img1_f.write(data)
    try:
        imageio.imread("/tmp/img1.file")
    except ValueError:
        None
    except RuntimeError:
        None
    os.remove("/tmp/img1.file")


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
