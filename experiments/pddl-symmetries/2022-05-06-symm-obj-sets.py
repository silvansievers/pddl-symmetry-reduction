#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import subprocess
import sys

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print('matplotlib not available, scatter plots not available')
    matplotlib = False

OLD_REV = 'b4509f30bd033a59f4889226af99847f9cb2fe06'
NEW_REV = '2b694fc41d05789ad72f206653a1ef903710311d'

def main(revisions=None):
    benchmarks_dir = os.environ['DOWNWARD_BENCHMARKS']
    opt_strips = ['agricola-opt18-strips', 'airport', 'barman-opt11-strips', 'barman-opt14-strips', 'blocks', 'childsnack-opt14-strips', 'data-network-opt18-strips', 'depot', 'driverlog', 'elevators-opt08-strips', 'elevators-opt11-strips', 'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell', 'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips', 'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery', 'nomystery-opt11-strips', 'openstacks-opt08-strips', 'openstacks-opt11-strips', 'openstacks-opt14-strips', 'openstacks-strips', 'organic-synthesis-opt18-strips', 'organic-synthesis-split-opt18-strips', 'parcprinter-08-strips', 'parcprinter-opt11-strips', 'parking-opt11-strips', 'parking-opt14-strips', 'pathways', 'pegsol-08-strips', 'pegsol-opt11-strips', 'petri-net-alignment-opt18-strips', 'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers', 'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips', 'snake-opt18-strips', 'sokoban-opt08-strips', 'sokoban-opt11-strips', 'spider-opt18-strips', 'storage', 'termes-opt18-strips', 'tetris-opt14-strips', 'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp', 'transport-opt08-strips', 'transport-opt11-strips', 'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips', 'visitall-opt14-strips', 'woodworking-opt08-strips', 'woodworking-opt11-strips', 'zenotravel']

    sat_strips = ['agricola-sat18-strips', 'airport', 'barman-sat11-strips', 'barman-sat14-strips', 'blocks', 'childsnack-sat14-strips', 'data-network-sat18-strips', 'depot', 'driverlog', 'elevators-sat08-strips', 'elevators-sat11-strips', 'floortile-sat11-strips', 'floortile-sat14-strips', 'freecell', 'ged-sat14-strips', 'grid', 'gripper', 'hiking-sat14-strips', 'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery', 'nomystery-sat11-strips', 'openstacks-sat08-strips', 'openstacks-sat11-strips', 'openstacks-sat14-strips', 'openstacks-strips', 'organic-synthesis-sat18-strips', 'organic-synthesis-split-sat18-strips', 'parcprinter-08-strips', 'parcprinter-sat11-strips', 'parking-sat11-strips', 'parking-sat14-strips', 'pathways', 'pegsol-08-strips', 'pegsol-sat11-strips', 'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers', 'satellite', 'scanalyzer-08-strips', 'scanalyzer-sat11-strips', 'snake-sat18-strips', 'sokoban-sat08-strips', 'sokoban-sat11-strips', 'spider-sat18-strips', 'storage', 'termes-sat18-strips', 'tetris-sat14-strips', 'thoughtful-sat14-strips', 'tidybot-sat11-strips', 'tpp', 'transport-sat08-strips', 'transport-sat11-strips', 'transport-sat14-strips', 'trucks-strips', 'visitall-sat11-strips', 'visitall-sat14-strips', 'woodworking-sat08-strips', 'woodworking-sat11-strips', 'zenotravel']

    suite_neg_precs_requirements = ['agricola-opt18-strips', 'agricola-sat18-strips', 'caldera-opt18-adl', 'caldera-sat18-adl', 'citycar-opt14-adl', 'citycar-sat14-adl', 'data-network-opt18-strips', 'data-network-sat18-strips', 'mprime', 'organic-synthesis-opt18-strips', 'organic-synthesis-sat18-strips', 'organic-synthesis-split-opt18-strips', 'settlers-opt18-adl', 'settlers-sat18-adl', 'snake-opt18-strips', 'snake-sat18-strips', 'spider-opt18-strips', 'spider-sat18-strips', 'termes-opt18-strips', 'termes-sat18-strips', 'tetris-opt14-strips', 'tetris-sat14-strips']

    suite = set(opt_strips) | set(sat_strips)
    suite -= set(suite_neg_precs_requirements)
    suite = sorted(suite)

    environment = BaselSlurmEnvironment(
        email="silvan.sievers@unibas.ch", export=["PATH"], partition='infai_2')

    if is_test_run():
        suite = [
            'gripper:prob01.pddl',
            # 'depot:p01.pddl',
            'transport-opt08-strips:p01.pddl',
            'pathways:p01.pddl',
            'mystery:prob07.pddl',
            'miconic:s1-0.pddl',
        ]
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate-symm-objsymms-symmobjsetfromsymm', ['--translate-options', '--compute-symmetries', '--only-object-symmetries', '--compute-symmetric-object-sets-from-symmetries', '--do-not-stabilize-initial-state', '--do-not-stabilize-goal', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-symm-objsymms-stabgoal-stabinit-symmobjsetfromsymm', ['--translate-options', '--compute-symmetries', '--only-object-symmetries', '--compute-symmetric-object-sets-from-symmetries', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-symmobjsetdirect', ['--translate-options', '--compute-symmetric-object-sets-directly', '--stop-after-computing-symmetries'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    exp.add_parser(exp.EXITCODE_PARSER)
    exp.add_parser(exp.TRANSLATOR_PARSER)
    exp.add_parser('symmetries-parser.py')
    exp.add_parser('symm-obj-parser.py')

    num_lifted_generators = Attribute('num_lifted_generators', absolute=True, min_wins=False)
    time_symmetries1_symmetry_graph = Attribute('time_symmetries1_symmetry_graph', absolute=False, min_wins=True, function=geometric_mean)
    time_symmetries2_bliss = Attribute('time_symmetries2_bliss', absolute=False, min_wins=True, function=geometric_mean)
    time_symmetries3_translate = Attribute('time_symmetries3_translate', absolute=False, min_wins=True, function=geometric_mean)
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    symmetry_graph_size = Attribute('symmetry_graph_size', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, function=geometric_mean)
    symmetry_group_order = Attribute('symmetry_group_order', absolute=False, min_wins=False)
    symmetries_only_affect_objects = Attribute('symmetries_only_affect_objects', absolute=True, min_wins=False)
    symmetries_only_affect_predicates = Attribute('symmetries_only_affect_predicates', absolute=True, min_wins=False)
    symmetries_only_affect_functions = Attribute('symmetries_only_affect_functions', absolute=True, min_wins=False)

    num_object_symmetries = Attribute('num_object_symmetries', absolute=True, min_wins=False)
    number_symmetric_object_sets = Attribute('number_symmetric_object_sets', absolute=True, min_wins=False)
    time_symm_obj_sets = Attribute('time_symm_obj_sets', absolute=False, min_wins=True, function=geometric_mean)

    extra_attributes = [
        num_lifted_generators,
        time_symmetries1_symmetry_graph,
        time_symmetries2_bliss,
        time_symmetries3_translate,
        bliss_out_of_memory,
        bliss_out_of_time,
        symmetry_graph_size,
        time_symmetries,
        symmetry_group_order,
        symmetries_only_affect_objects,
        symmetries_only_affect_predicates,
        symmetries_only_affect_functions,

        num_object_symmetries,
        number_symmetric_object_sets,
        time_symm_obj_sets,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries*')

    exp.add_step('build', exp.build)
    exp.add_step('start', exp.start_runs)
    exp.add_fetcher(name='fetch')

    algorithm_nicks = [
        'translate-symm-objsymms-symmobjsetfromsymm',
        'translate-symm-objsymms-stabgoal-stabinit-symmobjsetfromsymm',
        'translate-symmobjsetdirect',
    ]

    exp.add_absolute_report_step(
        attributes=attributes,
        filter_algorithm=['{}-{}'.format(NEW_REV, x) for x in algorithm_nicks])

    exp.add_fetcher(
        'data/2022-05-05-symm-obj-sets-eval',
        filter_algorithm=['{}-{}'.format(OLD_REV, x) for x in algorithm_nicks],
        merge=True)

    exp.add_comparison_table_step(revisions=[OLD_REV, NEW_REV], attributes=attributes)

    exp.run_steps()

main(revisions=[NEW_REV])
