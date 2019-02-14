#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries import SymmetryGraph, write_dot_graph
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
    f = open('out.dot', 'w')
#    write_dot_graph(graph, vertex_no_to_structure, f)
    f.close()
    sys.stdout.flush()
