#! /usr/bin/env python

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generators_count', 'Number of generators: (\d+)', required=False, type=int)
parser.add_pattern('generators_identity_count', 'Number of identity generators \(on states, not on operators\): (\d+)', required=False, type=int)
parser.add_pattern('generators_orders', 'Order of generators: \[(.*)\]', required=False, type=str)
parser.add_pattern('symmetry_graph_size', 'Size of the grounded symmetry graph: (\d+)', required=False, type=int)
parser.add_pattern('time_symmetries', 'Done initializing symmetries: (.+)s', required=False, type=float)
parser.add_pattern('symmetry_group_order', 'Symmetry group order: (\d+)', required=False, type=int)

parser.parse()
