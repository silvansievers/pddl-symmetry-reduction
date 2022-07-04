#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('time_bounds_and_subsets', 'Total time to compute bounds and determine subsets of symmetric object sets: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_program', 'Time to generate prolog program: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_model', 'Time to compute model of prolog program: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_expand', 'Time to expand reduced model: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_program', 'Time to compute h2 mutexes reachability program: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_model', 'Time to compute model of reachability program: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_expand', 'Time to expand h2 mutexes: (.+)s', required=False, type=float)
parser.add_pattern('num_used_symmetric_object_sets', 'Number of symmetric object sets used for symmetry reduction: (\d+)', required=False, type=int)
parser.add_pattern('num_reachable_pairs', 'Found (\d+) reachable pairs of literals', required=False, type=int)
parser.add_pattern('num_unreachable_pairs', 'Found (\d+) unreachable pairs of literals', required=False, type=int)
parser.add_pattern('num_expanded_unreachable_pairs', 'Expanded h2 mutex pairs to (\d+)', required=False, type=int)

def parse_boolean_flags(content, props):
    performed_reduction = False
    if props.get('num_used_symmetric_object_sets', 0):
        performed_reduction = True
    props['performed_reduction'] = performed_reduction

parser.add_function(parse_boolean_flags)

parser.parse()
