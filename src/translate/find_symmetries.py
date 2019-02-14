#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries import SymmetryGraph
import sys

WRITE_DOT_GRAPH = True

if __name__ == "__main__":
    task = pddl_parser.open()
    normalize.normalize(task)
#    task.dump()
    graph = SymmetryGraph(task, options.do_not_stabilize_goal,
                          options.do_not_stabilize_initial_state,
                          options.only_object_symmetries)
    generators = graph.find_automorphisms(options.bliss_time_limit, options.write_group_generators)
    for g in generators:
        graph.print_generator(g)
        print("")
        print("")
    if WRITE_DOT_GRAPH:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f)
        f.close()
    sys.stdout.flush()
