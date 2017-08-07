#!/usr/bin/env python
# other comment about how this file works, plus probably an example of implementation

import json
from argparse import ArgumentParser
from pprint import pprint
from itertools import product


def parse_args():
    parser = ArgumentParser(description='Create course permutations')
    parser.add_argument('--fields', action='', nargs=3)


def generate_course_permutations():
    with open('permutations.json') as permutation_options:
        permutation_data = json.load(permutation_options)

    start_dates = permutation_data["permutation_data"]["start"]
    availability = permutation_data["permutation_data"]['availability']

    permutation_generation = [start_dates, availability]

    print list(product(*permutation_generation))
