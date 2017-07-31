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
import sys

# course defaults
course_number = None
course_organization = "RITX"
course_run = "3T2017"
course_user = "edx@example.com"
course_partner = "edx"

# date configurations
future_date = "future"
past_date = "past"

test_courses_file = "test_courses.json"


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed_data_file', help="Input a permutation configuration file")
    parser.add_argument('--fields', nargs="*", action="append", default=None,
                        help="Specify which fields to generate permutations on")

    return parser.parse_args()


def process_field_arguments(parser_args, seed_data_file, field_args):
    try:
        file = open(parser_args.seed_data_file)
        file_data = json.load(file)
        default_data = file_data["default_data"]
        permutation_data = file_data["permutation_data"]
        default_data_keys = permutation_data.keys()
    except IOError:
        print sys.exc_value
        sys.exit()
    except KeyError:
        print("Could not find key {}".format(sys.exc_value))
        sys.exit()

    field_args = {}

    # if no field arguments are given, just return default data
    if not parser_args.fields:
        field_args = file_data["default_data"]
    else:
        num_field_args = len(parser_args.fields[0])
        if (num_field_args > 3):
            raise argparse.ArgumentTypeError("Only a max of 3 fields allowed")
        # add each command line field to fields dict
        for permutation_choices in parser_args.fields:
            for i in range(0, num_field_args):
                try:
                    field_args[permutation_choices[i]] = permutation_data[permutation_choices[i]]
                except KeyError:
                    print "{} is not a field option".format(sys.exc_value)

        # the difference btwn all possible fields and the chosen permutation ones
        default_fields = list(set(default_data_keys) - set(parser_args.fields[0]))

        # add non permutation fields to dict
        for field in default_fields:
            field_args[field] = default_data[field]

    return field_args


def generate_permutations(field_args, index, results, courses_dict, field_values_dict):
    all_permutations_keys = field_args.keys()
    permutation_option = all_permutations_keys[index]
    permutations_values = field_args[permutation_option]

    for permutation_value in permutations_values:
        # add other required default fields to dict
        enrollment_dict = set_course_defaults(courses_dict)
        # add permutation fields to dict
        field_values_dict[permutation_option] = permutation_value
        # generate start and end dates
        generate_date_translation(field_values_dict, permutation_option, permutation_value)

        for permutation_key in all_permutations_keys:
            # add audit and verify fields to dict
            if permutation_key == "audit" and permutation_value == True:
                enrollment_dict["audit"] = permutation_value
            if permutation_key == "verify" and permutation_value == True:
                enrollment_dict["verify"] = True

        if index + 1 < len(all_permutations_keys):
            generate_permutations(field_args, index + 1, results, courses_dict, field_values_dict)

        courses_dict["enrollment"] = enrollment_dict
        courses_dict["fields"] = field_values_dict.copy()
        results.append(courses_dict.copy())

    wrapper_courses_dict = {}  # needed to match course input file creation
    wrapper_courses_dict["courses"] = results

    with open(test_courses_file, "w") as outfile:
        json.dump(wrapper_courses_dict, outfile)


def set_course_defaults(courses_dict):
    courses_dict["number"] = course_number  # will be generated automatically by course creation script
    courses_dict["organization"] = course_organization
    courses_dict["run"] = course_run
    courses_dict["user"] = course_user
    courses_dict["partner"] = course_partner
    # configure enrollment seat settings
    enrollment_dict = {}
    enrollment_dict["credit"] = False
    enrollment_dict["credit_provider"] = "test-credit-provider"
    return enrollment_dict


def generate_date_translation(field_values_dict, permutation_option, permutation_value):
    now = datetime.datetime.now(pytz.UTC)
    if permutation_value == future_date:
        future = str(now + datetime.timedelta(days=365))
        field_values_dict[permutation_option] = future
    if permutation_value == past_date:
        past = str(now - datetime.timedelta(days=60))
        field_values_dict[permutation_option] = past
    if permutation_value == None:
        field_values_dict[permutation_option] = None


def start_field_recursion(process_field_args):
    generate_permutations(process_field_args, 0, [], {}, {})


if __name__ == "__main__":
    args = arg_parse()
    process_field_args = process_field_arguments(args, args.seed_data_file, args.fields)
    start_field_recursion(process_field_args)
