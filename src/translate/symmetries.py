#! /usr/bin/env python

from __future__ import division

import pddl

from collections import defaultdict
import itertools
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

import Queue

import sys
sys.path.append(os.path.join(dir_path, 'pybliss-0.73'))
import pybind11_blissmodule as bliss

import options
import timers


class PyblissModuleWrapper:
    """
    Class that collects all vertices and edges of a symmetry graph.
    On demand, it creates the pybliss module and computes the
    automorphisms.
    """
    def __init__(self):
        self.vertex_to_color = {}
        self.edges = set()

    def find_automorphisms(self, time_limit, write_group_generators):
        # Create and fill the graph
        timer = timers.Timer()
        print "Creating symmetry graph..."
        graph = bliss.DigraphWrapper()
        print "Size of the lifted symmetry graph: {}".format(len(self.vertex_to_color))
        for vertex in range(len(self.vertex_to_color)):
        # vertices have numbers 0, 1, 2, ... and we need to traverse them in
        # this order
            graph.add_vertex(self.vertex_to_color[vertex])

        for edge in self.edges:
            assert type(edge) is tuple
            graph.add_edge(edge[0], edge[1])
        time = timer.elapsed_time();
        print "Done creating symmetry graph: %ss" % time

        # Find automorphisms, use a time limit:
        timer = timers.Timer()
        print "Searching for autmorphisms..."
        automorphisms = graph.find_automorphisms(time_limit)
        time = timer.elapsed_time()
        print "Done searching for automorphisms: %ss" % time
        print("Number of lifted generators: {}".format(len(automorphisms)))

        if write_group_generators:
            # We write the "un-processed" generators because
            # these are in the right format to be processed by, e.g., sympy
            # to compute the order. We don't do this here to exclude the
            # computational overhead from the translator run.
            file = open('generators.py', 'w')
            for automorphism in automorphisms:
                file.write('[')
                for index, value in enumerate(automorphism):
                    file.write("{}".format(value))
                    if index != len(automorphism) - 1:
                        file.write(', ')
                file.write(']')
                file.write('\n')
            file.close()

        timer = timers.Timer()
        print "Translating automorphisms..."
        generators = []
        for aut in automorphisms:
            generators.append(dict(enumerate(aut)))
        time = timer.elapsed_time()
        print "Done translating automorphisms: %ss" % time

        return generators

    def get_color(self, vertex):
        return self.vertex_to_color[vertex]

    def add_vertex(self, vertex, color):
        vertex = vertex
        # Do nothing if the vertex has already been added
        if vertex in self.vertex_to_color:
            # TODO we could probably instead assert False because it should
            # never happen that we add the same vertex twice
            assert color == self.vertex_to_color[vertex]
            return

        # Add the vertex
        self.vertex_to_color[vertex] = color

    def add_edge(self, vertex1, vertex2):
        assert (vertex1 != vertex2) # we do not support self-loops
        assert vertex1 in self.vertex_to_color
        assert vertex2 in self.vertex_to_color
        self.edges.add((vertex1, vertex2))


def get_mapped_objects(generator):
    keys = sorted(generator.keys())
    mapped_objects = []
    for from_vertex in keys:
        to_vertex = generator[from_vertex]
        if from_vertex != to_vertex and from_vertex[0] == 0:
            mapped_objects.append(from_vertex[1])
    return mapped_objects


def compute_symmetric_object_sets(objects, transpositions):
    timer = timers.Timer()
    symmetric_object_sets = set([frozenset([obj.name]) for obj in objects])
    #print(symmetric_object_sets)
    for transposition in transpositions:
        mapped_objects = get_mapped_objects(transposition)
        assert len(mapped_objects) == 2
        #print(mapped_objects)

        set1 = None
        for symm_obj_set in symmetric_object_sets:
            if mapped_objects[0] in symm_obj_set:
                set1 = frozenset(symm_obj_set)
                symmetric_object_sets.remove(symm_obj_set)
                break
        assert set1 is not None

        set2 = None
        for symm_obj_set in symmetric_object_sets:
            if mapped_objects[1] in symm_obj_set:
                set2 = frozenset(symm_obj_set)
                symmetric_object_sets.remove(symm_obj_set)
                break
        assert set2 is not None

        union = set1 | set2
        symmetric_object_sets.add(union)
    print("Time to compute symmetric object sets: {}s".format(timer.elapsed_time()))
    sys.stdout.flush()
    return symmetric_object_sets


def create_abstract_structure(task, exclude_goal=False, only_static_initial_state=False):

    def as_for_literal(literal, variable_mapping={}):
        res = [literal.predicate]
        res.extend(variable_mapping.get(x,x) for x in literal.args)
        if literal.negated:
            res = ("!", tuple(res))
        else:
            res = tuple(res)
        return res

    def as_for_initial_state():
        result = []
        if only_static_initial_state:
            fluent_predicates = set()
            for action in task.actions:
                for effect in action.effects:
                    fluent_predicates.add(effect.literal.predicate)
            for axiom in task.axioms:
                fluent_predicates.add(axiom.name)
        for entry in task.init:
            if isinstance(entry, pddl.Literal):
                if (not only_static_initial_state or 
                    entry.predicate not in fluent_predicates):
                    result.append(as_for_literal(entry))
            else: # numeric function
                assert(isinstance(entry, pddl.Assign))
                assert(isinstance(entry.fluent, pddl.PrimitiveNumericExpression))
                assert(isinstance(entry.expression, pddl.NumericConstant))
                if entry.fluent.symbol == "total-cost":
                    continue
                function_term = [entry.fluent.symbol]
                function_term.extend(entry.fluent.args)
                result.append((tuple(function_term), entry.expression.value))
    
        for obj in task.objects:
            if obj.type_name != "object":
                result.append((obj.type_name, obj.name))
        return frozenset(result)
    
    def as_for_goal():
        result = []
        if isinstance(task.goal, pddl.Conjunction):
            for literal in task.goal.parts:
                result.append(as_for_literal(literal))
        elif isinstance(task.goal, pddl.Literal):
            result.append(as_for_literal(task.goal))
        else:
            assert False
        return frozenset(result)

    def as_for_actions():
        result = []
        for action in task.actions:
            variable_mapping = dict()
            params = []
            pre = []
            effect = []
            for index, param in enumerate(action.parameters):
                new_var = "?x%s" % next(counter)
                params.append(new_var)
                variable_mapping[param.name] = new_var
                if param.type_name != "object":
                    pre.append((param.type_name, new_var))
            if isinstance(action.precondition, pddl.Conjunction):
                for literal in action.precondition.parts:
                    pre.append(as_for_literal(literal, variable_mapping))
            elif isinstance(action.precondition, pddl.Literal):
                pre.append(as_for_literal(action.precondition, variable_mapping))
            elif isinstance(action.precondition, pddl.Truth):
                pass
            else:
                assert False
            for eff in action.effects:
                effcond = []
                effvars = []
                if eff.parameters:
                    eff_var_mapping = dict(variable_mapping)
                else:
                    eff_var_mapping = variable_mapping
                for param in eff.parameters:
                    new_var = "?x%s" % next(counter)
                    effvars.append(new_var)
                    eff_var_mapping[param.name] = new_var
                    if param.type_name != "object":
                        effcond.append((param.type_name, new_var))
                     
                if isinstance(eff.condition, pddl.Conjunction):
                    for literal in action.precondition.parts:
                        effcond.append(as_for_literal(literal, eff_var_mapping))
                elif isinstance(eff.condition, pddl.Literal):
                    effcond.append(as_for_literal(eff.condition, eff_var_mapping))
                elif isinstance(eff.condition, pddl.Truth):
                    pass
                else:
                    assert False
                literal = as_for_literal(eff.literal, eff_var_mapping)
                effect.append((frozenset(effvars), frozenset(effcond), literal))
            if action.cost:
                val = action.cost.expression
                if isinstance(val, pddl.PrimitiveNumericExpression):
                    cost = [val.symbol]
                    cost.extend(variable_mapping.get(x,x) for x in val.args)
                    cost = tuple(cost)
                else:
                    assert(isinstance(val, pddl.NumericConstant))
                    cost = val.value
            else:
                cost = 1
            result.append((frozenset(params), frozenset(pre), frozenset(effect), cost))
        return frozenset(result)

    def as_for_axioms():
        result = []
        for axiom in task.axioms:
            variable_mapping = dict()
            params = set()
            pre = set()
            effect = [axiom.name]
            for index, param in enumerate(axiom.parameters):
                new_var = "?x%s" % next(counter)
                params.add(new_var)
                if index < axiom.num_external_parameters:
                    effect.append(new_var)
                variable_mapping[param.name] = new_var
                if param.type_name != "object":
                    pre.add((param.type_name, new_var))
            effect = tuple(effect)
            if isinstance(axiom.condition, pddl.Conjunction):
                for literal in axiom.condition.parts:
                    pre.add(as_for_literal(literal, variable_mapping))
            elif isinstance(axiom.condition, pddl.Literal):
                pre.add(as_for_literal(axiom.condition, variable_mapping))
            elif isinstance(axiom.condition, pddl.Truth):
               pass 
            else:
                assert False
            result.append((frozenset(params), frozenset(pre), effect))
        return frozenset(result)
    
    counter = itertools.count()
    
    init = as_for_initial_state()
    actions = as_for_actions()
    axioms = as_for_axioms()
    if exclude_goal:
        return (actions, axioms, init)
    else:
        return (actions, axioms, init, as_for_goal())


# TODO this type function prevent predicates to be mapped but it can for example
# not filter swaps duplicate operators. However, we also want to allow
# object symmetries to map actions. So we probably need to filter for symmetries
# that do not map any object in a post-processing step.
def build_type_function_only_object_symmetries(task):
    (OBJECT, VARIABLE, NEGATION) = range(3)
   
    counter = itertools.count(3)
    type_dict = dict()
    type_dict["!"] = NEGATION
    for obj in task.objects:
        type_dict[obj.name] = OBJECT
    for t in task.types:
        type_dict[t.name] = next(counter)
    for predicate in task.predicates:
        type_dict[predicate.name] = next(counter)
    for function in task.functions:
        type_dict[function.name] = next(counter)
    FIRST_NUMBER = next(counter)

    def get_type(symbol):
        if symbol in type_dict:
            return type_dict[symbol]
        try:
            num = int(symbol)
            return num + FIRST_NUMBER
        except ValueError:
            pass
        assert symbol.startswith("?")
        return VARIABLE

    return get_type


def build_type_function(task):
    (OBJECT, VARIABLE, NEGATION, PREDICATE, FUNCTION, FIRST_NUMBER) = range(6)
    
    type_dict = dict()
    type_dict["!"] = NEGATION
    for obj in task.objects:
        type_dict[obj.name] = OBJECT
    for t in task.types:
        type_dict[t.name] = PREDICATE
    for predicate in task.predicates:
        type_dict[predicate.name] = PREDICATE
    for function in task.functions:
        type_dict[function.name] = FUNCTION

    def get_type(symbol):
        if symbol in type_dict:
            return type_dict[symbol]
        try:
            num = int(symbol)
            return num + FIRST_NUMBER
        except ValueError:
            pass
        assert symbol.startswith("?")
        return VARIABLE

    return get_type


def get_abstract_structure_graph(abstract_structure, get_type):
    SET_COLOR = -1
    TUPLE_COLOR = -2
    AUX_COLOR = -3
    def process_structure(struct):
        if struct in structure_to_no:
            return structure_to_no[struct]
        no = next(vertex_counter)
        if isinstance(struct, tuple):
            graph.add_vertex(no, TUPLE_COLOR)
            curr = no
            for elem in struct:
                child_no = process_structure(elem)
                aux_no = next(vertex_counter)
                graph.add_vertex(aux_no, AUX_COLOR)
                graph.add_edge(aux_no, child_no)
                graph.add_edge(curr, aux_no)
                curr = aux_no
        elif isinstance(struct, frozenset):
            graph.add_vertex(no, SET_COLOR)
            for elem in struct:
                child_no = process_structure(elem)
                graph.add_edge(no, child_no)
        else:
            graph.add_vertex(no, get_type(struct))
        vertex_no_to_structure[no] = struct
        structure_to_no[struct] = no
        return no
    
    graph = PyblissModuleWrapper()
    vertex_counter = itertools.count()
    vertex_no_to_structure = dict()
    structure_to_no = dict()
    process_structure(abstract_structure)
    return graph, vertex_no_to_structure
   

def print_generator(generator, vertex_no_to_structure):
    keys = sorted(generator.keys())
    for from_vertex in keys:
        to_vertex = generator[from_vertex]
        from_struct = vertex_no_to_structure.get(from_vertex)
        to_struct = vertex_no_to_structure.get(to_vertex)
        if from_struct != to_struct:
            assert type(from_struct) == type(to_struct)
            if (not isinstance(from_struct, tuple) and 
                not isinstance(from_struct, frozenset)):
                print ("%s => %s" % (from_struct, to_struct))
   

# we only support graphs with standard type function. For the one allowing only
# object symmetries, only the colors up to color 2 make sense.
def write_dot_graph(graph, vertex_no_to_structure, file):
    """Write the graph into a file in the graphviz dot format."""
    def dot_label(node):
        structure = vertex_no_to_structure.get(node)
        if structure is None or isinstance(structure, tuple) or isinstance(structure, frozenset):
            return ""
        return structure

    colors = {
            -3 : ("X11", "white"),
            -2 : ("X11", "yellow"),
            -1 : ("X11", "green3"),
            0 : ("X11","blue"),
            1 : ("X11", "lightyellow"),
            2 : ("X11", "tomato"),
            3 : ("X11", "orange4"),
            4 : ("X11", "violetred"),
        }

    # we draw numbers with the same color albeit they are actually all
    # different. When only searching for object symmetries, this also covers
    # most predicates and functions (not really supported)
    all_other_colors = ("X11", "gray100")

    file.write("digraph g {\n")
    for vertex, color in graph.vertex_to_color.items():
        color_tuple = colors.get(color)
        if color_tuple is None:
            color_tuple = all_other_colors
        dot_color_scheme = color_tuple[0]
        dot_color = color_tuple[1]
        file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
            (vertex, dot_label(vertex), dot_color_scheme, dot_color))
    for edge in graph.edges:
        file.write("\"%s\" -> \"%s\";\n" % (edge[0], edge[1]))
    file.write("}\n")
