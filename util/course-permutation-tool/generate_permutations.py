#!/usr/bin/env python
#
# Create a file of course permutations based on permutations.json file configuration. A max
# of 3 fields can be chosen to build permutations on, and only the fields under
# "permutation_data" are eligible. No field input pulls from "default_data"
#
# ./generate_permutations.py --seed_data_file permutations.json --fields field1 field2 field3

import argparse
import json
import datetime
import pytz

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed_data_file', help="Input a permutation configuration file")
    parser.add_argument('--fields', nargs="*", action="append", default=None,
                        help="Specify which fields to generate permutations on")

    return parser.parse_args()


def parse_field_arguments():
    file = open(num_args.seed_data_file)
    file_data = json.load(file)

    default_data = file_data["default_data"]

    if not default_data:
        raise argparse.ArgumentTypeError("Default_data object needed")
    permutation_data = file_data["permutation_data"]

    default_data_keys = permutation_data.keys()

    fields = {}

    # if no field arguments are given, just return default data
    if not num_args.fields:
        default_permutation = file_data["default_data"]
        fields = default_permutation
    else:
        field_length = len(num_args.fields[0])

        if (field_length > 3):
            raise argparse.ArgumentTypeError("Only a max of 3 fields allowed")
        # add each command line field to fields dict
        for permutation_choices in num_args.fields:
            for i in range(0, field_length):
                fields[permutation_choices[i]] = permutation_data[permutation_choices[i]]

        # the difference btwn all possible fields and the chosen permutation ones
        default_fields = list(set(default_data_keys) - set(num_args.fields[0]))

        # add non permutation fields to dict
        for j in range(0, len(default_fields)):
            fields[default_fields[j]] = default_data[default_fields[j]]

    return fields


def generate_permutations(fields, index, results, courses_dict, fields_dict):
    all_permutations_keys = fields.keys()
    permutation_option = all_permutations_keys[index]
    permutations_values = fields[permutation_option]

    for i in range(len(permutations_values)):
        # add other required default fields to dict
        courses_dict["number"] = None  # will be generated automatically by course creation script
        courses_dict["organization"] = "RITX"
        courses_dict["run"] = "3T2017"
        courses_dict["user"] = "edx@example.com"
        courses_dict["partner"] = "edx"

        # configure enrollment seat settings
        enrollment_dict = {}
        enrollment_dict["credit"] = False
        enrollment_dict["credit_provider"] = "test-credit-provider"

        # add permutation fields to dict
        fields_dict[permutation_option] = permutations_values[i]
        # generate dates
        now = datetime.datetime.now(pytz.UTC)
        if permutations_values[i] == "future":
            future = str(now + datetime.timedelta(days=365))
            fields_dict[permutation_option] = future
        if permutations_values[i] == "past":
            past = str(now - datetime.timedelta(days=60))
            fields_dict[permutation_option] = past
        if permutations_values[i] == None:
            fields_dict[permutation_option] = None
        # add audit and verify fields to dict
        if all_permutations_keys[i] == "audit" and permutations_values[i] == True:
            enrollment_dict["audit"] = permutations_values[i]
        if all_permutations_keys[i] == "verify" and permutations_values[i] == True:
            enrollment_dict["verify"] = True

        if index + 1 < len(all_permutations_keys):
            generate_permutations(fields, index + 1, results, courses_dict, fields_dict)

        courses_dict["enrollment"] = enrollment_dict
        courses_dict["fields"] = fields_dict.copy()
        results.append(courses_dict.copy())

    wrapper_courses_dict = {} # needed to match course input file creation
    wrapper_courses_dict["courses"] = results

    with open("test_courses.json", "w") as outfile:
        json.dump(wrapper_courses_dict, outfile)


if __name__ == "__main__":
    num_args = arg_parse()
    parse_field_arguments()
    generate_permutations(parse_field_arguments(), 0, [], {}, {})
