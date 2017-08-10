"""
Unittests for generating permutations file
"""

import unittest
from test_generate_permutations import arg_parse




class TestArgParsing(unittest.TestCase):

    # def test_parser(self):
    #     parser = arg_parse(["test", "start"])
    #     self.assertEqual(parser.long)


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


if __name__ == '__main__':
    unittest.main()

