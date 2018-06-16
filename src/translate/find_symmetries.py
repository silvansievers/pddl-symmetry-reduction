#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries import SymmetryGraph
import sys

WRITE_DOT_GRAPH = True

if __name__ == "__main__":
    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal
    time_limit = options.bliss_time_limit
    compute_order = options.compute_order
    task = pddl_parser.open()
    normalize.normalize(task)
    task.dump()
    graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.add_mutex_groups:
        print("cannot add mutex groups -- translator is not run!")
        exit(1)
    if WRITE_DOT_GRAPH:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    automorphisms = graph.find_automorphisms(time_limit, compute_order)
    graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=True)
    sys.stdout.flush()

