#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries import create_abstract_structure, build_type_function, build_type_function_only_object_symmetries, get_abstract_structure_graph, print_generator, write_dot_graph
import sys

WRITE_DOT_GRAPH = True

if __name__ == "__main__":
    task = pddl_parser.open()
    normalize.normalize(task)
#    task.dump()
    abstract_structure = create_abstract_structure(task, options.do_not_stabilize_goal, options.do_not_stabilize_initial_state)
    if options.only_object_symmetries:
        type_function = build_type_function_only_object_symmetries(task)
    else:
        type_function = build_type_function(task)
    graph, vertex_no_to_structure = get_abstract_structure_graph(abstract_structure, type_function)
    generators = graph.find_automorphisms(options.bliss_time_limit, options.write_group_generators)
    for g in generators:
        print_generator(g, vertex_no_to_structure)
        print("")
        print("")
    f = open('out.dot', 'w')
    write_dot_graph(graph, vertex_no_to_structure, f)
    f.close()
    sys.stdout.flush()
