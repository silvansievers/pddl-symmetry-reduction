#! /usr/bin/env python

import sys

sys.path.append('.')
sys.path.append('./lib/python')
import intpybliss

g = intpybliss.create()
g.add_vertex(0)
g.add_vertex(1)
g.add_vertex(1)
g.add_edge(0, 1)
g.add_edge(0, 2)

print "hi"
