"""
Unittests for generating permutations file
"""

import unittest
from generate_permutations import arg_parse
import sys


class TestArgParsing(unittest.TestCase):
    def setUp(self):
        self.parser = arg_parse()

    """
    If no arguments passed, should fail with SystemExit
    """

    def test_no_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_invalid_num_fields(self):
        args = self.parser.parse_args(['start', 'end', 'display_name', 'mobile_available'])
        command_error = "Only a max of 3 fields allowed"
        self.assertEqual(args, command_error)

    def test_invalid_file(self):
        sys.argv[1:] = ["--seed_data_file", "permutation.json"]
        options = arg_parse()
        self.assertEquals("permutation.json", options)


if __name__ == '__main__':
    unittest.main()
