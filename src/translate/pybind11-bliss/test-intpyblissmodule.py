#! /usr/bin/env python

import sys

sys.path.append('.')
sys.path.append('./lib/python')
import intpybliss

g = intpybliss.create()
intpybliss.add_vertex(g, 0)
intpybliss.add_vertex(g, 1)
intpybliss.add_vertex(g, 1)
intpybliss.add_vertex(g, 1)
intpybliss.add_edge(g, 0, 1)
intpybliss.add_edge(g, 0, 2)
intpybliss.add_edge(g, 0, 3)
intpybliss.find_automorphisms(g)
automorphisms = intpybliss.get_automorphisms(g)
assert type(automorphisms) is list

print "Python tester"
print "Got %d automorphism(s)" % len(automorphisms)
for aut_no, aut in enumerate(automorphisms):
    assert type(aut) is list
    print "automorphism #%d:" % aut_no
    for from_index, to_index in enumerate(aut):
        print "%d->%d" % (from_index, to_index)
