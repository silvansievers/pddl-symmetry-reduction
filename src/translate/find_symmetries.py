#! /usr/bin/env python

import normalize
import pddl

import sys
sys.path.append('/home/roeger/PyBliss-0.50beta')
sys.path.append('/home/roeger/PyBliss-0.50beta/lib/python')
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

        

class SymmetryGraph:
    TYPE_OBJECT = 0
    TYPE_PRED = 1
    TYPE_INIT = 2
    TYPE_GOAL = 3
    TYPE_OPERATOR = 4
    TYPE_OP_CONDITION = 5

    def __init__(self, task):
        self.graph = Digraph()
        self._object_color = 0
        self._first_predicate_color = 1
        self._add_objects(task)
        max_predicate_color = self._add_predicates(task)
        self._init_color = max_predicate_color + 1
        self._goal_color = max_predicate_color + 2
        self._operator_color = max_predicate_color + 3
        self._condition_color = max_predicate_color + 4
        self._add_init(task)
        self._add_goal(task)
        self._add_operators(task)
        for generator in self.graph.get_autiomorphism_generators():
            print("generator:")
            for a,b in generator.iteritems():
                if a != b:
                    print ("%s => %s" % (a,b))

    def _get_obj_node(self, obj_name):
        return (self.TYPE_OBJECT, obj_name) 

    def _get_pred_node(self, pred_name, index=0):
        return (self.TYPE_PRED, pred_name, index) 
    
    def _get_inv_pred_node(self, pred_name):
        return (self.TYPE_PRED, pred_name, -1) 

    def _get_init_node(self, name, init_index, arg_index=0):
        # name is only relevant for the dot output
        return (self.TYPE_INIT, init_index, arg_index, name) 

    def _get_goal_node(self, name, goal_index, arg_index=0):
        # name is only relevant for the dot output
        return (self.TYPE_GOAL, goal_index, arg_index, name) 
    
    def _get_operator_node(self, operator_name, param_name=None):
        # TODO include operator index because there could be several with the
        # same name
        return (self.TYPE_OPERATOR, operator_name, param_name) 
    
    def _get_op_condition_node(self, op_index, cond_index, param_index, name):
        return (self.TYPE_OP_CONDITION, op_index, cond_index, param_index, name) 
    

    def _dot_label(self, node):
        if node[0] == self.TYPE_OBJECT:
            return node[1]
        if node[0] == self.TYPE_PRED:
            pred, index = node[1], node[2]
            if index == -1:
                return "not %s" % pred
            if index == 0:
                return pred
            return "%s [%i]" % (pred, index)
        if node[0] in (self.TYPE_INIT, self.TYPE_GOAL):
            return node[3]
        if node[0] == self.TYPE_OPERATOR:
            if node[2] is not None:
                return node[2]
            else:
                return node[1]
        if node[0] == self.TYPE_OP_CONDITION:
            return node[-1]

    def _add_objects(self, task):
        for o in task.objects:
            self.graph.add_vertex(self._get_obj_node(o.name), self._object_color)

    def _add_predicates(self, task):
        assert(not task.axioms) # TODO support axioms
        fluent_predicates = set()
        for action in task.actions:
            for effect in action.effects:
                fluent_predicates.add(effect.literal.predicate)
        for axiom in task.axioms:
            fluent_predicates.add(axiom.name)

        max_predicate_color = self._first_predicate_color
        for pred in task.predicates:
            pred_node = self._get_pred_node(pred.name)
            is_fluent = pred.name in fluent_predicates
            color = self._first_predicate_color + len(pred.arguments)
            if color > max_predicate_color:
                max_predicate_color = color
            self.graph.add_vertex(pred_node, color)
            if is_fluent:
                inv_pred_node = self._get_inv_pred_node(pred.name)
                self.graph.add_vertex(inv_pred_node, color)
                self.graph.add_edge(inv_pred_node, pred_node)
                self.graph.add_edge(pred_node, inv_pred_node)
        for type in task.types:
            if type.name != "object":
                color = self._first_predicate_color + 1
                if color > max_predicate_color:
                    max_predicate_color = color
                pred_node = self._get_pred_node(type.get_predicate_name())
                self.graph.add_vertex(pred_node, color)
        return max_predicate_color 

    def _add_init(self, task):
        for no, fact in enumerate(task.init):
            pred_node = self._get_pred_node(fact.predicate)
            init_node = self._get_init_node(fact.predicate, no)
            self.graph.add_vertex(init_node, self._init_color)
            self.graph.add_edge(init_node, pred_node)
            prev_node = init_node
            for num, arg in enumerate(fact.args):
                arg_node = self._get_init_node(arg, no, num + 1)
                self.graph.add_vertex(arg_node, self._init_color)
                self.graph.add_edge(prev_node, arg_node)
                self.graph.add_edge(arg_node, self._get_obj_node(arg))
                prev_node = arg_node
        counter = len(task.init)
        type_dict = dict((type.name, type) for type in task.types)
        for no, o in enumerate(task.objects):
            obj_node = self._get_obj_node(o.name)
            type = type_dict[o.type_name]
            while type.name != "object":
                pred_name = type.get_predicate_name()
                init_node = self._get_init_node(pred_name, counter)
                self.graph.add_vertex(init_node, self._init_color)
                pred_node = self._get_pred_node(pred_name)
                self.graph.add_edge(init_node, pred_node)
                arg_node = self._get_init_node(o.name, counter, 1)
                self.graph.add_vertex(arg_node, self._init_color)
                self.graph.add_edge(init_node, arg_node)
                self.graph.add_edge(arg_node, obj_node)
                counter += 1
                type = type_dict[type.basetype_name]
    
    def _add_goal(self, task):
        for no, fact in enumerate(task.goal.parts):
            pred_node = self._get_pred_node(fact.predicate)
            goal_node = self._get_goal_node(fact.predicate, no)
            self.graph.add_vertex(goal_node, self._goal_color)
            self.graph.add_edge(goal_node, pred_node)
            prev_node = goal_node
            for num, arg in enumerate(fact.args):
                arg_node = self._get_goal_node(arg, no, num + 1)
                self.graph.add_vertex(arg_node, self._goal_color)
                self.graph.add_edge(prev_node, arg_node)
                self.graph.add_edge(arg_node, self._get_obj_node(arg))
                prev_node = arg_node
    
    def _add_operators(self, task):
        for op_index, op in enumerate(task.actions):
            op_node = self._get_operator_node(op.name)
            self.graph.add_vertex(op_node, self._operator_color)
            pre_index = 0
            for param in op.parameters:
                # parameter node
                param_node = self._get_operator_node(op.name, param.name)
                self.graph.add_vertex(param_node, self._operator_color)
                self.graph.add_edge(op_node, param_node)

                # type precondition
                type_dict = dict((type.name, type) for type in task.types)
                if param.type_name != "object":
                    pred_name = type_dict[param.type_name].get_predicate_name()
                    cond_node = self._get_op_condition_node(op_index, pre_index,
                    0, pred_name)
                    self.graph.add_vertex(cond_node, self._condition_color)
                    self.graph.add_edge(cond_node, op_node)
                    arg_node = self._get_op_condition_node(op_index, pre_index, 1, param.name)
                    self.graph.add_vertex(arg_node, self._condition_color)
                    self.graph.add_edge(cond_node, arg_node)
                    self.graph.add_edge(arg_node, param_node)
                    pred_node = self._get_pred_node(pred_name)
                    self.graph.add_edge(pred_node, cond_node)
                    pre_index += 1

            def add_condition_literal(literal, pre_index, base_node):
                pred_name = literal.predicate
                if literal.negated:
                    pred_node = self._get_inv_pred_node(pred_name)
                    label = "not %s" % pred_name
                else:
                    pred_node = self._get_pred_node(pred_name)
                    label = pred_name
                cond_node = self._get_op_condition_node(op_index, pre_index, 0, label)
                self.graph.add_vertex(cond_node, self._condition_color)
                self.graph.add_edge(cond_node, base_node)
                self.graph.add_edge(pred_node, cond_node)
                prev_node = cond_node
                for arg_no, arg in enumerate(literal.args):  
                    arg_node = self._get_op_condition_node(op_index, pre_index,
                                                           arg_no, arg)
                    self.graph.add_vertex(arg_node, self._condition_color)
                    self.graph.add_edge(prev_node, arg_node)
                    prev_node = arg_node
                    # edge argument to respective parameter or constant
                    if arg[0] == "?":
                        corr_node = self._get_operator_node(op.name, arg)
                    else:
                        corr_node = self._get_obj_node(arg)
                    self.graph.add_edge(arg_node, corr_node)

            if isinstance(op.precondition, pddl.Literal):
                add_condition_literal(op.precondition, pre_index, op_node)
                pre_index += 1
            else:
                assert isinstance(op.precondition, pddl.Conjunction)
                for literal in op.precondition.parts:
                    add_condition_literal(literal, pre_index, op_node)
                    pre_index += 1
               

    def write_dot(self, file):
        """
        Write the graph into a file in the graphviz dot format.
        """
        colors = {
                self._object_color: ("X11","blue"),
                self._init_color: ("X11", "lightyellow"),
                self._goal_color: ("X11", "yellow"),
                self._operator_color: ("X11", "green4"),
                self._condition_color: ("X11", "green2"),
            }
        different_pred_colors = self._init_color - self._first_predicate_color
        for c in range(self._first_predicate_color, self._init_color):
            colors[c] = ("blues%i" % different_pred_colors, 
                         "%i" %  c )
        file.write("digraph g {\n")
        for vertex in self.graph.get_vertices():
            color = self.graph.get_color(vertex)
            file.write("\"%s\" [style=filled, label=\"%s\", colorscheme=%s, fillcolor=%s];\n" %
                (vertex, self._dot_label(vertex), colors[color][0], colors[color][1]))
        for vertex in self.graph.get_vertices():
            for succ in self.graph.get_successors(vertex):
                file.write("\"%s\" -> \"%s\";\n" % (vertex, succ))
        file.write("}\n")



if __name__ == "__main__":
    import pddl_parser
    task = pddl_parser.open()
    normalize.normalize(task)
    task.dump()
    G = SymmetryGraph(task)
    f = open('out.dot', 'w')
    G.write_dot(f)
