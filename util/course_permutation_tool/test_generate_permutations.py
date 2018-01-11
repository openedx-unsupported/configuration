"""
Unittests for generating permutations file
"""

import unittest
import generate_permutations

class TestGeneratePermutations(unittest.TestCase):
    def test_start_field_recursion(self):
        # test display_name permutation
        process_field_args = {"audit": [True], "end": ["future"], "mobile_available": [True], "verified": [True],
                              "start": ["past"],
                              "display_name": ["International Project Management", "Cybersecurity Fundamentals", "",
                                               None]}
        actual_output = generate_permutations.start_field_recursion(process_field_args)

        expected_output = {
            "courses": [
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": "International Project Management"
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": "Cybersecurity Fundamentals"
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": ""
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False,
                        "audit": True
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False,
                        "audit": True
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False
                    },
                    "number": None
                },
                {
                    "partner": "edx",
                    "run": "3T2017",
                    "user": "edx@example.com",
                    "organization": "RITX",
                    "fields": {
                        "audit": True,
                        "start": "2017-06-19 14:07:40.835573+00:00",
                        "verified": True,
                        "end": "2018-08-18 14:07:40.835529+00:00",
                        "mobile_available": True,
                        "display_name": None
                    },
                    "enrollment": {
                        "credit-provider": "test-credit-provider",
                        "credit": False,
                        "audit": True
                    },
                    "number": None
                }
            ]
        }

        self.assertEquals(actual_output, expected_output)

if __name__ == '__main__':
    unittest.main()
