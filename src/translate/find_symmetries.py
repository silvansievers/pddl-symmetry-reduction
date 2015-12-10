#! /usr/bin/env python

import normalize
import pddl

import sys
sys.path.append('PyBliss-0.50beta')
sys.path.append('PyBliss-0.50beta/lib/python')
import PyBliss


class Digraph:
    def __init__(self):
        self.graph = PyBliss.Graph()
        self.internal_node_color = 0
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

    def _new_node(self, vertex=None):
        self.id_to_vertex.append(vertex)
        return len(self.id_to_vertex) - 1

    def get_color(self, vertex):
        v_out = self.vertices[vertex][1]
        vertex = self.graph._vertices[v_out]
        return vertex.color - 1;

    def add_vertex(self, vertex, color):
        vertex = tuple(vertex)
        if vertex in self.vertices:
            assert (color == self.get_color(vertex))
            return
        v_in, v_out = self._new_node(vertex), self._new_node()
        self.graph.add_vertex(v_in, self.internal_node_color)
        self.graph.add_vertex(v_out, color + 1)
        self.graph.add_edge(v_in, v_out)
        self.vertices[vertex] = (v_in, v_out)

    def add_edge(self, v1, v2):
        assert (v1 != v2) # we do not support self-loops
        v_out = self.vertices[tuple(v1)][1]
        v_in = self.vertices[tuple(v2)][0]
        self.graph.add_edge(v_out, v_in)
    
    def get_vertices(self):
        return list(self.vertices)

    def get_successors(self, vertex):
        successors = []
        v_in, v_out = self.vertices[vertex]
        for succ in self.graph._vertices[v_out].edges:
            if succ != v_in:
                successors.append(self.id_to_vertex[int(succ.name)]) 
        return successors


class NodeType:
    (constant, init, goal, operator, condition, effect, effect_literal, predicate) = range(8)


class Color:
    # NOTE: it is important that predicate has the highest value. This value is
    # used for predicates of arity 0, predicates of higher arity get assigned
    # subsequent numbers
    (constant, init, goal, operator, condition, effect, effect_literal, predicate) = range(8)


class SymmetryGraph:
    def __init__(self, task):
        self.graph = Digraph()
        self.max_predicate_arity = \
            max([len(p.arguments) for p in task.predicates] +
                [int(len(task.types) > 1)])
        
        self._add_objects(task)
        self._add_predicates(task)
        self._add_init(task)
        self._add_goal(task)
        self._add_operators(task)

    def _get_obj_node(self, obj_name):
        return (NodeType.constant, obj_name)

    def _get_pred_node(self, pred_name, negated=False):
        index = -1 if negated else 0
        return (NodeType.predicate, index, pred_name)
    
    def _get_structure_node(self, node_type, id_indices, name):
        # name is either the operator or effect name or an argument name.
        # The argument name is relevant for identifying the node
        assert (node_type in (NodeType.operator, NodeType.effect))
        return (node_type, id_indices, name)

    def _get_literal_node(self, node_type, id_indices, arg_index, name):
        # name is only relevant for the dot output
        return (node_type, id_indices, arg_index, name) 
    
    def _add_objects(self, task):
        for o in task.objects:
            self.graph.add_vertex(self._get_obj_node(o.name), Color.constant)

    def _add_predicates(self, task):
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
        
    def _add_literal(self, node_type, color, literal, id_indices, param_dicts=()):
        pred_node = self._get_pred_node(literal.predicate, literal.negated)
        index = -1 if literal.negated else 0
        first_node = self._get_literal_node(node_type, id_indices, index,
                                            literal.predicate)
        self.graph.add_vertex(first_node, color)
        self.graph.add_edge(first_node, pred_node)
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
        for no, fact in enumerate(sorted(task.init)):
            self._add_literal(NodeType.init, Color.init, fact, (no,))
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

    def write_dot(self, file):
        """
        Write the graph into a file in the graphviz dot format.
        """
        def dot_label(node):
            if (node[0] in (NodeType.predicate, NodeType.effect_literal,
                NodeType.condition) and node[-2] == -1):
                return "not %s" % node[-1]
            return node[-1]

        colors = {
                Color.constant: ("X11","blue"),
                Color.init: ("X11", "lightyellow"),
                Color.goal: ("X11", "yellow"),
                Color.operator: ("X11", "green4"),
                Color.condition: ("X11", "green2"),
                Color.effect: ("X11", "green3"),
                Color.effect_literal: ("X11", "yellowgreen"),
            }
        vals = self.max_predicate_arity + 1
        for c in range(vals):
            colors[Color.predicate + c] = ("blues%i" % vals, "%i" %  (c + 1))

        file.write("digraph g {\n")
        for vertex in self.graph.get_vertices():
            color = self.graph.get_color(vertex)
            file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
                (vertex, dot_label(vertex), colors[color][0], colors[color][1]))
        for vertex in self.graph.get_vertices():
            for succ in self.graph.get_successors(vertex):
                file.write("\"%s\" -> \"%s\";\n" % (vertex, succ))
        file.write("}\n")

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
