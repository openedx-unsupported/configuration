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
    if (len(num_args.fields[0]) > 3):
        raise argparse.ArgumentTypeError("--fields can only take a max of 3 values")

    file = open(num_args.filename)
    permutation_data = json.load(file)
    first_field = permutation_data
    second_field = permutation_data
    third_field = permutation_data

    # if no field arguments are given, just print out default data
    if not num_args.fields:
        default_permutation = permutation_data["default_data"]
        print default_permutation
    else:
        for permutation_choices in num_args.fields:
            first_field = first_field["permutation_data"][permutation_choices[0]]
            second_field = second_field["permutation_data"][permutation_choices[1]]
            third_field = third_field["permutation_data"][permutation_choices[2]]

    return first_field, second_field, third_field




def generate_permutations(fields):
    #permutation_generation = [first_field, second_field, third_field]
    # print list(product(*fields))
    print ""


if __name__ == "__main__":
    parse_field_arguments()
    generate_permutations(parse_field_arguments())
