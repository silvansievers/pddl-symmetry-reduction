#! /usr/bin/env python

import sys

sys.path.append('.')
sys.path.append('./lib/python')
import pyext_blissmodule as bliss

g = bliss.create()
bliss.add_vertex(g, 0)
bliss.add_vertex(g, 1)
bliss.add_vertex(g, 1)
bliss.add_vertex(g, 1)
bliss.add_edge(g, 0, 1)
bliss.add_edge(g, 0, 2)
bliss.add_edge(g, 0, 3)
automorphisms = bliss.find_automorphisms(g)
assert type(automorphisms) is list

print "Python tester"
print "Got %d automorphism(s)" % len(automorphisms)
for aut_no, aut in enumerate(automorphisms):
    assert type(aut) is list
    print "automorphism #%d:" % aut_no
    for from_index, to_index in enumerate(aut):
        print "%d->%d" % (from_index, to_index)
