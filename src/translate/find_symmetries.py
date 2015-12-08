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
    TYPE_CONDITION = 5

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
    
    def _get_operator_node(self, index, operator_name, param_name=None):
        # TODO include operator index because there could be several with the
        # same name
        return (self.TYPE_OPERATOR, operator_name, param_name) 
    
    def _get_condition_node(self, op_index, eff_index, cond_index, param_index, name):
        return (self.TYPE_CONDITION, op_index, eff_index, cond_index, param_index, name) 
    

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
        if node[0] == self.TYPE_CONDITION:
            return node[-1]

    def _add_objects(self, task):
        for o in task.objects:
            self.graph.add_vertex(self._get_obj_node(o.name), self._object_color)

    def _fluent_predicates(self, task):
        fluent_predicates = set()
        for action in task.actions:
            for effect in action.effects:
                fluent_predicates.add(effect.literal.predicate)
        for axiom in task.axioms:
            fluent_predicates.add(axiom.name)
        return fluent_predicates

    def _add_predicates(self, task):
        assert(not task.axioms) # TODO support axioms
        fluent_predicates = self._fluent_predicates(task)

        def add_predicate(pred_name, arity):
            pred_node = self._get_pred_node(pred_name)
            color = self._first_predicate_color + arity 
            self.graph.add_vertex(pred_node, color)
            if pred.name in fluent_predicates:
                inv_pred_node = self._get_inv_pred_node(pred_name)
                self.graph.add_vertex(inv_pred_node, color)
                self.graph.add_edge(inv_pred_node, pred_node)
                self.graph.add_edge(pred_node, inv_pred_node)
            return color

        max_predicate_color = self._first_predicate_color
        for pred in task.predicates:
            color = add_predicate(pred.name, len(pred.arguments)) 
            max_predicate_color = max(max_predicate_color, color)
        for type in task.types:
            if type.name != "object":
                color = add_predicate(type.get_predicate_name(), 1) 
                max_predicate_color = max(max_predicate_color, color)
        return max_predicate_color 

    def _add_init(self, task):
        def add_fact(predicate, args, counter):
            pred_node = self._get_pred_node(predicate)
            init_node = self._get_init_node(predicate, counter)
            self.graph.add_vertex(init_node, self._init_color)
            self.graph.add_edge(init_node, pred_node)
            prev_node = init_node
            for num, arg in enumerate(args):
                arg_node = self._get_init_node(arg, counter, num + 1)
                self.graph.add_vertex(arg_node, self._init_color)
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
            self.graph.add_vertex(goal_node, self._goal_color)
            self.graph.add_edge(goal_node, pred_node)
            prev_node = goal_node
            for num, arg in enumerate(fact.args):
                arg_node = self._get_goal_node(arg, no, num + 1)
                self.graph.add_vertex(arg_node, self._goal_color)
                self.graph.add_edge(prev_node, arg_node)
                self.graph.add_edge(arg_node, self._get_obj_node(arg))
                prev_node = arg_node
   
    def _add_condition(self, literal, cond_index, base_node, op_index, op_args,
                       eff_index = -1, eff_args=dict()):
        # base node is operator node for preconditions and effect node for
        # effect conditions
        pred_name = literal.predicate
        if literal.negated:
            pred_node = self._get_inv_pred_node(pred_name)
            label = "not %s" % pred_name
        else:
            pred_node = self._get_pred_node(pred_name)
            label = pred_name
        cond_node = self._get_condition_node(op_index, eff_index, cond_index, 0, label)
        self.graph.add_vertex(cond_node, self._condition_color)
        self.graph.add_edge(cond_node, base_node)
        self.graph.add_edge(pred_node, cond_node)
        prev_node = cond_node
        for arg_no, arg in enumerate(literal.args):  
            arg_node = self._get_condition_node(op_index, eff_index, cond_index, arg_no+1, arg)
            self.graph.add_vertex(arg_node, self._condition_color)
            self.graph.add_edge(prev_node, arg_node)
            prev_node = arg_node
            # edge argument to respective parameter or constant
            if arg[0] == "?":
                if arg in eff_args:
                    self.graph.add_edge(arg_node, eff_args[arg])
                else:
                    self.graph.add_edge(arg_node, op_args[arg])
            else:
                self.graph.add_edge(arg_node, self._get_obj_node(arg))

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

    def _add_operators(self, task):
        for op_index, op in enumerate(task.actions):
            op_node = self._get_operator_node(op_index, op.name)
            self.graph.add_vertex(op_node, self._operator_color)
            op_args = dict()
            for param in op.parameters:
                # parameter node
                param_node = self._get_operator_node(op.name, param.name)
                op_args[param.name] = param_node
                self.graph.add_vertex(param_node, self._operator_color)
                self.graph.add_edge(op_node, param_node)

            self._add_preconditions(op, op_index, op_node, op_args) 
               

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
