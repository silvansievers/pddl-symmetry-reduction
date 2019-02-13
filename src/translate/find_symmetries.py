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
#    if WRITE_DOT_GRAPH:
#        f = open('out.dot', 'w')
#        graph.write_dot_graph(f, hide_equal_predicates=True)
#        f.close()
#    automorphisms = graph.find_automorphisms(time_limit, write_group_generators)
#    graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=True)
#    sys.stdout.flush()

