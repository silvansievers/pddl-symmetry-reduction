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

    def _in(self, name):
        return "%s_i" % name

    def _from_in(self, name):
        return name[0:-2]
    
    def _out(self, name):
        return "%s_o" % name

    def _edge(self, n1, n2):
        return "_%s_%s_0" % (n1, n2), "_%s_%s_1" % (n1, n2) 
        # TODO this is dangerous because n1 and n2 could contain underscores

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

    def __init__(self, task):
        self.graph = Digraph()
        self._object_color = 0
        self._first_predicate_color = 1
        self._add_objects(task)
        max_predicate_color = self._add_predicates(task)
        print ("max predicate color", max_predicate_color)
        self._init_color = max_predicate_color + 1
        self._goal_color = max_predicate_color + 2
        self._add_init(task)
        self._add_goal(task)
        test = self.graph.get_autiomorphism_generators()
        for generator in test:
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

    def write_dot(self, file):
        """
        Write the graph into a file in the graphviz dot format.
        """


        colors = {
                self._object_color: ("X11","blue"),
                self._init_color: ("X11", "lightyellow"),
                self._goal_color: ("X11", "yellow"),
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
