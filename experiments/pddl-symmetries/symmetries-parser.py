#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generator_count_lifted', 'Number of lifted generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_grounded', 'Number of remaining valid generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_removed', 'Removed generators: (\d+)', required=False, type=int)
parser.add_pattern('time_prolog_model', 'Done building program and model: (.+)s', required=False, type=float)
parser.add_pattern('time_bliss', 'Done searching for automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('time_translate_automorphisms', 'Done translating automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('generator_order_2', 'Order 2: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_3', 'Order 3: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_4', 'Order 4: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_5', 'Order 5: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_6', 'Order 6: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_7', 'Order 7: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_8', 'Order 8: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_9', 'Order 9: (\d+)', required=False, type=int)

def add_lifted_grounded(content, props):
    generator_count_lifted = props.get('generator_count_lifted', 0)
    generator_count_grounded = props.get('generator_count_grounded', 0)
    props['generator_count_lifted_grounded'] = "{}/{}".format(generator_count_lifted, generator_count_grounded)

parser.add_function(add_lifted_grounded)

def parse_generator_orders(content, props):
    merge_order = re.findall(r'Generator orders:  \[(.*)\]', content)
    props['generator_orders'] = merge_order

parser.add_function(parse_generator_orders)

def parse_bliss_limits(content, props):
    lines = content.split('\n')
    bliss_memory_out = False
    bliss_timeout = False
    for line in lines:
        if 'Bliss memory out' in line:
            bliss_memory_out = True
            break

        if 'Bliss timeout' in line:
            bliss_timeout = True
            break

    props['bliss_out_of_memory'] = bliss_memory_out
    props['bliss_out_of_time'] = bliss_timeout

parser.add_function(parse_bliss_limits)

def parse_symmetries_time(content, props):
    time_bliss = props.get('time_bliss', 0)
    time_translate_automorphisms = props.get('time_translate_automorphisms', 0)
    props['time_symmetries'] = time_bliss + time_translate_automorphisms

parser.add_function(parse_symmetries_time)

def parse_action_axiom_symmetry(content, props):
    lines = content.split('\n')
    generator_count_affecting_actions_axioms = False
    generator_count_mapping_actions_axioms = False
    for line in lines:
        if 'Generator affects operator or axiom' in line:
            generator_count_affecting_actions_axioms = True
        if 'Generator entirely maps operator or axioms' in line:
            generator_count_mapping_actions_axioms = True
    props['generator_count_affecting_actions_axioms'] = generator_count_affecting_actions_axioms
    props['generator_count_mapping_actions_axioms'] = generator_count_mapping_actions_axioms

parser.add_function(parse_action_axiom_symmetry)

def parse_errors(content, props):
    if 'error' in props:
        return

    # Error names that start with "unexplained" will show up in the errors table.
    exitcode_to_error = {
        0: 'none',
        1: 'unexplained-critical-error',
        232: 'timeout',
        247: 'unexplained-bliss-timeout', # TODO: remove "unexplained" once explained
    }

    exitcode = props['fast-downward_returncode']
    props['timeout'] = False
    if exitcode == 232:
        props['timeout'] = True
    if exitcode in exitcode_to_error:
        props['error'] = exitcode_to_error[exitcode]
    else:
        props['error'] = 'unexplained-exitcode-%d' % exitcode

parser.add_function(parse_errors)

parser.parse()
