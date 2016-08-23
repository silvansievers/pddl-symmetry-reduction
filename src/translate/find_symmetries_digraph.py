#! /usr/bin/env python

import normalize
import pddl

import sys
sys.path.append('PyBliss-0.50beta-digraph')
sys.path.append('PyBliss-0.50beta-digraph/lib/python')
import PyBliss


class Digraph:
    """Wrapper graph for PyBliss graphs.
    """
    def __init__(self):
        self.graph = PyBliss.Graph()
        self.id_to_vertex = []
        self.vertices = {}

    def get_autiomorphism_generators(self):
        aut_gens = []
        def report(perm, text = None):
            aut_gens.append(self._translate_generator(perm))
        self.graph.find_automorphisms(report, "Aut gen:")
        return aut_gens

    def _translate_generator(self, generator):
        result = {}
        for a,b in generator.iteritems():
            if self.id_to_vertex[a] is not None:
                assert (self.id_to_vertex[b] is not None)
                result[self.id_to_vertex[a]] = self.id_to_vertex[b]
        return result

    def _new_node(self, vertex):
        self.id_to_vertex.append(vertex)
        return len(self.id_to_vertex) - 1

    def get_color(self, vertex):
        v = self.vertices[vertex]
        return self.graph._vertices[v].color

    def add_vertex(self, vertex, color):
        vertex = tuple(vertex)
        if vertex in self.vertices:
            assert (color == self.get_color(vertex))
            return
        v = self._new_node(vertex)
        self.graph.add_vertex(v, color)
        self.vertices[vertex] = v

    def add_edge(self, vertex1, vertex2):
        assert (vertex1 != vertex2) # we do not support self-loops
        v1 = self.vertices[tuple(vertex1)]
        v2 = self.vertices[tuple(vertex2)]
        self.graph.add_edge(v1, v2)

    def get_vertices(self):
        return list(self.vertices)

    def get_successors(self, vertex):
        successors = []
        v = self.vertices[vertex]
        for succ in self.graph._vertices[v].edges:
            if succ.name != v:
                successors.append(self.id_to_vertex[int(succ.name)])
        return successors

    def write_dot(self, file):
        self.graph.write_dot(file)


class NodeType:
    """Used by SymmetryGraph to make nodes of different types distinguishable."""
    (constant, init, goal, operator, condition, effect, effect_literal,
    function, predicate, cost, number) = range(11)


class Color:
    """Node colors used by SymmetryGraph"""
    # NOTE: it is important that predicate has the highest value. This value is
    # used for predicates of arity 0, predicates of higher arity get assigned
    # subsequent numbers
    (constant, init, goal, operator, condition, effect, effect_literal,
    cost, predicate) = range(9)
    function = None # will be set by Symmetry Graph, depending on the colors
                    # required for predicate symbols
    number = None # will be set by Symmetry Graph

class SymmetryGraph:
    def __init__(self, task):
        self.graph = Digraph()
        self.numbers = set()
        self.constant_functions = dict()
        self.max_predicate_arity = \
            max([len(p.arguments) for p in task.predicates] +
                [int(len(task.types) > 1)])
        self.max_function_arity = max([0] + [len(p.arguments)
                                       for p in task.functions])
        Color.function = Color.predicate + self.max_predicate_arity + 1
        Color.number = Color.function + self.max_function_arity + 1

        self._add_objects(task)
        self._add_predicates(task)
        self._add_functions(task)
        self._add_init(task)
        self._add_goal(task)
        self._add_operators(task)

    def _get_number_node(self, no):
        node = (NodeType.number, no)
        if no not in self.numbers:
            self.graph.add_vertex(node, Color.number + len(self.numbers))
            self.numbers.add(no)
        return node

    def _get_obj_node(self, obj_name):
        return (NodeType.constant, obj_name)

    def _get_pred_node(self, pred_name, negated=False):
        return (NodeType.predicate, negated, pred_name)

    def _get_function_node(self, function_name, arg_index=0):
        return (NodeType.function, function_name, arg_index)

    def _get_structure_node(self, node_type, id_indices, name):
        # name is either the operator or effect name or an argument name.
        # The argument name is relevant for identifying the node
        assert (node_type in (NodeType.operator, NodeType.effect))
        return (node_type, id_indices, name)

    def _get_literal_node(self, node_type, id_indices, arg_index, name):
        # name is mostly relevant for the dot output. The only exception are
        # init nodes for constant functions, where it is used to distinguish
        # them
        return (node_type, id_indices, arg_index, name)

    def _add_objects(self, task):
        """Add a node for each object of the task.

        All nodes have color Color.constant.
        """
        for o in task.objects:
            self.graph.add_vertex(self._get_obj_node(o.name), Color.constant)

    def _add_predicates(self, task):
        """Add nodes for each declared predicate and type predicate.

        For a normal predicate there is a positive and a negative node and edges
        between them in both directions. For a type predicate (that cannot occur
        as a negative condition) there is only the positive node. The nodes have
        color 'Color.predicate + <arity of the predicate>'.
        """
        assert(not task.axioms) # TODO support axioms

        def add_predicate(pred_name, arity, only_positive=False):
            pred_node = self._get_pred_node(pred_name)
            color = Color.predicate + arity
            self.graph.add_vertex(pred_node, color)
            if not only_positive:
                inv_pred_node = self._get_pred_node(pred_name, True)
                self.graph.add_vertex(inv_pred_node, color)
                self.graph.add_edge(inv_pred_node, pred_node)
                self.graph.add_edge(pred_node, inv_pred_node)

        for pred in task.predicates:
            add_predicate(pred.name, len(pred.arguments))
        for type in task.types:
            if type.name != "object":
                add_predicate(type.get_predicate_name(), 1, True)

    def _add_functions(self, task):
        """Add a node for each function symbol.

        All functions f of the same arity share the same color
        Color.function + arity(f).
        """
        type_dict = dict((type.name, type) for type in task.types)
        for function in task.functions:
            if function.name == "total-cost":
                continue
            func_node = self._get_function_node(function.name, 0)
            assert (Color.function is not None)
            self.graph.add_vertex(func_node,
                                  Color.function + len(function.arguments))
#            prev_node = func_node
#            for no, arg in enumerate(function.arguments):
#                arg_node = self._get_function_node(function.name, no+1)
#                self.graph.add_vertex(arg_node, Color.function)
#                self.graph.add_edge(prev_node, arg_node)
#                prev_node = arg_node
#                if arg.type_name != "object":
#                    type = type_dict[arg.type_name]
#                    type_node = self._get_pred_node(type.get_predicate_name())
#                    self.graph.add_edge(type_node, arg_node)
#            val_node = self._get_function_node(function.name, -1)
#            self.graph.add_vertex(val_node, Color.function)
#            self.graph.add_edge(prev_node, val_node)


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
        pred_node = self._get_pred_node(literal.predicate, literal.negated)
        index = -1 if literal.negated else 0
        first_node = self._get_literal_node(node_type, id_indices, index,
                                            literal.predicate)
        self.graph.add_vertex(first_node, color)
        self.graph.add_edge(pred_node, first_node)
        prev_node = first_node
        for num, arg in enumerate(literal.args):
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
        return first_node

    def _add_init(self, task):
        for no, entry in enumerate(task.init):
            if isinstance(entry, pddl.Literal):
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

        # add types
        counter = len(task.init)
        type_dict = dict((type.name, type) for type in task.types)
        for o in task.objects:
            type = type_dict[o.type_name]
            while type.name != "object":
                literal = pddl.Atom(type.get_predicate_name(), (o.name,))
                self._add_literal(NodeType.init, Color.init, literal, (counter,))
                counter += 1
                type = type_dict[type.basetype_name]

    def _add_goal(self, task):
        for no, fact in enumerate(task.goal.parts):
            self._add_literal(NodeType.goal, Color.goal, fact, (no,))

    def _add_condition(self, literal, id_indices, base_node, op_args,
                       eff_args=dict()):
        # base node is operator node for preconditions and effect node for
        # effect conditions
        first_node = self._add_literal(NodeType.condition, Color.condition,
                                       literal, id_indices, (eff_args, op_args))
        self.graph.add_edge(base_node, first_node)

    def _add_conditions(self, params, condition, id_indices, base_node, op_args,
        eff_args=dict()):
        pre_index = 0
        if isinstance(condition, pddl.Literal):
            self._add_condition(condition, id_indices + (pre_index,), base_node,
                                op_args, eff_args)
            pre_index += 1
        elif isinstance(condition, pddl.Conjunction):
            assert isinstance(condition, pddl.Conjunction)
            for literal in condition.parts:
                self._add_condition(literal, id_indices + (pre_index,),
                                    base_node, op_args, eff_args)
                pre_index += 1
        else:
            assert isinstance(condition, pddl.Truth)

        # condition from types
        type_dict = dict((type.name, type) for type in task.types)
        for param in params:
            if param.type_name != "object":
                pred_name = type_dict[param.type_name].get_predicate_name()
                literal = pddl.Atom(pred_name, (param.name,))
                self._add_condition(literal, id_indices + (pre_index,), base_node,
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
        self._add_conditions(eff.parameters, eff.condition, (op_index,
                             eff_index), eff_node, op_args, eff_args)

        # affected literal
        first_node = self._add_literal(NodeType.effect_literal,
                                       Color.effect_literal, eff.literal,
                                       (op_index, eff_index),
                                       (eff_args, op_args))
        self.graph.add_edge(eff_node, first_node)

    def _add_operators(self, task):
        for op_index, op in enumerate(task.actions):
            op_node, op_args = self._add_structure(NodeType.operator,
                                                   (op_index,), op.name,
                                                   Color.operator,
                                                   op.parameters)
            self._add_conditions(op.parameters, op.precondition, (op_index,),
                                 op_node, op_args)
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


    def write_dot(self, file):
        """Write the graph into a file in the graphviz dot format."""
        def dot_label(node):
            if (node[0] in (NodeType.predicate, NodeType.effect_literal,
                NodeType.condition) and (node[-2] is True or node[-2] == -1)):
                return "not %s" % node[-1]
            elif node[0] == NodeType.function:
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
            }
        vals = self.max_predicate_arity + 1
        for c in range(vals):
            colors[Color.predicate + c] = ("blues%i" % vals, "%i" %  (c + 1))
        vals = self.max_function_arity + 1
        for c in range(vals):
            colors[Color.function + c] = ("oranges%i" % vals, "%i" %  (c + 1))
        for c in range(len(self.numbers) + 1):
            colors[Color.number + c] = ("X11", "gray100")
            # we draw numbers with the same color albeit they are actually all
            # different

        file.write("digraph g {\n")
        for vertex in self.graph.get_vertices():
            color = self.graph.get_color(vertex)
            file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
                (vertex, dot_label(vertex), colors[color][0], colors[color][1]))
        for vertex in self.graph.get_vertices():
            for succ in self.graph.get_successors(vertex):
                file.write("\"%s\" -> \"%s\";\n" % (vertex, succ))
        file.write("}\n")

    def write_dot_bliss(self, file):
        self.graph.write_dot(file)

    def print_automorphism_generators(self):
        for generator in self.graph.get_autiomorphism_generators():
            print("generator:")
            for a,b in generator.iteritems():
                if a != b:
                    print ("%s => %s" % (a,b))

if __name__ == "__main__":
    import pddl_parser
    task = pddl_parser.open()
    normalize.normalize(task)
    task.dump()
    G = SymmetryGraph(task)
    G.print_automorphism_generators()
    f = open('out.dot', 'w')
    G.write_dot(f)
    f.close()
    f = open('out_bliss.dot', 'w')
    G.write_dot_bliss(f)
    f.close()
