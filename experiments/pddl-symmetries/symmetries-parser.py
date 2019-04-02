#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('num_lifted_generators', 'Number of generators: (\d+)', required=False, type=int)
parser.add_pattern('time_symmetries1_symmetry_graph', 'Done creating abstract structure graph: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetries2_bliss', 'Done searching for generators: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetries3_translate', 'Done translating generators: (.+)s', required=False, type=float)
parser.add_pattern('symmetry_graph_size', 'Size of abstract structure graph: (\d+)', required=False, type=int)
parser.add_pattern('symmetry_group_order', 'Symmetry group order: (\d+)', required=False, type=int)

def add_composed_attributes(content, props):
    translator_time_done = props.get('translator_time_done', None)
    translator_completed = False
    if translator_time_done is not None:
        translator_completed = True
    props['translator_completed'] = translator_completed

parser.add_function(add_composed_attributes)

def parse_boolean_flags(content, props):
    bliss_memory_out = False
    bliss_timeout = False
    symmetries_only_affect_objects = False
    symmetries_only_affect_predicates = False
    symmetries_only_affect_functions = False
    lines = content.split('\n')
    for line in lines:
        if 'Bliss memory out' in line:
            bliss_memory_out = True

        if 'Bliss timeout' in line:
            bliss_timeout = True

        if line == 'Symmetries only affect objects':
            symmetries_only_affect_objects = True
        if line == 'Symmetries only affect predicates':
            symmetries_only_affect_predicates = True
        if line == 'Symmetries only affect functions':
            symmetries_only_affect_functions = True

    props['bliss_out_of_memory'] = bliss_memory_out
    props['bliss_out_of_time'] = bliss_timeout
    props['symmetries_only_affect_objects'] = symmetries_only_affect_objects
    props['symmetries_only_affect_predicates'] = symmetries_only_affect_predicates
    props['symmetries_only_affect_functions'] = symmetries_only_affect_functions

parser.add_function(parse_boolean_flags)

def duplicate_attribute(content, props):
    props['time_symmetries'] = props.get('translator_time_symmetries_computing_symmetries', None)

parser.add_function(duplicate_attribute)

parser.parse()
