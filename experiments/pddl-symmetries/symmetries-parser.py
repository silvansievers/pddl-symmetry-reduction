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

parser.parse()
