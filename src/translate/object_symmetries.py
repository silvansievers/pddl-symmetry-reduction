from collections import defaultdict
from itertools import combinations

import pddl

DEBUG = False

class QuickUnion:
    def __init__(self, all_objects):
        self.parent = {obj: obj for obj in all_objects}
        self.components = len(all_objects)

    def find(self, obj):
        while self.parent[obj] != obj:
            obj = self.parent[obj]
        return obj

    def union(self, object1, object2):
        id1 = self.find(object1)
        id2 = self.find(object2)
        if id1 == id2:
            return
        self.parent[id1] = id2
        self.components -= 1


# We silently remove all equivalence classes of size 1
def refine_by_type(candidate_sets, typed_objects):
    obj_by_type = defaultdict(set)
    for obj in typed_objects:
        obj_by_type[obj.type_name].add(obj.name)

    for t, objects in obj_by_type.items():
        new_candidate_sets = []
        for candidate in candidate_sets:
            new_cand = candidate & objects
            if new_cand and len(new_cand) > 1:
                new_candidate_sets.append(new_cand)
            new_cand = candidate - objects
            if new_cand and len(new_cand) > 1:
                new_candidate_sets.append(new_cand)
        candidate_sets = new_candidate_sets
    return candidate_sets


def refine_by_args(candidate_sets, args_by_name, relevant_names_by_obj=None):
    def are_symmetric(obj1, obj2, args_by_name):
        if (relevant_names_by_obj is not None and
            relevant_names_by_obj[obj1] != relevant_names_by_obj[obj2]):
            return False
        mapping = { obj1 : obj2, obj2: obj1 }
        for name, args_set in args_by_name.items():
            if relevant_names_by_obj:
                if name not in relevant_names_by_obj[obj1]:
                    continue
            for args in args_set:
                sym_args = tuple(mapping[o] if o in mapping else o for o in args)
                if sym_args not in args_set:
                    return False
        return True

    new_candidate_sets = []
    for candidate in candidate_sets:
        # special case for size two without union find structure
        if len(candidate) == 2:
            obj1, obj2 = candidate
            if are_symmetric(obj1, obj2, args_by_name):
                new_candidate_sets.append(candidate)
            continue
        uf = QuickUnion(candidate)
        for obj1, obj2 in combinations(candidate, 2):
            if uf.find(obj1) == uf.find(obj2):
                continue
            if are_symmetric(obj1, obj2, args_by_name):
                uf.union(obj1, obj2)
        if uf.components == 1:
            new_candidate_sets.append(candidate)
        else:
            equivalence_classes_by_id = defaultdict(set)
            for obj in candidate:
                equivalence_classes_by_id[uf.find(obj)].add(obj)
            for cand in equivalence_classes_by_id.values():
                if len(cand) > 1:
                    new_candidate_sets.append(cand)
    return new_candidate_sets


# We silently remove all equivalence classes of size 1
def refine_by_partial_state(state_atoms, candidate_sets, predicates_by_arity):
    state_by_predicate = defaultdict(set)
    for atom in state_atoms:
        if isinstance(atom, pddl.Atom) and atom.predicate not in predicates_by_arity[0]:
            # predicates of arity 0 are always symmetric
            state_by_predicate[atom.predicate].add(atom.args)
    for predicate in predicates_by_arity[1]:
        if predicate not in state_by_predicate:
            continue
        true = set(params[0] for params in state_by_predicate[predicate])
        new_candidate_sets = []
        for candidate in candidate_sets:
            new_cand = candidate & true
            if new_cand and len(new_cand) > 1:
                new_candidate_sets.append(new_cand)
            new_cand = candidate - true
            if new_cand and len(new_cand) > 1:
                new_candidate_sets.append(new_cand)
        candidate_sets = new_candidate_sets
        del state_by_predicate[predicate]

    return refine_by_args(candidate_sets, state_by_predicate)



def refine_by_mutex_groups(candidate_sets, mutex_groups):
    def are_symmetric(obj1, obj2, mutex_groups_by_object):
        mutex_groups1 = set(mutex_groups_by_object[obj1])
        mapping = { obj1: obj2, obj2 : obj1 }
        for group in mutex_groups_by_object[obj2]:
            symmetric_group = frozenset(atom.rename_variables(mapping)
                                        for atom in group)
            try:
                mutex_groups1.remove(symmetric_group)
            except KeyError:
                return False
        return not mutex_groups1 # symmetric if we have removed all original entries

    mutex_groups_by_object = defaultdict(set)
    relevant_objects = set().union(*candidate_sets)
    for group in mutex_groups:
        group_objects = set()
        for atom in group:
            group_objects.update(atom.args)
        group_objects &= relevant_objects
        if group_objects:
            frozen_group = frozenset(group)
            for obj in group_objects:
                mutex_groups_by_object[obj].add(frozen_group)
    new_candidate_sets = []
    for candidate in candidate_sets:
        if len(candidate) == 2:
            obj1, obj2 = candidate
            if are_symmetric(obj1, obj2, mutex_groups_by_object):
                new_candidate_sets.append(candidate)
            continue
        uf = QuickUnion(candidate)
        for obj1, obj2 in combinations(candidate, 2):
            if uf.find(obj1) == uf.find(obj2):
                continue
            if are_symmetric(obj1, obj2, mutex_groups_by_object):
                uf.union(obj1, obj2)
        if uf.components == 1:
            new_candidate_sets.append(candidate)
        else:
            equivalence_classes_by_id = defaultdict(set)
            for obj in candidate:
                equivalence_classes_by_id[uf.find(obj)].add(obj)
            for cand in equivalence_classes_by_id.values():
                if len(cand) > 1:
                    new_candidate_sets.append(cand)
    return new_candidate_sets


# note: we do not include constants (objects occurring in the domain
# description)
def compute_symmetric_object_sets(task, ground_actions, mutex_groups, reachable_atoms):
    # we are only interested in objects that are part of a reachable
    # atom. Filter in advance
    objects_set = set()
    for atom in reachable_atoms:
        objects_set.update(atom.args)

    predicates_by_arity = defaultdict(set)
    for predicate in task.predicates:
        predicates_by_arity[len(predicate.arguments)].add(predicate.name)

    candidate_sets = [objects_set]

    # process types
    candidate_sets = refine_by_type(candidate_sets, task.objects)
    if DEBUG:
        print("after refinement by type", candidate_sets)

    if not candidate_sets:
        return candidate_sets

    # process initial state
    # (we only stabilize the constant part of the initial state)
    fluent_predicates = set()
    for action in task.actions:
        for effect in action.effects:
            fluent_predicates.add(effect.literal.predicate)
    state_atoms = [atom for atom in task.init if isinstance(atom, pddl.Atom)
                   and atom.predicate != "=" and atom.predicate not in
                   fluent_predicates]
    if DEBUG:
        print("initial", state_atoms)
    # what about action costs? if we do not check all ground atoms, we need
    # to check the numeric assignments
    candidate_sets = refine_by_partial_state(state_atoms, candidate_sets, predicates_by_arity)
    if DEBUG:
        print("after processing the initial state:",  candidate_sets)

    if not candidate_sets:
        return candidate_sets

    # process goal
    if isinstance(task.goal, pddl.Atom):
        state_atoms = [task.goal]
    elif isinstance(task.goal, pddl.Conjunction):
        state_atoms = task.goal.parts
    candidate_sets = refine_by_partial_state(state_atoms, candidate_sets, predicates_by_arity)
    if DEBUG:
        print("after processing the goal:",  candidate_sets)

    if not candidate_sets:
        return candidate_sets

    # process actions
    actions_by_constant = defaultdict(list)
    for action in task.actions:
        constants = action.objects()
        for constant in constants:
            actions_by_constant[constant].append(action)
    constants = set(actions_by_constant.keys())

    new_candidate_sets = []
    for candidate in candidate_sets:
        candidate = candidate - constants
        if len(candidate) > 1:
            new_candidate_sets.append(candidate)
    candidate_sets = new_candidate_sets

    if DEBUG:
        print("after elimination of constants:", candidate_sets)
    if not candidate_sets:
        return candidate_sets

    # process ground actions
    ground_action_names_by_object = defaultdict(set)
    name_to_parameters = defaultdict(set)
    for action in ground_actions:
        action_name = action.name[1:-1]
        # openstack has actions without parameters which results
        # in the action name having a trailing white space.
        action_name = action_name.strip()
        name = action_name.split(' ')
        name_to_parameters[name[0]].add(tuple(name[1:]))
        for obj in name[1:]:
            ground_action_names_by_object[obj].add(name[0])
    candidate_sets = refine_by_args(candidate_sets, name_to_parameters,
            ground_action_names_by_object)
    if DEBUG:
        print("after processing ground action names:", candidate_sets)
    if not candidate_sets:
        return candidate_sets

    # process mutex groups
    candidate_sets = refine_by_mutex_groups(candidate_sets, mutex_groups)
    if DEBUG:
        print("after processing mutex groups:", candidate_sets)

    non_trivial_symmetric_object_sets = [sorted(symmetric_object_set)
            for symmetric_object_set in candidate_sets]
    print(f"Number of non-trivial symmetric object sets: {len(non_trivial_symmetric_object_sets)}")
    print(f"Non-trivial symmetric object sets: {non_trivial_symmetric_object_sets}")

    return non_trivial_symmetric_object_sets

