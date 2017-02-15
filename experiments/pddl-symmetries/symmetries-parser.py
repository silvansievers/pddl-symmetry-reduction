#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generator_count_lifted', 'Number of lifted generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_lifted_mapping_objects_predicates', 'Number of lifted generators mapping predicates or objects: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_2', 'Lifted generator order 2: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_3', 'Lifted generator order 3: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_4', 'Lifted generator order 4: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_5', 'Lifted generator order 5: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_6', 'Lifted generator order 6: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_7', 'Lifted generator order 7: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_8', 'Lifted generator order 8: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_9', 'Lifted generator order 9: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_max', 'Maximum generator order: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_grounded', 'Number of remaining grounded generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_count_removed', 'Number of removed generators: (\d+)', required=False, type=int)
parser.add_pattern('time_bliss', 'Done searching for automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('time_translate_automorphisms', 'Done translating automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('generator_order_grounded_2', 'Grounded generator order 2: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_3', 'Grounded generator order 3: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_4', 'Grounded generator order 4: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_5', 'Grounded generator order 5: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_6', 'Grounded generator order 6: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_7', 'Grounded generator order 7: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_8', 'Grounded generator order 8: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_grounded_9', 'Grounded generator order 9: (\d+)', required=False, type=int)

def add_lifted_grounded(content, props):
    generator_count_lifted = props.get('generator_count_lifted', 0)
    generator_count_grounded = props.get('generator_count_grounded', 0)
    props['generator_count_lifted_grounded'] = "{}/{}".format(generator_count_lifted, generator_count_grounded)

parser.add_function(add_lifted_grounded)

def parse_generator_orders(content, props):
    lifted_generator_orders = re.findall(r'Lifted generator orders: \[(.*)\]', content)
    props['generator_orders_lifted'] = lifted_generator_orders
    lifted_generator_orders_list = re.findall(r'Lifted generator orders list: \[(.*)\]', content)
    props['generator_orders_lifted_list'] = lifted_generator_orders
    grounded_generator_orders = re.findall(r'Grounded generator orders: \[(.*)\]', content)
    props['generator_orders_grounded'] = grounded_generator_orders
    grounded_generator_orders_list = re.findall(r'Grounded generator orders list: \[(.*)\]', content)
    props['generator_orders_grounded_list'] = grounded_generator_orders_list

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
    generator_lifted_affecting_actions_axioms = False
    generator_lifted_mapping_actions_axioms = False
    generator_not_well_defined_for_search = False
    for line in lines:
        if 'Generator affects operator or axiom' in line:
            generator_lifted_affecting_actions_axioms = True
        if 'Generator entirely maps operator or axioms' in line:
            generator_lifted_mapping_actions_axioms = True
        if 'Transformed generator contains -1' in line:
            generator_not_well_defined_for_search = True
    props['generator_lifted_affecting_actions_axioms'] = generator_lifted_affecting_actions_axioms
    props['generator_lifted_mapping_actions_axioms'] = generator_lifted_mapping_actions_axioms
    props['generator_not_well_defined_for_search'] = generator_not_well_defined_for_search

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

def check_completion(content, props):
    translator_time_done = props.get('translator_time_done', None)
    translator_completed = False
    if translator_time_done is not None:
        translator_completed = True
    props['translator_completed'] = translator_completed

parser.add_function(check_completion)

parser.parse()
