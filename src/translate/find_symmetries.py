#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries import SymmetryGraph, create_abstract_structure, build_type_function, get_abstract_structure_graph, print_generator
import sys

WRITE_DOT_GRAPH = True

if __name__ == "__main__":
    task = pddl_parser.open()
    normalize.normalize(task)
#    task.dump()
    abstract_structure = create_abstract_structure(task)
    type_function = build_type_function(task)
    graph, vertex_no_to_structure = get_abstract_structure_graph(abstract_structure, type_function)
    generators = graph.find_automorphisms(500, True)
    for g in generators:
        print_generator(g, vertex_no_to_structure)
        print("")
        print("")

#    only_object_symmetries = options.only_object_symmetries
#    stabilize_initial_state = not options.do_not_stabilize_initial_state
#    stabilize_goal = not options.do_not_stabilize_goal
#    time_limit = options.bliss_time_limit
#    write_group_generators = options.write_group_generators
#    add_object_type_nodes = options.add_object_type_nodes
#    task = pddl_parser.open()
#    normalize.normalize(task)
#    task.dump()
#    graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal, add_object_type_nodes)
#    if options.add_mutex_groups:
#        print("cannot add mutex groups -- translator is not run!")
#        exit(1)
#    if WRITE_DOT_GRAPH:
#        f = open('out.dot', 'w')
#        graph.write_dot_graph(f, hide_equal_predicates=True)
#        f.close()
#    automorphisms = graph.find_automorphisms(time_limit, write_group_generators)
#    graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=True)
#    sys.stdout.flush()

