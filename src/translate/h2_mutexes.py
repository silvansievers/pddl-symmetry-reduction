#! /usr/bin/env python

from collections import deque, defaultdict
from itertools import combinations

import sys

import pddl
import timers

DEBUG = False

# We represent literals als tuples (atom, True/False) where True means
# the literal is positive and False means the literal is negative.


def get_atom(literal):
    return literal[0]


def is_positive(literal):
    return literal[1]


def compute_all_pairs(element_dict, only_positive_literals=False):
    if only_positive_literals:
        elements = dict(e for e in element_dict.items() if is_positive(e))
    else:
        elements = element_dict
    pairs = [frozenset([e]) for e in elements.items()]
    for pair in combinations(elements.items(), 2):
        pairs.append(frozenset(pair))
    return pairs


def extract_literals_from_condition(condition):
    result = dict()
    if condition is None: # e.g. empty effect condition
        return result
    if isinstance(condition, list): # e.g. effect condition
        for cond in condition:
            result.update(extract_literals_from_condition(cond))
    elif isinstance(condition, pddl.Literal):
        if condition.negated:
            result[condition.negate()] = False
        else:
            result[condition] = True
    else:
        print(condition)
        assert False
    return result


def add_rule(pair_to_rules, pair_index, rules, condition_pairs):
    for cond_pair in condition_pairs:
        pair_to_rules[cond_pair].append(len(rules)) # fails if cond_pair is unknown
        if DEBUG:
            print("adding rule index {} to pair".format(len(rules)))
    if DEBUG:
        print("adding rule with body {}".format(condition_pairs))
    rules.append([pair_index, len(condition_pairs)])


def handle_axiom(pairs, axiom, pair_to_rules, rules, only_positive_literals):
    assert isinstance(axiom.effect, pddl.Literal)
    for pair_index, pair in enumerate(pairs):
        if len(pair) == 1:
            literal = next(iter(pair))
            if get_atom(literal) == axiom.effect: # 2) axiom from which literal can be derived
                condition_literals = \
                    extract_literals_from_condition(axiom.condition)
                condition_pairs = compute_all_pairs(condition_literals,
                                                    only_positive_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)
        else:
            literals = list(pair)
            literal1 = literals[0]
            literal2 = literals[1]
            axiom_makes_literal1_true = (is_positive(literal1) and get_atom(literal1) == axiom.effect)
            axiom_makes_literal2_true = (is_positive(literal2) and get_atom(literal2) == axiom.effect)
            if axiom_makes_literal1_true or axiom_makes_literal2_true:
                #  3) axiom from which literal1 or literal2 can be derived
                condition_literals = extract_literals_from_condition(axiom.condition)
                # Depending on which literal is made true by the axiom, add the other
                # to condition_literals unless the rule body would be inconsistent.
                if axiom_makes_literal1_true:
                    if (get_atom(literal2) in condition_literals and
                        condition_literals[get_atom(literal2)] != is_positive(literal2)):
                        # \psi \land literal2 is inconsistent, skip rule
                        continue
                    condition_literals[get_atom(literal2)] = is_positive(literal2)
                else:
                    if (get_atom(literal1) in condition_literals and
                        condition_literals[get_atom(literal1)] != is_positive(literal1)):
                        # \psi \land literal1 is inconsistent, skip rule
                        continue
                    condition_literals[get_atom(literal1)] = is_positive(literal1)
                condition_pairs = compute_all_pairs(condition_literals,
                                                     only_positive_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def combine_dicts_if_consistent(literal_dict1, literal_dict2):
    result = literal_dict1.copy()
    for atom, positive in literal_dict2.items():
        if atom in literal_dict1 and literal_dict1[atom] != positive:
            return None
        result[atom] = positive
    return result


def is_subset(literal_dict1, literal_dict2):
    for atom, positive in literal_dict1.items():
        if not atom in literal_dict2 or literal_dict2[atom] != positive:
            return False
    return True


def effect_makes_opposite_literal_true(literal, conditions_by_effect, relevant_literals):
    # Go over the effects that make the negated literal true and check
    # if any of the effects can trigger; if so, return true.
    for psi in conditions_by_effect[(get_atom(literal), not is_positive(literal))]:
        if is_subset(psi, relevant_literals):
            return True
    return False


def handle_operator_for_literal(literal, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_literals, only_positive_literals):
    # Since l = l', there is no second effect phi' -> l', since l = l'.
    for condition in conditions_by_effect[literal]:
        relevant_literals = combine_dicts_if_consistent(pre_literals, condition)
        if relevant_literals is None:
            # pre \land condition is inconsistent, skip rule
            continue

        if not is_positive(literal):
            if effect_makes_opposite_literal_true(literal, conditions_by_effect, relevant_literals):
                # ~literal can become true, skip rule
                continue

        condition_pairs = compute_all_pairs(relevant_literals,
                                            only_positive_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_pair_single_effect(literal, preserve_literal, pair_to_rules,
    pair_index, rules, conditions_by_effect, pre_literals, only_positive_literals):

    for phi in conditions_by_effect[literal]:
        relevant_literals = combine_dicts_if_consistent(pre_literals, phi)
        if relevant_literals is None:
            # pre \land phi is inconsistent, skip rule
            continue

        if effect_makes_opposite_literal_true(preserve_literal, conditions_by_effect, relevant_literals):
            # ~preserve_literal can become true, skip rule
            continue

        if (get_atom(preserve_literal) in relevant_literals and
            relevant_literals[get_atom(preserve_literal)] != is_positive(preserve_literal)):
            # pre \land phi \land l' is inconsistent, skip rule
            continue
        relevant_literals[get_atom(preserve_literal)] = is_positive(preserve_literal)

        if not is_positive(literal):
            if effect_makes_opposite_literal_true(literal, conditions_by_effect, relevant_literals):
                # ~literal can become true, skip rule
                continue

        condition_pairs = compute_all_pairs(relevant_literals,
                                            only_positive_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_pair(literal1, literal2, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_literals, only_positive_literals):
    # first case: both possibly made true by operator
    for phi1 in conditions_by_effect[literal1]:
        tmp_relevant_literals = combine_dicts_if_consistent(pre_literals, phi1)
        if tmp_relevant_literals is None:
            # pre \land \phi1 is inconsistent
            continue

        for phi2 in conditions_by_effect[literal2]:
            relevant_literals = combine_dicts_if_consistent(tmp_relevant_literals, phi2)
            if relevant_literals is None:
                # pre \land \phi1 \land \phi2 is inconsistent
                continue

            if not is_positive(literal1):
                if effect_makes_opposite_literal_true(literal1, conditions_by_effect, relevant_literals):
                    # ~literal1 can become true, skip rule
                    continue

            if not is_positive(literal2):
                if effect_makes_opposite_literal_true(literal2, conditions_by_effect, relevant_literals):
                    # ~literal2 can become true, skip rule
                    continue

            condition_pairs = compute_all_pairs(relevant_literals,
                                                only_positive_literals)
            add_rule(pair_to_rules, pair_index, rules, condition_pairs)

    # second case: one possibly made true whereas the other is preserved
    handle_operator_for_pair_single_effect(literal1, literal2, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_literals, only_positive_literals)
    handle_operator_for_pair_single_effect(literal2, literal1, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_literals, only_positive_literals)


def handle_operator(pairs, operator, pair_to_rules, rules, only_positive_literals):
    conditions_by_effect = defaultdict(list)
    for cond, eff in operator.add_effects:
        condition_literals = extract_literals_from_condition(cond)
        conditions_by_effect[(eff, True)].append(condition_literals)
    for cond, eff in operator.del_effects:
        condition_literals = extract_literals_from_condition(cond)
        conditions_by_effect[(eff, False)].append(condition_literals)
    pre_literals = extract_literals_from_condition(operator.precondition)

    for pair_index, pair in enumerate(pairs):
        if len(pair) == 1:
            handle_operator_for_literal(next(iter(pair)), pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_literals,
                only_positive_literals)
        else:
            literals = list(pair)
            handle_operator_for_pair(literals[0], literals[1], pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_literals,
                only_positive_literals)


def compute_reachability_program(atoms, actions, axioms, only_positive_literals):
    timer = timers.Timer()
    literals = [(a,True) for a in atoms]
    if not only_positive_literals:
        for atom in atoms:
            literals.append((atom, False))

    # pair contains both "singleton pairs" and "real pairs".
    pairs = [frozenset([e]) for e in literals]
    for pair in combinations(literals, 2):
        pairs.append(frozenset(pair))

    rules = []
    pair_to_rules = {}
    # Manually set empty list for each pair to enforce key errors when
    # attempting to access unknown pairs later.
    for pair in pairs:
        pair_to_rules[pair] = []

    for op in actions:
        handle_operator(pairs, op, pair_to_rules, rules, only_positive_literals)
    for ax in axioms:
        handle_axiom(pairs, ax, pair_to_rules, rules, only_positive_literals)
    print("Time to compute h2 mutexes reachability program: {}s".format(timer.elapsed_time()))
    sys.stdout.flush()
    return pairs, pair_to_rules, rules


def compute_mutex_pairs(task, atoms, actions, axioms, reachable_action_params,
    only_positive_literals=False):
    pairs, pair_to_rules, rules = compute_reachability_program(atoms, actions,
        axioms, only_positive_literals)

    if DEBUG:
        for key,val in pair_to_rules.items():
            print(key, val)

        for rule in rules:
            pair = pairs[rule[0]]
            num_conditions = rule[1]
            print("{} <- {}".format(pair, num_conditions))

    timer = timers.Timer()
    open_list = deque()
    closed = set()
    init = set(task.init)
    init &= atoms
    initially_true_literals = dict()
    for atom in atoms:
        if atom in init:
            initially_true_literals[atom] = True
        elif not only_positive_literals:
            initially_true_literals[atom] = False
    initial_pairs = compute_all_pairs(initially_true_literals)
    for pair in initial_pairs:
        assert pair not in closed
        open_list.append(pair)
        closed.add(pair)
    while len(open_list):
        pair = open_list.popleft()
        #print("pop pair {}".format(pair))
        for rule_index in pair_to_rules[pair]:
            rule = rules[rule_index]
            #print("deal with rule index {} which is rule {}".format(rule_index, rule))
            assert(rule[1] > 0)
            rule[1] = rule[1] - 1

            if rule[1] == 0:
                # handle applicable rule (the test against closed prevents
                # rules from being handled more than once)
                new_pair = pairs[rule[0]]
                #print("new pair {}".format(new_pair))
                if new_pair not in closed: # already dealt with new_pair
                    #print("must be queued")
                    closed.add(new_pair)
                    open_list.append(new_pair)

    print("Found {} reachable pairs of literals".format(len(closed)))
    sys.stdout.flush()
    if DEBUG:
        for pair in closed:
            for lit in pair:
                print(lit),
            print

    mutex_pairs = []
    for pair in pairs:
        if pair not in closed:
            new_pair = []
            for literal in pair:
                if is_positive(literal):
                    new_pair.append(get_atom(literal))
                else:
                    new_pair.append(get_atom(literal).negate())
            mutex_pairs.append(frozenset(new_pair))
    print("Found {} unreachable pairs of literals".format(len(mutex_pairs)))
    if DEBUG:
        for pair in mutex_pairs:
            for lit in pair:
                print(lit),
            print

    print("Time to compute model of reachability program: {}s".format(timer.elapsed_time()))
    sys.stdout.flush()
    return mutex_pairs
