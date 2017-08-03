#!/usr/bin/env python
# other comment about how this file works, plus probably an example of implementation

import json
import argparse
from argparse import ArgumentParser
from pprint import pprint
from itertools import product
import sys

# # def parse_args():
# parser = ArgumentParser(description='Create course permutations')
# parser.add_argument('--fields', action='', nargs=3)
#
# def generate_permutations():
#
#     class Permutations(argparse.Action):
#         def __call__(self, parser, args, values, option_string=None):
#             setattr(args, self.dest, values)
#             return Permutations


parser = argparse.ArgumentParser()
#parser.add_argument('--fields', action='generate_permutations', nargs=3)
parser.add_argument('filename')
args = parser.parse_args()

# parser.register('action', 'generate_permutations', GenerationPermutations)
with open(args.filename) as file:
    permutation_data = json.load(file)
    start_dates = permutation_data["permutation_data"]["start"]
    availability = permutation_data["permutation_data"]['availability']
    permutation_generation = [start_dates, availability]
    print list(product(*permutation_generation))
