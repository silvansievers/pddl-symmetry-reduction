#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generator_count_lifted', 'Number of raw generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_lifted_interesting', 'Number of interesting generators: (\d+)', required=False, type=int)
parser.add_pattern('time_symmetries1_symmetry_graph', 'Done creating abstract structure graph: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetries2_bliss', 'Done searching for generators: (.+)s', required=False, type=float)
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
    generator_lifted_affecting_actions_axioms = False
    generator_lifted_mapping_actions_axioms = False
    generator_not_well_defined_for_search = False
    ignore_none_of_those_mapping = False
    simplify_var_removed = False
    simplify_val_removed = False
    reorder_var_removed = False
    lines = content.split('\n')
    for line in lines:
        if 'Bliss memory out' in line:
            bliss_memory_out = True

        if 'Bliss timeout' in line:
            bliss_timeout = True

    props['bliss_out_of_memory'] = bliss_memory_out
    props['bliss_out_of_time'] = bliss_timeout

parser.add_function(parse_boolean_flags)

def parse_memory_error(content, props):
    translate_out_of_memory = False
    lines = content.split('\n')
    for line in lines:
        if line == 'MemoryError':
            translate_out_of_memory = True
    props['translate_out_of_memory'] = translate_out_of_memory

parser.add_function(parse_memory_error, file='run.err')

def duplicate_attribute(content, props):
    props['time_symmetries'] = props.get('translator_time_symmetries_computing_symmetries', None)

parser.add_function(duplicate_attribute)

parser.parse()
