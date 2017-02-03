#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries_module import SymmetryGraph
import sys

WRITE_DOT_GRAPH = True

if __name__ == "__main__":
    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = options.stabilize_initial_state
    time_limit = options.bliss_time_limit
    task = pddl_parser.open()
    normalize.normalize(task)
    task.dump()
    graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state)
    if WRITE_DOT_GRAPH:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    automorphisms = graph.find_automorphisms(time_limit)
    graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=True)
    sys.stdout.flush()

