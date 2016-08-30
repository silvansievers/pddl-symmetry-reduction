#! /usr/bin/env python

import sys

sys.path.append('.')
sys.path.append('./lib/python')
import pybliss

g = pybliss.create()
pybliss.add_vertex(g, 0)
pybliss.add_vertex(g, 1)
pybliss.add_vertex(g, 1)
pybliss.add_vertex(g, 1)
pybliss.add_edge(g, 0, 1)
pybliss.add_edge(g, 0, 2)
pybliss.add_edge(g, 0, 3)
automorphisms = pybliss.find_automorphisms(g)
assert type(automorphisms) is list

print "Python tester"
print "Got %d automorphism(s)" % len(automorphisms)
for aut_no, aut in enumerate(automorphisms):
    assert type(aut) is list
    print "automorphism #%d:" % aut_no
    for from_index, to_index in enumerate(aut):
        print "%d->%d" % (from_index, to_index)
