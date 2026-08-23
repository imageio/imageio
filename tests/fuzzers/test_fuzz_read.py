import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import fuzz_read


class FuzzReadTest(unittest.TestCase):
    def test_unexpected_exception_is_not_suppressed(self):
        sentinel = SimpleNamespace(imread=Mock(side_effect=AssertionError))
        with patch.object(fuzz_read, "iio", sentinel):
            with self.assertRaises(AssertionError):
                fuzz_read.TestOneInput(b"0123456789")


if __name__ == "__main__":
    unittest.main()
