#!/usr/bin/env python
# other comment about how this file works, plus probably an example of implementation

import json
import argparse
from argparse import ArgumentParser
from pprint import pprint
from itertools import product
import sys

def parse_field_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fields', nargs="*", action="append", default=None,
                        help="Specify which fields to generate permutations on")
    parser.add_argument('filename')

    num_args = parser.parse_args()
    field_length = len(num_args.fields[0])
    if (field_length > 3):
        raise argparse.ArgumentTypeError("--fields can only take a max of 3 values")

    file = open(num_args.filename)
    permutation_data = json.load(file)

    fields = {}

    # first_field = permutation_data
    # second_field = permutation_data
    # third_field = permutation_data

    # if no field arguments are given, just print out default data
    if not num_args.fields:
        default_permutation = permutation_data["default_data"]
        print default_permutation
    else:
        for permutation_choices in num_args.fields:
            for i in range(0, field_length):
                fields[permutation_choices[i]] = permutation_data["permutation_data"][permutation_choices[i]]
    return fields


def generate_permutations(fields):
    #permutation_generation = [first_field, second_field, third_field]
     # print list(product(*fields))
     print fields


if __name__ == "__main__":
    parse_field_arguments()
    generate_permutations(parse_field_arguments())
