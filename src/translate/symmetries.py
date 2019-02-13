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

# HACK
GLOBAL_COLOR_COUNT = -1


class PyblissModuleWrapper:
    """
    Class that collets all vertices and edges of a symmetry graph.
    On demand, it creates the pybliss module and computes the
    automorphisms.
    """
    def __init__(self, only_object_symmetries):
        self.vertex_to_color = {}
        self.edges = set()
        # To exclude "="-predicates and all related nodes from dot output
        self.excluded_vertices = set()
        self.only_object_symmetries = only_object_symmetries

    def find_automorphisms(self, time_limit, write_group_generators):
        # Create and fill the graph
        timer = timers.Timer()
        print "Creating symmetry graph..."
        graph = bliss.DigraphWrapper()
        vertices = self.get_vertices()
        print "Size of the lifted symmetry graph: {}".format(len(vertices))
        self.id_to_vertex = []
        self.vertex_to_id = {}
        for id, vertex in enumerate(vertices):
            graph.add_vertex(self.vertex_to_color[vertex])
            self.id_to_vertex.append(vertex)
            assert len(self.id_to_vertex) - 1 == id
            self.vertex_to_id[vertex] = id
        for edge in self.edges:
            assert type(edge) is tuple
            v1 = self.vertex_to_id[edge[0]]
            v2 = self.vertex_to_id[edge[1]]
            graph.add_edge(v1, v2)
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
            # We write the "un-translated" generators on purpose because
            # these are in the right format to be processed by, e.g., sympy
            # to compute the order. We don't do it here to exclude the
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
            generators.append(self._translate_generator(aut))
        time = timer.elapsed_time()
        print "Done translating automorphisms: %ss" % time

        return generators

    def _translate_generator(self, generator):
        result = {}
        for a,b in enumerate(generator):
            if self.id_to_vertex[a] is not None:
                assert (self.id_to_vertex[b] is not None)
                result[self.id_to_vertex[a]] = self.id_to_vertex[b]
        return result

    def get_color(self, vertex):
        return self.vertex_to_color[vertex]

    def add_vertex(self, vertex, color, exclude=False):
        vertex = vertex
        # Do nothing if the vertex has already been added
        if vertex in self.vertex_to_color:
            if not self.only_object_symmetries:
                # This test potentially fails when using object symmetries,
                # because the color manually gets overwritten.
                assert color == self.vertex_to_color[vertex]
            return

        # Update color to a unique number if using object symmetries and not adding an object node
        if self.only_object_symmetries and color not in [Color.constant, Color.init, Color.goal]:
            global GLOBAL_COLOR_COUNT
            assert GLOBAL_COLOR_COUNT != -1
            color = GLOBAL_COLOR_COUNT
            GLOBAL_COLOR_COUNT += 1

        # Add the vertex
        self.vertex_to_color[vertex] = color
        if exclude:
            self.excluded_vertices.add(vertex)

    def add_edge(self, vertex1, vertex2):
        assert (vertex1 != vertex2) # we do not support self-loops
        assert vertex1 in self.vertex_to_color
        assert vertex2 in self.vertex_to_color
        self.edges.add((vertex1, vertex2))

    def get_vertices(self):
        return sorted(self.vertex_to_color.keys())

    def get_successors(self, vertex):
        successors = []
        for edge in self.edges:
            assert type(edge) is tuple
            assert len(edge) == 2
            if edge[0] == vertex:
                successors.append(edge[1])
        return successors

class NodeType:
    """Used by SymmetryGraph to make nodes of different types distinguishable."""
    (constant, init, goal, operator, condition, effect, effect_literal,
    function, axiom, axiom_cond, axiom_eff, predicate, cost, mutex_group,
    number) = range(15)


class Color:
    """Node colors used by SymmetryGraph"""
    # NOTE: it is important that predicate has the highest value. This value is
    # used for predicates of arity 0, predicates of higher arity get assigned
    # subsequent numbers
    (constant, init, goal, operator, condition, effect, effect_literal,
    cost, axiom, axiom_cond, axiom_eff, mutex_group, predicate) = range(13)
    derived_predicate = None # will be set by Symmetry Graph, depending on
                             # the colors required for predicate symbols
    function = None # will be set by Symmetry Graph
    number = None # will be set by Symmetry Graph

class SymmetryGraph:
    def __init__(self, task, only_object_symmetries, stabilize_initial_state, stabilize_goal):
        self.only_object_symmetries = only_object_symmetries
        self.stabilize_initial_state = stabilize_initial_state
        self.stabilize_goal = stabilize_goal
        self.graph = PyblissModuleWrapper(only_object_symmetries)
        self.numbers = set()
        self.constant_functions = dict()
        self.max_predicate_arity = \
            max([len(p.arguments) for p in task.predicates] +
                [int(len(task.types) > 1)])
        self.max_function_arity = max([0] + [len(p.arguments)
                                       for p in task.functions])
        Color.derived_predicate = Color.predicate + self.max_predicate_arity + 1
        Color.function = Color.derived_predicate + self.max_predicate_arity + 1
        Color.number = Color.function + self.max_function_arity + 1
        self.type_dict = dict((type.name, type) for type in task.types)

        if not self.stabilize_initial_state:
            #task_predicate_names = set([predicate.name for predicate in task.predicates])
            self.fluent_predicates = set()
            for action in task.actions:
                for effect in action.effects:
                    self.fluent_predicates.add(effect.literal.predicate)
            for axiom in task.axioms:
                self.fluent_predicates.add(axiom.name)
            #assert self.fluent_predicates.issubset(task_predicate_names)
            #self.static_predicates = task_predicate_names.difference(self.fluent_predicates)

        if self.only_object_symmetries:
            # TODO: are there planning tasks with numbers larger than that?
            global GLOBAL_COLOR_COUNT
            GLOBAL_COLOR_COUNT = Color.number + 10000

        self._add_objects(task)
        self._add_predicates(task)
        self._add_functions(task)
        self._add_init(task)
        if self.stabilize_goal:
            self._add_goal(task)
        self._add_operators(task)
        self._add_axioms(task)

    def _get_number_node(self, no):
        node = (NodeType.number, no)
        if no not in self.numbers:
            self.graph.add_vertex(node, Color.number + len(self.numbers))
            self.numbers.add(no)
        return node

    def _get_obj_node(self, obj_name):
        return (NodeType.constant, obj_name)

    def _get_pred_node(self, pred_name):
        return (NodeType.predicate, pred_name)

    def _get_function_node(self, function_name, arg_index=0):
        return (NodeType.function, function_name, arg_index)

    def _get_structure_node(self, node_type, id_indices, name):
        # name is either the operator or effect name or an argument name. Or an axiom.
        # The argument name is relevant for identifying the node
        assert (node_type in (NodeType.operator, NodeType.effect, NodeType.axiom))
        return (node_type, id_indices, name)

    def _get_literal_node(self, node_type, id_indices, arg_index, name):
        # name is mostly relevant for the dot output. The only exception are
        # init nodes for constant functions, where it is used to distinguish
        # them
        return (node_type, id_indices, arg_index, name)

    def _get_mutex_group_node(self, id_indices):
        return (NodeType.mutex_group, id_indices)

    def _add_objects(self, task):
        """Add a node for each object of the task.

        All nodes have color Color.constant.
        """
        for o in task.objects:
            self.graph.add_vertex(self._get_obj_node(o.name), Color.constant)

    def _add_predicates(self, task):
        """Add nodes for each declared predicate and type predicate.

        For a normal or a derived predicate there is a positive and a negative
        node and edges between them in both directions. For a type predicate
        (that cannot occur as a negative condition) there is only the positive
        node. The nodes have color 'Color.predicate + <arity of the predicate>'
        or 'Color.derived_predicate + <arity of the predicate>'.
        """

        derived_predicates = set(axiom.name for axiom in task.axioms)

        def add_predicate(pred_name, arity, derived):
            pred_node = self._get_pred_node(pred_name)
            if derived:
                color = Color.derived_predicate + arity
            else:
                color = Color.predicate + arity
            exclude_node = pred_name == "="
            self.graph.add_vertex(pred_node, color, exclude_node)

        for pred in task.predicates:
            derived = pred.name in derived_predicates
            add_predicate(pred.name, len(pred.arguments), derived)
        for type in task.types:
            if type.name != "object":
                add_predicate(type.get_predicate_name(), 1, False)

    def _add_functions(self, task):
        """Add a node for each function symbol.

        All functions f of the same arity share the same color
        Color.function + arity(f).
        """
        for function in task.functions:
            if function.name == "total-cost":
                continue
            func_node = self._get_function_node(function.name, 0)
            assert (Color.function is not None)
            self.graph.add_vertex(func_node,
                                  Color.function + len(function.arguments))

    def _add_pne(self, node_type, color, pne, id_indices, param_dicts=()):
        function_node = self._get_function_node(pne.symbol)
        first_node = self._get_literal_node(node_type, id_indices, 0,
                                            pne.symbol)
        self.graph.add_vertex(first_node, color)
        self.graph.add_edge(function_node, first_node)
        prev_node = first_node
        for num, arg in enumerate(pne.args):
            arg_node = self._get_literal_node(node_type, id_indices, num+1, arg)
            self.graph.add_vertex(arg_node, color)
            self.graph.add_edge(prev_node, arg_node)
            # edge from respective parameter or constant to argument
            if arg[0] == "?":
                for d in param_dicts:
                    if arg in d:
                        self.graph.add_edge(d[arg], arg_node)
                        break
                else:
                    assert(False)
            else:
                self.graph.add_edge(self._get_obj_node(arg), arg_node)
            prev_node = arg_node
        return first_node, prev_node

    def _add_literal(self, node_type, color, literal, id_indices, param_dicts=()):
        pred_node = self._get_pred_node(literal.predicate)
        exclude_vertices = pred_node in self.graph.excluded_vertices
        literal_pred_node = self._get_literal_node(node_type, id_indices, 0,
                                                   literal.predicate)
        self.graph.add_vertex(literal_pred_node, color, exclude_vertices)
        self.graph.add_edge(pred_node, literal_pred_node)
        first_node = literal_pred_node
        if literal.negated:
            neg_node = self._get_literal_node(node_type, id_indices, -1, "not")
            self.graph.add_vertex(neg_node, color, exclude_vertices)
            self.graph.add_edge(neg_node, literal_pred_node)
            first_node = neg_node

        prev_node = literal_pred_node
        for num, arg in enumerate(literal.args):
            arg_node = self._get_literal_node(node_type, id_indices, num+1, arg)
            self.graph.add_vertex(arg_node, color, exclude_vertices)
            self.graph.add_edge(prev_node, arg_node)
            # edge from respective parameter or constant to argument
            if arg[0] == "?":
                for d in param_dicts:
                    if arg in d:
                        self.graph.add_edge(d[arg], arg_node)
                        break
                else:
                    assert(False)
            else:
                self.graph.add_edge(self._get_obj_node(arg), arg_node)
            prev_node = arg_node
        return first_node

    def _add_init(self, task):
        def get_key(init_entry):
            if isinstance(init_entry, pddl.Literal):
                return init_entry.key
            elif isinstance(init_entry, pddl.Assign):
                return str(init_entry)
            else:
                assert False
        assert isinstance(task.init, list)
        init = sorted(task.init, key=get_key)
        for no, entry in enumerate(init):
            if isinstance(entry, pddl.Literal):
                if options.only_functions_from_initial_state:
                    continue
                if self.stabilize_initial_state or entry.predicate not in self.fluent_predicates:
                    self._add_literal(NodeType.init, Color.init, entry, (no,))
            else: # numeric function
                assert(isinstance(entry, pddl.Assign))
                assert(isinstance(entry.fluent, pddl.PrimitiveNumericExpression))
                assert(isinstance(entry.expression, pddl.NumericConstant))
                if entry.fluent.symbol == "total-cost":
                    continue
                first, last = self._add_pne(NodeType.init, Color.init, entry.fluent, (no,))
                num_node = self._get_number_node(entry.expression.value)
                self.graph.add_edge(last, num_node)

        if not options.only_functions_from_initial_state:
            # add types
            counter = len(init)
            for o in task.objects:
                the_type = self.type_dict[o.type_name]
                while the_type.name != "object":
                    literal = pddl.Atom(the_type.get_predicate_name(), (o.name,))
                    self._add_literal(NodeType.init, Color.init, literal, (counter,))
                    counter += 1
                    the_type = self.type_dict[the_type.basetype_name]

    def _add_goal(self, task):
        if isinstance(task.goal, pddl.Literal):
            self._add_literal(NodeType.goal, Color.goal, task.goal, (0,))
        elif isinstance(task.goal, pddl.Conjunction):
            for no, fact in enumerate(task.goal.parts):
                self._add_literal(NodeType.goal, Color.goal, fact, (no,))
        else:
            assert isinstance(task.goal, pddl.Truth)

    def _add_condition(self, node_type, color, literal, id_indices,
                       base_node, op_args,
                       eff_args):
        # base node is operator node for preconditions and effect node for
        # effect conditions
        first_node = self._add_literal(node_type, color, literal,
                                       id_indices, (eff_args, op_args))
        self.graph.add_edge(base_node, first_node)

    def _add_conditions(self, node_type, color, params, condition,
        id_indices, base_node, op_args, eff_args=dict()):
        pre_index = 0
        if isinstance(condition, pddl.Literal):
            self._add_condition(node_type, color, condition,
                                id_indices + (pre_index,), base_node,
                                op_args, eff_args)
            pre_index += 1
        elif isinstance(condition, pddl.Conjunction):
            assert isinstance(condition, pddl.Conjunction)
            for literal in condition.parts:
                self._add_condition(node_type, color, literal,
                                    id_indices + (pre_index,),
                                    base_node, op_args, eff_args)
                pre_index += 1
        else:
            assert isinstance(condition, pddl.Truth)

        # condition from types
        for param in params:
            if param.type_name != "object":
                pred_name = self.type_dict[param.type_name].get_predicate_name()
                literal = pddl.Atom(pred_name, (param.name,))
                self._add_condition(node_type, color,literal,
                                    id_indices + (pre_index,), base_node,
                                    op_args, eff_args)
                pre_index += 1

    def _add_structure(self, node_type, id_indices, name, color, parameters):
        main_node = self._get_structure_node(node_type, id_indices, name)
        self.graph.add_vertex(main_node, color);
        args = dict()
        for param in parameters:
            param_node = self._get_structure_node(node_type, id_indices,
                                                  param.name)
            self.graph.add_vertex(param_node, color);
            args[param.name] = param_node
            self.graph.add_edge(main_node, param_node)
        return main_node, args

    def _add_effect(self, op_index, op_node, op_args, eff_index, eff):
        name = "e_%i_%i" % (op_index, eff_index)
        eff_node, eff_args = self._add_structure(NodeType.effect,
                                                 (op_index, eff_index),
                                                  name, Color.effect,
                                                  eff.parameters)
        self.graph.add_edge(op_node, eff_node);

        # effect conditions (also from parameter types)
        self._add_conditions(NodeType.effect, Color.effect,
                             eff.parameters, eff.condition, (op_index,
                             eff_index), eff_node, op_args, eff_args)

        # affected literal
        first_node = self._add_literal(NodeType.effect_literal,
                                       Color.effect_literal, eff.literal,
                                       (op_index, eff_index),
                                       (eff_args, op_args))
        self.graph.add_edge(eff_node, first_node)

    def _add_operators(self, task):
        # We consider operators sorted by name
        actions = sorted(task.actions, key=lambda x:x.name)
        for op_index, op in enumerate(actions):
            op_node, op_args = self._add_structure(NodeType.operator,
                                                   (op_index,), op.name,
                                                   Color.operator,
                                                   op.parameters)
            self._add_conditions(NodeType.condition, Color.condition,
                                 op.parameters, op.precondition, (op_index,),
                                 op_node, op_args)
            # TODO: for reproduciblity, we could also sort the effects
            for no, effect in enumerate(op.effects):
                self._add_effect(op_index, op_node, op_args, no, effect)

            if op.cost:
                val = op.cost.expression
                if isinstance(val, pddl.PrimitiveNumericExpression):
                    c_node, _ = self._add_pne(NodeType.cost, Color.cost, val,
                                              (op_index,), (op_args,))
                else:
                    assert(isinstance(val, pddl.NumericConstant))
                    num_node = self._get_number_node(val.value)
                    if val.value not in self.constant_functions:
                        # add node for constant function
                        assert (Color.function is not None)
                        name = "const@%i" % val.value
                        symbol_node = self._get_function_node(name, 0)
                        self.graph.add_vertex(symbol_node, Color.function)

                        # add structure for initial state
                        id_indices = -1
                        i_node = self._get_literal_node(NodeType.init, id_indices, 0, name)
                        self.graph.add_vertex(i_node, Color.init)
                        self.graph.add_edge(symbol_node, i_node)
                        self.graph.add_edge(i_node, num_node)
                        self.constant_functions[val.value] = (symbol_node, name)
                    sym_node, name = self.constant_functions[val.value]
                    c_node = self._get_literal_node(NodeType.cost, (op_index,),
                                                    0, name)
                    self.graph.add_vertex(c_node, Color.cost)
                    self.graph.add_edge(sym_node, c_node)
                    self.graph.add_edge(c_node, num_node)
                self.graph.add_edge(op_node, c_node)

    def _add_axioms(self, task):
        # We consider axioms sorted by name
        axioms = sorted(task.axioms, key=lambda x: x.name)
        for index, axiom in enumerate(axioms):
            axiom_node, axiom_args = self._add_structure(
                NodeType.axiom, (index,), axiom.name, Color.axiom,
                axiom.parameters)
            self._add_conditions(NodeType.axiom_cond, Color.axiom_cond,
                                 axiom.parameters, axiom.condition,
                                 (index,), axiom_node, axiom_args)

            # TODO: why doesn't an axiom have a simple "effect", i.e.
            # a literal so that we could use _add_literal()? The code
            # below is an adapted copy for _add_literal().
            first_node = self._get_literal_node(
                NodeType.axiom_eff, (index,), 0, axiom.name)
            self.graph.add_vertex(first_node, Color.axiom_eff)
            self.graph.add_edge(axiom_node, first_node)
            derived_pred_node = self._get_pred_node(axiom.name)
            self.graph.add_edge(derived_pred_node, first_node)

            prev_node = first_node
            for num, param in enumerate(axiom.parameters):
                arg = param.name
                arg_node = self._get_literal_node(NodeType.axiom_eff, (index,), num+1, arg)
                self.graph.add_vertex(arg_node, Color.axiom_eff)
                self.graph.add_edge(prev_node, arg_node)
                # edge from respective parameter or constant to argument
                if arg[0] == "?":
                    for d in (axiom_args,):
                        if arg in d:
                            self.graph.add_edge(d[arg], arg_node)
                            break
                    else:
                        assert(False)
                else:
                    self.graph.add_edge(self._get_obj_node(arg), arg_node)
                prev_node = arg_node


    def write_dot_graph(self, file, hide_equal_predicates=False):
        """Write the graph into a file in the graphviz dot format."""
        def dot_label(node):
            if node[0] == NodeType.function:
                if node[-1] == 0:
                    return node[-2]
                elif node[-1] == -1: # val
                    return "%s [val]" % node[-2]
                else:
                    return "%s [%i]" % (node[-2], node[-1])
            return node[-1]

        colors = {
                Color.constant: ("X11","blue"),
                Color.init: ("X11", "lightyellow"),
                Color.goal: ("X11", "yellow"),
                Color.operator: ("X11", "green4"),
                Color.condition: ("X11", "green2"),
                Color.effect: ("X11", "green3"),
                Color.effect_literal: ("X11", "yellowgreen"),
                Color.cost: ("X11", "tomato"),
                Color.axiom: ("X11", "orange4"),
                Color.axiom_cond: ("X11", "orange2"),
                Color.axiom_eff: ("X11", "orange3"),
                Color.mutex_group: ("X11", "violetred"),
            }
        # TODO: these color schemes only work for max arities of at least 3 and at most 9
        vals = self.max_predicate_arity + 1
        for c in range(vals):
            colors[Color.predicate + c] = ("blues%i" % vals, "%i" %  (c + 1))
        vals = self.max_predicate_arity + 1
        for c in range(vals):
            colors[Color.derived_predicate + c] = ("reds%i" % vals, "%i" %  (c + 1))
        vals = self.max_function_arity + 1
        for c in range(vals):
            colors[Color.function + c] = ("oranges%i" % vals, "%i" %  (c + 1))
        for c in range(len(self.numbers) + 1):
            colors[Color.number + c] = ("X11", "gray100")
            # we draw numbers with the same color albeit they are actually all
            # different

        file.write("digraph g {\n")
        if hide_equal_predicates:
            file.write("\"extra\" [style=filled, fillcolor=red, label=\"Warning: hidden =-predicates\"];\n")
        for vertex in self.graph.get_vertices():
            if hide_equal_predicates and vertex in self.graph.excluded_vertices:
                continue
            color = self.graph.get_color(vertex)
            if self.only_object_symmetries and color not in [Color.constant, Color.init, Color.goal]:
                dot_color_scheme = "X11"
                dot_color = "red"
            else:
                dot_color_scheme = colors[color][0]
                dot_color = colors[color][1]
            file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
                (vertex, dot_label(vertex), dot_color_scheme, dot_color))
        for vertex in self.graph.get_vertices():
            if hide_equal_predicates and vertex in self.graph.excluded_vertices:
                continue
            for succ in self.graph.get_successors(vertex):
                if hide_equal_predicates and succ in self.graph.excluded_vertices:
                    continue
                file.write("\"%s\" -> \"%s\";\n" % (vertex, succ))
        file.write("}\n")

    def find_automorphisms(self, time_limit, compute_group_order):
        # TODO: we sorted task's init, hence if we wanted to to use
        # the generators, we should remap init indices when required.
        # The same is true for operators.
        automorphisms = self.graph.find_automorphisms(time_limit, compute_group_order)
        return automorphisms


    def print_generator(self, generator, hide_equal_predicates=False):
        keys = sorted(generator.keys())
        for from_vertex in keys:
            if hide_equal_predicates and from_vertex in self.graph.excluded_vertices:
                continue
            to_vertex = generator[from_vertex]
            if hide_equal_predicates and to_vertex in self.graph.excluded_vertices:
                continue
            if from_vertex != to_vertex:
                print ("%s => %s" % (from_vertex, to_vertex))

    def write_or_print_automorphisms(self, automorphisms, hide_equal_predicates=False, write=False, dump=False):
        if write:
            file = open('generators.txt', 'w')
        for generator in automorphisms:
            if dump:
                print("generator:")
            if write:
                file.write("generator:\n")
            keys = sorted(generator.keys())
            for from_vertex in keys:
                if hide_equal_predicates and from_vertex in self.graph.excluded_vertices:
                    continue
                to_vertex = generator[from_vertex]
                if hide_equal_predicates and to_vertex in self.graph.excluded_vertices:
                    continue
                if from_vertex != to_vertex:
                    if dump:
                        print ("%s => %s" % (from_vertex, to_vertex))
                    if write:
                        file.write("%s => %s\n" % (from_vertex, to_vertex))
        if write:
            file.close()

    def add_mutex_groups(self, mutex_groups):
        for index, mutex_group in enumerate(mutex_groups):
            assert isinstance(mutex_group, list)
            group_node = self._get_mutex_group_node((index))
            self.graph.add_vertex(group_node, Color.mutex_group)
            for atom in mutex_group:
                assert isinstance(atom, pddl.Atom)
                lit_node = self._add_literal(NodeType.mutex_group, Color.mutex_group, atom, (index))
                self.graph.add_edge(group_node, lit_node)


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


def create_abstract_structure(task):
    counter = itertools.count()
    init = get_as_for_initial_state(task.init, task.objects)
    goal = get_as_for_goal(task.goal)
    axioms = get_as_for_axioms(task.axioms, counter)
    actions = get_as_for_actions(task.actions, counter)
    return (actions, axioms, init, goal)

def get_as_for_literal(literal, variable_mapping={}):
    res = [literal.predicate]
    res.extend(variable_mapping.get(x,x) for x in literal.args)
    if literal.negated:
        res = ("!", tuple(res))
    else:
        res = tuple(res)
    return res

def get_as_for_initial_state(init, objects):
    result = []
    for entry in init:
        if isinstance(entry, pddl.Literal):
            result.append(get_as_for_literal(entry))
        else: # numeric function
            assert(isinstance(entry, pddl.Assign))
            assert(isinstance(entry.fluent, pddl.PrimitiveNumericExpression))
            assert(isinstance(entry.expression, pddl.NumericConstant))
            if entry.fluent.symbol == "total-cost":
                continue
            function_term = [entry.fluent.symbol]
            function_term.extend(entry.fluent.args)
            result.append((tuple(function_term), entry.expression.value))
    
    for obj in objects:
        if obj.type_name != "object":
            result.append((obj.type_name, obj.name))
    return frozenset(result)

def get_as_for_goal(goal):
    result = []
    if isinstance(goal, pddl.Conjunction):
        for literal in goal.parts:
            result.append(get_as_for_literal(literal))
    elif isinstance(goal, pddl.Literal):
        result.append(get_as_for_literal(goal))
    else:
        assert False
    return frozenset(result)

def get_as_for_actions(actions, counter):
    result = []
    for action in actions:
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
                pre.append(get_as_for_literal(literal, variable_mapping))
        elif isinstance(action.precondition, pddl.Literal):
            pre.append(get_as_for_literal(action.precondition, variable_mapping))
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
                    effcond.append(get_as_for_literal(literal, eff_var_mapping))
            elif isinstance(eff.condition, pddl.Literal):
                effcond.append(get_as_for_literal(eff.condition, eff_var_mapping))
            elif isinstance(eff.condition, pddl.Truth):
                pass
            else:
                assert False
            literal = get_as_for_literal(eff.literal, eff_var_mapping)
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


def get_as_for_axioms(axioms, counter):
    result = []
    for axiom in axioms:
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
                pre.add(get_as_for_literal(literal, variable_mapping))
        elif isinstance(axiom.condition, pddl.Literal):
            pre.add(get_as_for_literal(axiom.condition, variable_mapping))
        elif isinstance(axiom.condition, pddl.Truth):
           pass 
        else:
            assert False
        result.append((frozenset(params), frozenset(pre), effect))
    return frozenset(result)


def build_type_function(task):
    (OBJECT, VARIABLE, PREDICATE, FUNCTION, NEGATION, FIRST_NUMBER) = range(6)
    
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
    
    graph = PyblissModuleWrapper(False)
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
                not isinstance(from_struct, set)):
                print ("%s => %s" % (from_struct, to_struct))
