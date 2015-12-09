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
        self.internal_edge_color = 1
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
        return vertex.color - 2;

    def add_vertex(self, vertex, color):
        vertex = tuple(vertex)
        if vertex in self.vertices:
            assert (color == self.get_color(vertex))
            return
        v_in, v_out = self._new_node(vertex), self._new_node()
        self.graph.add_vertex(v_in, self.internal_node_color)
        self.graph.add_vertex(v_out, color + 2)
        self.graph.add_edge(v_in, v_out)
        self.vertices[vertex] = (v_in, v_out)

    def add_edge(self, v1, v2):
        v_out = self.vertices[tuple(v1)][1]
        v_in = self.vertices[tuple(v2)][0]
        e1, e2 = self._new_node(), self._new_node()
        self.graph.add_vertex(e1, self.internal_edge_color)
        self.graph.add_vertex(e2, self.internal_edge_color)
        self.graph.add_edge(e1, e2)
        self.graph.add_edge(v_out, e2)
        self.graph.add_edge(e2, v_in)
    
    def get_vertices(self):
        return list(self.vertices)

    def get_successors(self, vertex):
        successors = []
        v_out = self.vertices[vertex][1]
        for edge in self.graph._vertices[v_out].edges:
            if self.id_to_vertex[int(edge.name)] is None: # edge node
                for succ in self.graph._vertices[edge.name].edges:
                    if self.id_to_vertex[int(succ.name)] is not None: # in node
                        successors.append(self.id_to_vertex[int(succ.name)]) 
        return successors


class NodeType:
    constant = 0
    predicate = 1
    init = 2
    goal = 3
    operator = 4
    condition = 5
    effect = 6
    effect_literal = 7


class Color:
    constant = 0
    init = 1
    goal = 2
    operator = 3
    condition = 4
    effect = 5
    effect_literal = 6
    predicate = 7 # predicates of arity 0


class SymmetryGraph:
    def __init__(self, task):
        self.graph = Digraph()
        self._add_objects(task)
        self._add_predicates(task)
        self._add_init(task)
        self._add_goal(task)
        self._add_operators(task)
        self.max_predicate_arity = max([len(p.arguments)
                                        for p in task.predicates])
        if self.max_predicate_arity == 0 and len(task.types) > 1:
            # type predicates have arity 1 (we do not count type object)
            self.max_predicate_arity = 1

    def _get_obj_node(self, obj_name):
        return (NodeType.constant, obj_name)

    def _get_pred_node(self, pred_name, negated=False):
        index = -1 if negated else 0
        return (NodeType.predicate, index, pred_name) 
    
    def _get_init_node(self, name, init_index, arg_index=0):
        # name is only relevant for the dot output
        return (NodeType.init, init_index, arg_index, name) 

    def _get_goal_node(self, name, goal_index, arg_index=0):
        # name is only relevant for the dot output
        return (NodeType.goal, goal_index, arg_index, name) 
    
    def _get_operator_node(self, op_index, name):
        # name is either operator name or argument name
        return (NodeType.operator, op_index, name) 
    
    def _get_condition_node(self, op_index, eff_index, cond_index, param_index, name):
        return (NodeType.condition, op_index, eff_index, cond_index, param_index, name) 

    def _get_effect_node(self, op_index, eff_index, name):
        # name is either some effect name or argument name.
        # The argument name is relevant for identifying the node
        return (NodeType.effect, op_index, eff_index, name)

    def _get_effect_literal_node(self, op_index, eff_index, index, name):
        return (NodeType.effect_literal, op_index, eff_index, index, name) 
    
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

    def _add_init(self, task):
        def add_fact(predicate, args, counter):
            pred_node = self._get_pred_node(predicate)
            init_node = self._get_init_node(predicate, counter)
            self.graph.add_vertex(init_node, Color.init)
            self.graph.add_edge(init_node, pred_node)
            prev_node = init_node
            for num, arg in enumerate(args):
                arg_node = self._get_init_node(arg, counter, num + 1)
                self.graph.add_vertex(arg_node, Color.init)
                self.graph.add_edge(prev_node, arg_node)
                self.graph.add_edge(arg_node, self._get_obj_node(arg))
                prev_node = arg_node

        for no, fact in enumerate(task.init):
            add_fact(fact.predicate, fact.args, no)
        counter = len(task.init)
        type_dict = dict((type.name, type) for type in task.types)
        for o in task.objects:
            obj_node = self._get_obj_node(o.name)
            type = type_dict[o.type_name]
            while type.name != "object":
                add_fact(type.get_predicate_name(), [o.name], counter)
                counter += 1
                type = type_dict[type.basetype_name]
    
    def _add_goal(self, task):
        for no, fact in enumerate(task.goal.parts):
            pred_node = self._get_pred_node(fact.predicate)
            goal_node = self._get_goal_node(fact.predicate, no)
            self.graph.add_vertex(goal_node, Color.goal)
            self.graph.add_edge(goal_node, pred_node)
            prev_node = goal_node
            for num, arg in enumerate(fact.args):
                arg_node = self._get_goal_node(arg, no, num + 1)
                self.graph.add_vertex(arg_node, Color.goal)
                self.graph.add_edge(prev_node, arg_node)
                self.graph.add_edge(arg_node, self._get_obj_node(arg))
                prev_node = arg_node
   
    def _add_condition(self, literal, cond_index, base_node, op_index, op_args,
                       eff_index = -1, eff_args=dict()):
        # base node is operator node for preconditions and effect node for
        # effect conditions
        pred_name = literal.predicate
        if literal.negated:
            pred_node = self._get_pred_node(pred_name, True)
            label = "not %s" % pred_name
        else:
            pred_node = self._get_pred_node(pred_name)
            label = pred_name
        index = -1 if literal.negated else 0
        cond_node = self._get_condition_node(op_index, eff_index, cond_index,
                                             index, pred_name)
        self.graph.add_vertex(cond_node, Color.condition)
#        self.graph.add_edge(cond_node, base_node)
        self.graph.add_edge(base_node, cond_node)
        self.graph.add_edge(pred_node, cond_node)
        prev_node = cond_node
        for arg_no, arg in enumerate(literal.args):  
            arg_node = self._get_condition_node(op_index, eff_index, cond_index, arg_no+1, arg)
            self.graph.add_vertex(arg_node, Color.condition)
            self.graph.add_edge(prev_node, arg_node)
            prev_node = arg_node
            # edge argument to respective parameter or constant
            if arg[0] == "?":
                if arg in eff_args:
                    self.graph.add_edge(eff_args[arg], arg_node)
                else:
                    self.graph.add_edge(op_args[arg], arg_node)
            else:
                self.graph.add_edge(self._get_obj_node(arg), arg_node)

    def _add_preconditions(self, op, op_index, op_node, op_args): 
        pre_index = 0
        if isinstance(op.precondition, pddl.Literal):
            self._add_condition(op.precondition, pre_index, op_node,
                                op_index, op_args)
            pre_index += 1
        else:
            assert isinstance(op.precondition, pddl.Conjunction)
            for literal in op.precondition.parts:
                self._add_condition(literal, pre_index, op_node,
                                    op_index, op_args)
                pre_index += 1
        
        # precondition from types
        type_dict = dict((type.name, type) for type in task.types)
        for param in op.parameters:
            if param.type_name != "object":
                pred_name = type_dict[param.type_name].get_predicate_name()
                literal = pddl.Atom(pred_name, (param.name,))
                self._add_condition(literal, pre_index, op_node,
                                    op_index, op_args)
                pre_index += 1

    def _add_effect(self, op_index, op_node, op_args, eff_index, eff):
        eff_node = self._get_effect_node(op_index, eff_index, 
                                         "e_%i_%i" % (op_index, eff_index))
        self.graph.add_vertex(eff_node, Color.effect);
        self.graph.add_edge(op_node, eff_node);
        eff_args = dict()
        for param in eff.parameters: 
            param_node = self._get_effect_node(op_index, eff_index, param.name) 
            self.graph.add_vertex(param_node, Color.effect); 
            eff_args[param.name] = param_node
            self.graph.add_edge(eff_node, param_node)
        
        pre_index = 0
        if isinstance(eff.condition, pddl.Literal):
            self._add_condition(eff.condition, pre_index, eff_node,
                                op_index, op_args, eff_index, eff_args)
            pre_index += 1
        elif isinstance(eff.condition, pddl.Conjunction):
            for literal in eff.condition.parts:
                self._add_condition(literal, pre_index, eff_node,
                                    op_index, op_args, eff_index, eff_args)
                pre_index += 1
        else:
            assert isinstance(eff.condition, pddl.Truth)
        # effect condition from types
        type_dict = dict((type.name, type) for type in task.types)
        for param in eff.parameters:
            if param.type_name != "object":
                pred_name = type_dict[param.type_name].get_predicate_name()
                literal = pddl.Atom(pred_name, (param.name,))
                self._add_condition(literal, pre_index, eff_node,
                                    op_index, op_args, eff_index, eff_args)
                pre_index += 1

        # affected literal
        pred_name = eff.literal.predicate
        index = -1 if eff.literal.negated else 0
        eff_literal_node = self._get_effect_literal_node(op_index, eff_index,
                                                         index, pred_name)
        pred_node = self._get_pred_node(pred_name, index)
        self.graph.add_vertex(eff_literal_node, Color.effect_literal)
        self.graph.add_edge(eff_literal_node, pred_node)
        self.graph.add_edge(eff_node, eff_literal_node)
        prev_node = eff_literal_node
        for num, arg in enumerate(eff.literal.args):
            arg_node = self._get_effect_literal_node(op_index, eff_index,
                                                         num+1, arg)
            self.graph.add_vertex(arg_node, Color.effect_literal)
            self.graph.add_edge(prev_node, arg_node)
#            self.graph.add_edge(arg_node, self._get_obj_node(arg))
            prev_node = arg_node
            if arg[0] == "?":
                if arg in eff_args:
                    self.graph.add_edge(eff_args[arg], arg_node)
                else:
                    self.graph.add_edge(op_args[arg], arg_node)
            else:
                self.graph.add_edge(self._get_obj_node(arg), arg_node)

    def _add_operators(self, task):
        for op_index, op in enumerate(task.actions):
            op_node = self._get_operator_node(op_index, op.name)
            self.graph.add_vertex(op_node, Color.operator)
            op_args = dict()
            for param in op.parameters:
                # parameter node
                param_node = self._get_operator_node(op_index, param.name)
                op_args[param.name] = param_node
                self.graph.add_vertex(param_node, Color.operator)
                self.graph.add_edge(op_node, param_node)

            self._add_preconditions(op, op_index, op_node, op_args) 
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
