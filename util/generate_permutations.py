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
    parser.add_argument('--fields', nargs=3, action="append", default=None,
                        help="Specify which fields to generate permutations on")
    parser.add_argument('filename')
    args = parser.parse_args()

    file = open(args.filename)
    permutation_data = json.load(file)
    first_field = permutation_data
    second_field = permutation_data
    third_field = permutation_data

    # if no field arguments are given, just print out default data
    if not args.fields:
        default_permutation = permutation_data["default_data"]
        print default_permutation
    else:
        for permutation_choices in args.fields:
            first_field = first_field["permutation_data"][permutation_choices[0]]
            second_field = second_field["permutation_data"][permutation_choices[1]]
            third_field = third_field["permutation_data"][permutation_choices[2]]
            
    return first_field, second_field, third_field




def generate_permutations(fields):
    #permutation_generation = [first_field, second_field, third_field]
    print list(product(*fields))
    # print fields



if __name__ == "__main__":
    parse_field_arguments()
    generate_permutations(parse_field_arguments())
