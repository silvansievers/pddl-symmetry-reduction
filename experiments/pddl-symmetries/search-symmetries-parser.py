#! /usr/bin/env python

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generators_count', 'Number of generators: (\d+)', required=False, type=int)
parser.add_pattern('generators_orders', 'Order of generators: \[(.*)\]', required=False, type=str)
parser.add_pattern('time_symmetries', 'Done initializing symmetries: (.+)s', required=False, type=float)

parser.parse()
