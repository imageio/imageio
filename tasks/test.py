import os
import sys
import subprocess
import webbrowser

from invoke import task

from ._config import ROOT_DIR


@task
def lint(ctx):
    """alias for "invoke test --style" """
    flake8_wrapper()  # exits on fail
    black_wrapper(False)  # always exits


@task(
    optional=["unit", "style"],
    help=dict(
        unit="run unit tests (pytest)",
        installed="like unit, but prefer using installed package, "
        + "and do not allow the use of internet.",
        style="run style tests (flake8 and black)",
        cover="show test coverage",
    ),
)
def test(ctx, unit=False, installed=False, style=False, cover=False):
    """run tests (unit, style)"""

    if not (unit or installed or style or cover):
        sys.exit("Test task needs --unit, --style or --cover")

    if unit:
        sys.exit(pytest_wrapper())

    if style:
        flake8_wrapper()  # exits on fail
        black_wrapper(False)  # always exits

    if installed:
        for p in list(sys.path):
            if p in ("", "."):
                sys.path.remove(p)
            elif p == ROOT_DIR or p == os.path.dirname(ROOT_DIR):
                sys.path.remove(p)
        os.environ["IMAGEIO_NO_INTERNET"] = "1"
        sys.exit(pytest_wrapper())

    if cover:
        res = pytest_wrapper(cov_report="html")
        if res:
            raise RuntimeError("Cannot show coverage, tests failed.")
        print("Launching browser.")
        fname = os.path.join(os.getcwd(), "htmlcov", "index.html")
        if not os.path.isfile(fname):
            raise IOError("Generated file not found: %s" % fname)
        webbrowser.open_new_tab(fname)


@task
def autoformat(ctx):
    """Alias for format."""
    black_wrapper(True)


@task
def format(ctx):
    """Format the code using the Black uncompromising formatter."""
    black_wrapper(True)


@task
def checkformat(ctx):
    """Check for formatting errors using Black."""
    black_wrapper(False)


@task
def lint(ctx):
    """Check for linting errors using flake8."""
    flake8_wrapper()  # exits on fail


def flake8_wrapper():
    """Helper function to catch the worst style errors (e.g. unused variables)."""
    # http://pep8.readthedocs.io/en/latest/intro.html#error-codes
    cmd = [sys.executable, "-m", "flake8", "--select=F,E11", "imageio", "tests"]
    ret_code = subprocess.call(cmd, cwd=ROOT_DIR)
    if ret_code == 0:
        print("No style errors found")
    else:
        sys.exit(ret_code)


def black_wrapper(writeback):
    """Helper function to invoke black programatically."""

    check = [] if writeback else ["--check"]
    exclude = "|".join(["_tifffile\.py"])
    sys.argv[1:] = check + ["--exclude", exclude, ROOT_DIR]

    import black

    black.main()


def pytest_wrapper(cov_report="term"):
    """ Helper function to run tests."""
    import pytest

    return pytest.main(
        [
            "-v",
            "--cov",
            "imageio",
            "--cov-config",
            ".coveragerc",
            "--cov-report",
            cov_report,
            os.path.join(ROOT_DIR, "tests"),
        ]
    )
