#! /usr/bin/env python

from __future__ import division

import pddl

from collections import defaultdict
from itertools import count, chain
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

import sys
sys.path.append(os.path.join(dir_path, 'pybliss-0.73'))
import pybind11_blissmodule as bliss

import options
import timers

DEBUG = False


class PyblissModuleWrapper:
    """
    Class that collects all vertices and edges of a symmetry graph.
    On demand, it creates the pybliss module and computes the
    automorphisms.
    """
    def __init__(self):
        self.vertex_to_color = {}
        self.edges = set()

    def find_automorphisms(self, time_limit):
        # Create and fill the graph
        graph = bliss.DigraphWrapper()
        for vertex in range(len(self.vertex_to_color)):
        # vertices have numbers 0, 1, 2, ... and we need to traverse them in
        # this order
            graph.add_vertex(self.vertex_to_color[vertex])

        for edge in self.edges:
            assert type(edge) is tuple
            graph.add_edge(edge[0], edge[1])

        # Find automorphisms, use a time limit:
        automorphisms = graph.find_automorphisms(time_limit)

        generators = []
        for aut in automorphisms:
            generators.append(dict(enumerate(aut)))

        return generators

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
        timer = timers.Timer()
        print("Creating abstract structure graph...")
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
        print("Done creating abstract structure graph: %ss" % timer.elapsed_time())
        print("Size of abstract structure graph: {}".format(len(self.asg.vertex_to_color)))


    def find_automorphisms(self, time_limit, write_group_generators):
        timer = timers.Timer()
        print("Searching for generators...")
        automorphisms = self.asg.find_automorphisms(time_limit)
        time = timer.elapsed_time()
        print("Done searching for generators: %ss" % time)
        print("Number of generators: {}".format(len(automorphisms)))

        print("Translating generators...")
        generators = []
        for gen in automorphisms:
            object_mapping = dict()
            predicate_mapping = dict()
            function_mapping = dict()
            variable_mapping = dict()
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
                        if col in self.colors["variable"]:
                            # This assertion does not hold because
                            # symmetries mapping constants also need to
                            # map actions and therefore variables.
                            # assert not self.only_object_symmetries
                            variable_mapping[from_struct] = to_struct
            if self.only_object_symmetries and not object_mapping:
                # We filter symmetries that map actions (and therefore
                # variables) but do not map objects.
                print(f"skipping generator {gen}")
                continue
            assert (object_mapping or predicate_mapping or
                function_mapping or variable_mapping)
            generator = Generator(object_mapping,
                                  predicate_mapping,
                                  function_mapping,
                                  variable_mapping)
            generators.append(generator)
        time = timer.elapsed_time()
        print("Done translating generators: %ss" % time)
        if not self.only_object_symmetries:
            assert len(generators) == len(automorphisms)

        if write_group_generators:
            # To avoid writing large generators, we first compute the set of
            # symbols that is actually affected by any generator and assign
            # them consecutive numbers.
            symbol_to_index = dict()
            symbol_counter = count()
            for g in generators:
                for s in chain(g.object_mapping, g.predicate_mapping,
                               g.function_mapping, g.variable_mapping):
                    if s not in symbol_to_index:
                        symbol_to_index[s] = next(symbol_counter)

            # Then we go over all generators again, writing them out as
            # permutations using the symbol-to-id mapping.
            num_symbols = len(symbol_to_index)
            file = open('generators.py', 'w')
            for g in generators:
                perm = list(range(num_symbols))
                for f,t in chain(g.object_mapping.items(),
                    g.predicate_mapping.items(),
                    g.function_mapping.items(),
                    g.variable_mapping.items()):
                    perm[symbol_to_index[f]] = symbol_to_index[t]
                file.write(str(perm))
                file.write('\n')
            file.close()

        return generators


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

    # NOTE: This type function prevents predicates to be mapped, but it
    # does not prevent actions from being mapped. This is necessary to
    # be able to find symmetries that map constants, which occur in
    # actions that hence also must be mapped. We therefore need to
    # filter out any symmetries that do not map any objects in a
    # post-processing step.
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
        result = [actions, axioms, init]
        if not exclude_goal:
            result.append(as_for_goal())

        return tuple(result)


class Generator:
    def __init__(self, objects, predicates, functions, variables):
        self.object_mapping = objects
        self.predicate_mapping = predicates
        self.function_mapping = functions
        self.variable_mapping = variables

    def apply_to_atom(self, atom):
        # If no entry is present, use identity mapping.
        predicate = self.predicate_mapping.get(atom.predicate, atom.predicate)
        args = tuple(self.object_mapping.get(a, a) for a in atom.args)
        return pddl.Atom(predicate, args)

    def dump(self):
        print("Mapping objects: {}; Mapping predicates: {}; Mapping functions: {}; Mapping variables: {}".format(
            self.object_mapping, self.predicate_mapping, self.function_mapping,
            self.variable_mapping))


def compute_generators(task):
    if DEBUG:
        task.dump()
    graph = SymmetryGraph(task,
        exclude_goal=options.do_not_stabilize_goal,
        only_static_initial_state=options.do_not_stabilize_initial_state,
        only_object_symmetries=options.only_object_symmetries)
    generators = graph.find_automorphisms(options.bliss_time_limit,
        options.write_group_generators)
    if DEBUG:
        for num, gen in enumerate(generators):
            print("Generator #{}".format(num + 1))
            gen.dump()
    if options.write_dot_graph:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f)
        f.close()
    if generators:
        symmetries_only_affect_objects = True
        symmetries_only_affect_predicates = True
        symmetries_only_affect_functions = True
        for generator in generators:
            if generator.object_mapping:
                symmetries_only_affect_predicates = False
                symmetries_only_affect_functions = False
            if generator.predicate_mapping:
                symmetries_only_affect_objects = False
                symmetries_only_affect_functions = False
            if generator.function_mapping:
                symmetries_only_affect_objects = False
                symmetries_only_affect_predicates = False
        if symmetries_only_affect_objects:
            print("Symmetries only affect objects")
        if symmetries_only_affect_predicates:
            print("Symmetries only affect predicates")
        if symmetries_only_affect_functions:
            print("Symmetries only affect functions")
    return generators


def compute_transpositions(generators):
    transpositions = []
    for generator in generators:
        if not generator.predicate_mapping and not generator.function_mapping and len(generator.object_mapping) == 2:
            transpositions.append(generator)
    return transpositions


def compute_symmetric_object_sets(objects, transpositions, atoms=[]):
    print("Number of transpositions: {}".format(len(transpositions)))
    symmetric_object_sets = set([frozenset([obj.name]) for obj in objects])
    for transposition in transpositions:
        mapped_objects = list(transposition.object_mapping.keys())
        assert len(mapped_objects) == 2
        # print(mapped_objects)

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

    # print(f"Symmetric object sets: {symmetric_object_sets}")

    # Filter symmetric object sets that consist of only
    # one object or whose objects are not part of any
    # reachable atom.
    non_trivial_symmetric_object_sets = []
    for symmetric_object_set in symmetric_object_sets:
        if len(symmetric_object_set) > 1:
            if atoms:
                for atom in atoms:
                    if any(obj in symmetric_object_set for obj in atom.args):
                        non_trivial_symmetric_object_sets.append(symmetric_object_set)
                        break
            else:
                non_trivial_symmetric_object_sets.append(symmetric_object_set)
    print(f"Number of non-trivial symmetric object sets: {len(non_trivial_symmetric_object_sets)}")
    print(f"Non-trivial symmetric object sets: {non_trivial_symmetric_object_sets}")
    return non_trivial_symmetric_object_sets

################# Code related to grounding symmetries ################

def is_identity(sas_generator):
    for key in sas_generator.keys():
        if sas_generator[key] != key:
            return False
    return True


def is_permutation(sas_generator):
    # Caution! If the given sas_generator maps two keys to the same value,
    # this check may fail and loop forever.
    for start_key in sas_generator.keys():
        current_key = sas_generator[start_key]
        while current_key != start_key:
            if not current_key in sas_generator.keys():
                return False
            current_key = tuple(sas_generator[current_key])
    return True


def print_sas_generator(sas_generator):
    for from_fact in sorted(sas_generator.keys()):
        to_fact = sas_generator[from_fact]
        if from_fact != to_fact:
            print("{} -> {}".format(from_fact, sas_generator[from_fact]))


def filter_out_identities_or_nonpermutations(sas_generators):
    # Return an updated list of generators, containing only "valid" generators,
    # i.e. generators that are a permutation and not the identity.
    remaining_generators = []
    for sas_generator in sas_generators:
        if is_identity(sas_generator):
            if DEBUG:
                print(sas_generator)
                print("is the identiy!")
        elif not is_permutation(sas_generator):
            if not options.do_not_stabilize_initial_state:
                assert False
            elif DEBUG:
                print(sas_generator)
                print("is not a permutation!")
        else:
            remaining_generators.append(sas_generator)
    if DEBUG:
        for sas_generator in sas_generators:
            print("generator: ")
            print_sas_generator(sas_generator)
    return remaining_generators


def ground_generators(generators):
    # For each generator, create its sas mapping from var-vals to var-vals
    sas_generators = []
    for generator in generators:
        if DEBUG:
            print("Considering generator: ")
            generator.dump()
        sas_generator = {}
        valid_generator = True
        for atom, var_val_list in strips_to_sas.items():
            if not len(var_val_list) == 1:
                raise NotImplementedError("Using the option --full-encoding "
                "with --compute-symmetries is not implemented!")
            mapped_atom = generator.apply_to_atom(atom)
            mapped_var_val_list = strips_to_sas.get(mapped_atom, None)
            if DEBUG:
                if atom != mapped_atom:
                    print("mapping atom {} to atom {}".format(atom, mapped_atom))
            if mapped_var_val_list is None:
                if DEBUG:
                    print("need to skip generator because it maps an atom to some "
                        "atom which does not exist in the sas representation")
                if not options.do_not_stabilize_initial_state:
                    assert False
                valid_generator = False
                break
            if not len(mapped_var_val_list) == 1:
                raise NotImplementedError("Using the option --full-encoding "
                "with --compute-symmetries is not implemented!")
            mapped_var_val = mapped_var_val_list[0]
            var_val = var_val_list[0]
            sas_generator[var_val] = mapped_var_val
        if valid_generator:
            if DEBUG:
                print("Transformed generator (without none-of-those values!): ")
                print_sas_generator(sas_generator)
            assert is_permutation(sas_generator)
            if not is_identity(sas_generator):
                sas_generators.append(sas_generator)
            elif DEBUG:
                print("need to skip generator because it is the identiy")
    return sas_generators


def add_none_of_those_and_filter_sas_generators(sas_task, sas_generators):
    # Go over all facts of the sas task and all generators:
    # 1) If the option is set, add mappings for none-of-those values.
    # 2) Remove all facts from the generators that are not present in
    # the task anymore.
    facts = []
    for var, var_range in enumerate(sas_task.variables.ranges):
        for val in range(var_range):
            facts.append((var, val))
    for sas_generator in sas_generators:
        if options.add_none_of_those_mappings:
            # 1) For each var, set the mapping for the none-of-those value.
            # If the var is mapped to another var, map to the other var's
            # none-of-those value. Otherwise, map to itself.
            for from_var, var_range in enumerate(sas_task.variables.ranges):
                from_fact = (from_var, 0) # some fact for var
                to_fact = sas_generator.get(from_fact, None)
                assert to_fact is not None
                to_var = to_fact[0]

                none_of_those_from_fact = (from_var, var_range - 1)
                assert sas_generator.get(none_of_those_from_fact, None) is None
                assert sas_task.variables.ranges[from_var] == sas_task.variables.ranges[to_var]
                none_of_those_to_fact = (to_var, var_range - 1)

                sas_generator[none_of_those_from_fact] = none_of_those_to_fact
        # 2) remove facts that have been removed
        for from_var_val, to_var_val in sas_generator.items():
            if from_var_val not in facts or to_var_val not in facts:
                del sas_generator[from_var_val]
    sas_generators = filter_out_identities_or_nonpermutations(sas_generators)
    if DEBUG:
        for sas_generator in sas_generators:
            print("generator: ")
            print_sas_generator(sas_generator)
    return sas_generators


def compute_search_generators(sas_task, sas_generators):
    # Transform the sas generators into the format used by the search
    # component, i.e. [0...n-1; 0...range(var-1)-1, ..., 0...range(var-n)-1]
    # where the first n entries represent the mapping on variables, and
    # successive block represent the mapping of each variable's values.
    # For none-of-those-values, we use -1 to denote that the symmetry
    # is not defined for these.

    # Precompute some data structures to ease mapping from facts to indices
    # of the above representation.
    var_by_shifted_index = []
    var_to_start_index = []
    num_vars = len(sas_task.variables.ranges)
    num_indices = num_vars
    for var in range(num_vars):
        var_to_start_index.append(num_indices)
        num_indices += sas_task.variables.ranges[var]
        for val in range(sas_task.variables.ranges[var]):
            var_by_shifted_index.append(var)

    def get_var_val_by_index(index):
        assert index >= num_vars
        var =  var_by_shifted_index[index - num_vars]
        val = index - var_to_start_index[var]
        return (var, val)

    def get_index_by_var_val(var, val):
        index = var_to_start_index[var] + val
        assert num_vars <= index < num_indices
        return index

    facts = []
    for var, var_range in enumerate(sas_task.variables.ranges):
        for val in range(var_range):
            facts.append((var, val))
    search_generators = []
    for gen_no, sas_generator in enumerate(sas_generators):
        transformed_generator = [-1 for x in range(num_indices)]
        for from_fact in facts:
            to_fact = sas_generator.get(from_fact, None)
            if to_fact is None:
                continue
            from_index = get_index_by_var_val(*from_fact)
            to_index = get_index_by_var_val(*yto_fact)
            transformed_generator[from_index] = to_index

            from_var = from_fact[0]
            to_var = to_fact[0]
            if transformed_generator[from_var] == -1:
                transformed_generator[from_var] = to_var
            else:
                assert transformed_generator[from_var] == to_var
        if -1 in transformed_generator:
            print("Transformed generator contains -1")
            assert not options.add_none_of_those_mappings

        search_generators.append(transformed_generator)
        #for from_index, to_index in enumerate(transformed_generator):
            #if from_index < num_vars:
                #continue
            #from_fact = get_var_val_by_index(from_index)
            #to_fact = get_var_val_by_index(to_index)
            #assert sas_generator.get(from_fact, from_fact) == to_fact
        if DEBUG:
            print("original generator number {}:".format(gen_no))
            print_sas_generator(sas_generator)
            print("transformed_generator number {}:".format(gen_no))
            print(transformed_generator)
    # Append the transformed generators to the task so that they are
    # written to the output.sas file.
    sas_task.search_generators = sas_tasks.SearchGenerators(
        var_by_shifted_index, var_to_start_index, search_generators)


import normalize
import pddl_parser

if __name__ == "__main__":
    task = pddl_parser.open()
    normalize.normalize(task)
#    task.dump()
    generators = compute_generators(task)
    for num, gen in enumerate(generators):
        print("Generator #{}".format(num + 1))
        gen.dump()
    if options.write_dot_graph:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f)
        f.close()
    sys.stdout.flush()
