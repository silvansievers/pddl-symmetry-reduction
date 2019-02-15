#! /usr/bin/env python

from __future__ import division

import pddl

from collections import defaultdict
from itertools import count
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

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


class SymmetryGraph:
    def __init__(self, task, exclude_goal=False,
                 only_static_initial_state=False, only_object_symmetries=False):
        self.task = task
        self.only_object_symmetries = only_object_symmetries
        self.abstract_structure = self._abstract_structure(exclude_goal,
                                                           only_static_initial_state)
        self.colors = None
        if only_object_symmetries:
            self.type_mapping = self._build_type_function_only_object_symmetries()
        else:
            self.type_mapping = self._build_type_function()
        self.asg, self.vertex_no_to_structure = self._abstract_structure_graph()

    
    def find_automorphisms(self, time_limit, write_group_generators):
        automorphisms = self.asg.find_automorphisms(time_limit, write_group_generators)
        generators = []
        for gen in automorphisms:
            object_mapping = dict()
            predicate_mapping = dict()
            function_mapping = dict()
            for from_vertex, to_vertex in gen.items():
                from_struct = self.vertex_no_to_structure.get(from_vertex)
                to_struct = self.vertex_no_to_structure.get(to_vertex)
                if from_struct != to_struct:
                    assert type(from_struct) == type(to_struct)
                    if (not isinstance(from_struct, tuple) and 
                        not isinstance(from_struct, frozenset)):
                        # some symbol...
                        assert self.type_mapping(from_struct) == self.type_mapping(to_struct)
                        col = self.type_mapping(from_struct)
                        if col in self.colors["object"]:
                            object_mapping[from_struct] = to_struct 
                        if col in self.colors["predicate"]:
                            assert not self.only_object_symmetries
                            predicate_mapping[from_struct] = to_struct 
                        if col in self.colors["function"]:
                            assert not self.only_object_symmetries
                            function_mapping[from_struct] = to_struct
            if object_mapping or predicate_mapping or function_mapping:
                generator = Generator(object_mapping,
                                      predicate_mapping,
                                      function_mapping)
                generators.append(generator) 
        return generators


    def print_generator(self, generator):
        keys = sorted(generator.keys())
        for from_vertex in keys:
            to_vertex = generator[from_vertex]
            from_struct = self.vertex_no_to_structure.get(from_vertex)
            to_struct = self.vertex_no_to_structure.get(to_vertex)
            if from_struct != to_struct:
                assert type(from_struct) == type(to_struct)
                if (not isinstance(from_struct, tuple) and 
                    not isinstance(from_struct, frozenset)):
                    print ("%s => %s" % (from_struct, to_struct))

    # we only properly support graphs with standard type function. For the one
    # allowing only object symmetries, only the colors up to color 2 make sense.
    def write_dot_graph(self, file):
        """Write the graph into a file in the graphviz dot format."""
        def dot_label(node):
            structure = self.vertex_no_to_structure.get(node)
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
        for vertex, color in self.asg.vertex_to_color.items():
            color_tuple = colors.get(color)
            if color_tuple is None:
                color_tuple = all_other_colors
            dot_color_scheme = color_tuple[0]
            dot_color = color_tuple[1]
            file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
                (vertex, dot_label(vertex), dot_color_scheme, dot_color))
        for edge in self.asg.edges:
            file.write("\"%s\" -> \"%s\";\n" % (edge[0], edge[1]))
        file.write("}\n")


    def _abstract_structure_graph(self):
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
                graph.add_vertex(no, self.type_mapping(struct))
            vertex_no_to_structure[no] = struct
            structure_to_no[struct] = no
            return no
        
        graph = PyblissModuleWrapper()
        vertex_counter = count()
        vertex_no_to_structure = dict()
        structure_to_no = dict()
        process_structure(self.abstract_structure)
        return graph, vertex_no_to_structure


    def _build_type_function(self):
        assert self.colors is None
        (OBJECT, VARIABLE, NEGATION, PREDICATE, FUNCTION, FIRST_NUMBER) = range(6)
        self.colors = defaultdict(set)
        self.colors["object"].add(OBJECT)
        self.colors["variable"].add(VARIABLE)
        self.colors["predicate"].add(PREDICATE)
        self.colors["function"].add(FUNCTION)
        
        type_dict = dict()
        type_dict["!"] = NEGATION
        for obj in self.task.objects:
            type_dict[obj.name] = OBJECT
        for t in self.task.types:
            type_dict[t.name] = PREDICATE
        for predicate in self.task.predicates:
            type_dict[predicate.name] = PREDICATE
        for function in self.task.functions:
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

    # TODO this type function prevent predicates to be mapped but it can for example
    # not filter swaps duplicate operators. However, we also want to allow
    # object symmetries to map actions. So we probably need to filter for symmetries
    # that do not map any object in a post-processing step.
    def _build_type_function_only_object_symmetries(self):
        assert self.colors is None
        (OBJECT, VARIABLE, NEGATION) = range(3)
        self.colors = defaultdict(set)
        self.colors["object"].add(OBJECT)
        self.colors["variable"].add(VARIABLE)
       
        counter = count(3)
        type_dict = dict()
        type_dict["!"] = NEGATION
        for obj in self.task.objects:
            type_dict[obj.name] = OBJECT
        for t in self.task.types:
            type_dict[t.name] = next(counter)
            self.colors["predicate"].add(type_dict[t.name])
        for predicate in self.task.predicates:
            type_dict[predicate.name] = next(counter)
            self.colors["predicate"].add(type_dict[predicate.name])
        for function in self.task.functions:
            type_dict[function.name] = next(counter)
            self.colors["function"].add(type_dict[function.name])
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


    def _abstract_structure(self, exclude_goal, only_static_initial_state):

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
                for action in self.task.actions:
                    for effect in action.effects:
                        fluent_predicates.add(effect.literal.predicate)
                for axiom in self.task.axioms:
                    fluent_predicates.add(axiom.name)
            for entry in self.task.init:
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
        
            for obj in self.task.objects:
                if obj.type_name != "object":
                    result.append((obj.type_name, obj.name))
            return frozenset(result)
        
        def as_for_goal():
            result = []
            if isinstance(self.task.goal, pddl.Conjunction):
                for literal in self.task.goal.parts:
                    result.append(as_for_literal(literal))
            elif isinstance(self.task.goal, pddl.Literal):
                result.append(as_for_literal(self.task.goal))
            else:
                assert False
            return frozenset(result)

        def as_for_actions():
            result = []
            for action in self.task.actions:
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
            for axiom in self.task.axioms:
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
        
        counter = count()
        
        init = as_for_initial_state()
        actions = as_for_actions()
        axioms = as_for_axioms()
        if exclude_goal:
            return (actions, axioms, init)
        else:
            return (actions, axioms, init, as_for_goal())


class Generator:
    def __init__(self, objects, predicates, functions):
        self.object_mapping = objects
        self.predicate_mapping = predicates
        self.function_mapping = functions

    def apply_to_atom(self, atom):
        # If no entry is present, use identity mapping.
        predicate = self.predicate_mapping[0].get(atom.predicate, atom.predicate)
        args = tuple(self.object_mapping.get(a, a) for a in atom.args)
        return pddl.Atom(predicate, args)

    def dump(self):
        print("Mapping objects: {}; Mapping predicates: {}; Mapping functions: {}".format(self.object_mapping, self.predicate_mapping, self.function_mapping))
