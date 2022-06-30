import argparse
import sys


def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "domain", help="path to domain pddl file")
    argparser.add_argument(
        "task", help="path to task pddl file")
    argparser.add_argument(
        "--relaxed", dest="generate_relaxed_task", action="store_true",
        help="output relaxed task (no delete effects)")
    argparser.add_argument(
        "--full-encoding",
        dest="use_partial_encoding", action="store_false",
        help="By default we represent facts that occur in multiple "
        "mutex groups only in one variable. Using this parameter adds "
        "these facts to multiple variables. This can make the meaning "
        "of the variables clearer, but increases the number of facts.")
    argparser.add_argument(
        "--invariant-generation-max-candidates", default=100000, type=int,
        help="max number of candidates for invariant generation "
        "(default: %(default)d). Set to 0 to disable invariant "
        "generation and obtain only binary variables. The limit is "
        "needed for grounded input files that would otherwise produce "
        "too many candidates.")
    argparser.add_argument(
        "--sas-file", default="output.sas",
        help="path to the SAS output file (default: %(default)s)")
    argparser.add_argument(
        "--invariant-generation-max-time", default=300, type=int,
        help="max time for invariant generation (default: %(default)ds)")
    argparser.add_argument(
        "--add-implied-preconditions", action="store_true",
        help="infer additional preconditions. This setting can cause a "
        "severe performance penalty due to weaker relevance analysis "
        "(see issue7).")
    argparser.add_argument(
        "--keep-unreachable-facts",
        dest="filter_unreachable_facts", action="store_false",
        help="keep facts that can't be reached from the initial state")
    argparser.add_argument(
        "--skip-variable-reordering",
        dest="reorder_variables", action="store_false",
        help="do not reorder variables based on the causal graph. Do not use "
        "this option with the causal graph heuristic!")
    argparser.add_argument(
        "--keep-unimportant-variables",
        dest="filter_unimportant_vars", action="store_false",
        help="keep variables that do not influence the goal in the causal graph")
    argparser.add_argument(
        "--dump-task", action="store_true",
        help="dump human-readable SAS+ representation of the task")
    argparser.add_argument(
        "--layer-strategy", default="min", choices=["min", "max"],
        help="How to assign layers to derived variables. 'min' attempts to put as "
        "many variables into the same layer as possible, while 'max' puts each variable "
        "into its own layer unless it is part of a cycle.")

    # Options related to symmetries (computed via abstract structure graph)
    argparser.add_argument(
        "--compute-symmetries", action="store_true",
        help="compute symmetries on the normalized taks using bliss, dump "
        "statistics")
    argparser.add_argument(
        "--only-object-symmetries", action="store_true",
        help="Only allow objects to be permuted, but not "
        "predicates or functions. (Set option --compute-symmetries)")
    argparser.add_argument(
        "--do-not-stabilize-initial-state", action="store_true",
        help="If true, only those atoms in the initial state mentioning "
        "static predicates are added. (Set option --compute-symmetries)")
    argparser.add_argument(
        "--do-not-stabilize-goal", action="store_true",
        help="If true, the goal is ignored in the symmetry computation. "
        "(Set option --compute-symmetries)")
    argparser.add_argument(
        "--bliss-time-limit", default=300, type=int,
        help="Max time for bliss to search for automorphisms. (Set option "
        "--compute-symmetries)")
    argparser.add_argument(
        "--write-group-generators", action="store_true",
        help="If true, write the group generators to the file 'generators.py'. "
        "Each line contains a list of integers in the Python list format. "
        "The list is to be read as a permutation of the integers 0 to length "
        "of the list. (Set option --compute-symmetries)")
    argparser.add_argument(
        "--write-dot-graph", action="store_true",
        help="If true, write the symmetry graph in dot format to the file "
        "out.dot. (Set option --compute-symmetries)")
    argparser.add_argument(
        "--stop-after-computing-symmetries", action="store_true",
        help="If true, stop after computing symmetries. (Set option "
        "--compute-symmetries)")

    # Options related to computing symmetric object sets
    argparser.add_argument(
        "--compute-symmetric-object-sets-from-symmetries", action="store_true",
        help="If true, compute symmetric object sets of object symmetry "
        "generators. (Set options --compute-symmetries and "
        "--only-object-symmetries and do not set option "
        "--compute-symmetric-object-sets-directly)")
    argparser.add_argument(
        "--compute-symmetric-object-sets-directly", action="store_true",
        help="If true, compute all object symmetries brute force and "
        "symmetric object sets based on these object symemtries. (Do not "
        "set option --compute-symmetric-object-sets-from-symmetries)")

    # Options related to grounding of symmetries (computed via abstract structure graph)
    argparser.add_argument(
        "--preserve-symmetries-during-grounding", action="store_true",
        help="If true, grounding preserves unreachable structures (axioms, "
        "operators, ...) if they are symmetric to a reachable structure.")
    argparser.add_argument(
        "--ground-symmetries", action="store_true",
        help="If true, ground lifted symmetries to the search representation, "
        "mapping facts to facts.")
    argparser.add_argument(
        "--add-none-of-those-mappings", action="store_true",
        help="This option is only useful if using --ground-symmetries."
        "If true, add mappings to generators for none-of-those values: "
        "if the var is not mapped to another var, then set identity. Otherwise, "
        "map to the none-of-those-value of the mapped variable. This assumes "
        "that vars are entirely mapped to vars, or not mapped at all. This has "
        "been asserted on IPC tasks. "
        "If this option is used, generators that map none-of-those values to "
        "none-of-those values of other variables are *not* filtered out as "
        "they would otherwise be.")

    # Options related to computation of h2 mutexes
    argparser.add_argument(
        "--h2-mutexes", action="store_true",
        help="If true, compute h2 mutex groups.")
    argparser.add_argument(
        "--only-positive-literals", action="store_true",
        help="If true, relax the computation of h2 mutexes by not considering "
        "negative literals. (Set option --h2-mutexes)")

    # Options related to symmetry-based reduction and expansion
    argparser.add_argument(
        "--symmetry-reduced-grounding", action="store_true",
        help="If true, compute a task reduction based on all large enough "
        "symemtric object sets. (Set option "
        "--compute-symmetric-object-sets-from-symmetries or "
        "--compute-symmetric-object-sets-directly)")
    argparser.add_argument(
        "--symmetry-reduced-grounding-for-h2-mutexes", action="store_true",
        help="If true, compute a task reduction based on all large enough "
        "symemtric object sets, computing the minimum size as required for "
        "computing h2 mutexes on the reduction. (Set option "
        "--compute-symmetric-object-sets-from-symmetries or "
        "--compute-symmetric-object-sets-directly)")
    argparser.add_argument(
        "--expand-reduced-task", action="store_true",
        help="If true, expand the model of a symmetry-reduced task before "
        "instantiating it. (Set option --symmetry-reduced-grounding)")
    argparser.add_argument(
        "--expand-reduced-h2-mutexes", action="store_true",
        help="If true, expand the set of h2 mutexes computed on a "
        "symmetry-reduced task. (Set options "
        "--symmetry-reduced-grounding-for-h2-mutexes and --h2-mutexes)")
    argparser.add_argument(
        "--assert-equal-grounding", action="store_true",
        help="If true, assert that using --symmetry-reduced-grounding + "
        "--expand-reduced-task yields the same result as regular grounding. "
        "(Set the two obvious options.)")
    argparser.add_argument(
        "--assert-equal-h2-mutexes", action="store_true",
        help="If true, assert that using --symmetry-reduced-grounding-for-h2-mutexes "
        "+ --expand-reduced-h2-mutexes yields the same result as regular "
        "computation of h2-mutexes. (Set the two obvious options.)")

    return argparser.parse_args()


def copy_args_to_module(args):
    module_dict = sys.modules[__name__].__dict__
    for key, value in vars(args).items():
        module_dict[key] = value


def setup():
    args = parse_args()
    copy_args_to_module(args)


setup()
