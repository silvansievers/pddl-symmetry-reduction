#! /usr/bin/env python
# -*- coding: utf-8 -*-

import queue

from sympy.combinatorics.permutations import Permutation
from sympy.combinatorics.perm_groups import PermutationGroup


def compute_group_order_sympy(generators):
    sympy_permutations = [Permutation(gen) for gen in generators]
    sympy_group = PermutationGroup(sympy_permutations)
    return sympy_group.order()


def permute(automorphism, gen):
    # print "permuting %s with %s" % (automorphism, gen)
    result = list(automorphism)
    gen_mapping = dict([(key, val) for key, val in enumerate(gen)])
    for key, val in enumerate(automorphism):
        result[key] = gen_mapping[val]
    # print "result: %s" % result
    return tuple(result)


def compute_group_order_manual(generators):
    closed = set()
    open_list = queue.Queue()
    for gen in generators:
        closed.add(tuple(gen))
        open_list.put(tuple(gen))
    while not open_list.empty():
        automorphism = open_list.get()
        for gen in generators:
            if gen != automorphism:
                new_automorphism = permute(automorphism, gen)
                if new_automorphism not in closed:
                    closed.add(tuple(new_automorphism))
                    open_list.put(tuple(new_automorphism))
    return len(closed)

if __name__ == "__main__":
    file_name = "generators.py"
    print("Running symmetry group order computation...")
    order = 0
    gens = []
    try:
        with open(file_name) as f:
            for line in f:
                line = line.strip('\n')
                line = line.replace('[', '')
                line = line.replace(']', '')
                line = line.replace(',', '')
                if line == '':
                    continue
                line = line.split(' ')
                line = [int(x) for x in line]
                gens.append(line)
    except IOError as err:
        print("%s does not exist" % file_name)
    if gens:
        order = compute_group_order_sympy(gens)
    print("Symmetry group order: %d" % order)
