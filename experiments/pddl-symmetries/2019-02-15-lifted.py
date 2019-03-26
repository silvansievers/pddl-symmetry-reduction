#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not available, scatter plots not available'
    matplotlib = False

REVISION = '5f5e64d3c7de'

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    # optimal union satisficing
    suite = [
    'openstacks-sat08-adl', 'miconic-simpleadl', 'barman-sat14-strips',
    'transport-opt11-strips', 'openstacks-sat08-strips', 'logistics98',
    'parking-sat11-strips', 'psr-large', 'rovers', 'floortile-opt14-strips',
    'barman-opt14-strips', 'zenotravel', 'elevators-sat11-strips',
    'nomystery-opt11-strips', 'parcprinter-08-strips', 'tidybot-opt11-strips',
    'cavediving-14-adl', 'pegsol-opt11-strips', 'maintenance-opt14-adl',
    'citycar-opt14-adl', 'pipesworld-notankage', 'woodworking-sat08-strips',
    'woodworking-opt11-strips', 'driverlog', 'gripper', 'visitall-sat11-strips',
    'openstacks', 'hiking-opt14-strips', 'sokoban-opt11-strips',
    'tetris-sat14-strips', 'parcprinter-opt11-strips', 'openstacks-strips',
    'parcprinter-sat11-strips', 'grid', 'sokoban-opt08-strips',
    'elevators-opt08-strips', 'openstacks-sat14-strips', 'barman-sat11-strips',
    'tidybot-sat11-strips', 'mystery', 'visitall-opt14-strips',
    'childsnack-sat14-strips', 'sokoban-sat11-strips', 'trucks',
    'sokoban-sat08-strips', 'barman-opt11-strips', 'childsnack-opt14-strips',
    'parking-opt14-strips', 'openstacks-opt11-strips', 'elevators-sat08-strips',
    'movie', 'tidybot-opt14-strips', 'freecell', 'openstacks-opt14-strips',
    'scanalyzer-sat11-strips', 'ged-opt14-strips', 'pegsol-sat11-strips',
    'transport-opt08-strips', 'mprime', 'floortile-opt11-strips',
    'transport-sat08-strips', 'pegsol-08-strips', 'blocks',
    'floortile-sat11-strips', 'thoughtful-sat14-strips', 'openstacks-opt08-strips',
    'visitall-sat14-strips', 'pipesworld-tankage', 'scanalyzer-opt11-strips',
    'storage', 'maintenance-sat14-adl', 'optical-telegraphs',
    'elevators-opt11-strips', 'miconic', 'logistics00', 'depot',
    'transport-sat11-strips', 'openstacks-opt08-adl', 'psr-small', 'satellite',
    'assembly', 'citycar-sat14-adl', 'schedule', 'miconic-fulladl',
    'pathways-noneg', 'tetris-opt14-strips', 'ged-sat14-strips', 'pathways',
    'woodworking-opt08-strips', 'floortile-sat14-strips', 'nomystery-sat11-strips',
    'transport-opt14-strips', 'woodworking-sat11-strips', 'philosophers',
    'trucks-strips', 'hiking-sat14-strips', 'transport-sat14-strips',
    'openstacks-sat11-strips', 'scanalyzer-08-strips', 'visitall-opt11-strips',
    'psr-middle', 'airport', 'parking-opt11-strips', 'tpp', 'parking-sat14-strips']

    strips_suite = ['airport', 'barman-opt11-strips', 'barman-opt14-strips',
    'blocks', 'childsnack-opt14-strips', 'depot', 'driverlog',
    'elevators-opt08-strips', 'elevators-opt11-strips',
    'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell',
    'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips',
    'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery',
    'nomystery-opt11-strips', 'openstacks-opt08-strips',
    'openstacks-opt11-strips', 'openstacks-opt14-strips', 'openstacks-strips',
    'parcprinter-08-strips', 'parcprinter-opt11-strips',
    'parking-opt11-strips', 'parking-opt14-strips', 'pathways-noneg',
    'pegsol-08-strips', 'pegsol-opt11-strips', 'pipesworld-notankage',
    'pipesworld-tankage', 'psr-small', 'rovers', 'satellite',
    'scanalyzer-08-strips', 'scanalyzer-opt11-strips', 'sokoban-opt08-strips',
    'sokoban-opt11-strips', 'storage', 'tetris-opt14-strips',
    'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp',
    'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips',
    'visitall-opt14-strips', 'woodworking-opt08-strips',
    'woodworking-opt11-strips', 'zenotravel']

    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"], partition='infai_1')

    if is_test_run():
        suite = ['gripper:prob01.pddl', 'depot:p01.pddl', 'mystery:prob07.pddl', 'miconic-simpleadl:s1-0.pddl']
        environment = LocalEnvironment(processes=4)

    # NOTE: computation time of symmetries does not include computation of orders
    # because it is an extra command.
    configs = {
        IssueConfig('translate-symm-stabgoal-stabinit', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-symm-stabinit', ['--translate-options', '--compute-symmetries', '--do-not-stabilize-goal', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-symm-stabgoal', ['--translate-options', '--compute-symmetries', '--do-not-stabilize-initial-state', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-symm', ['--translate-options', '--compute-symmetries', '--do-not-stabilize-goal', '--do-not-stabilize-initial-state', '--bliss-time-limit', '300', '--stop-after-computing-symmetries', '--write-group-generators'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    exp.add_parser(exp.EXITCODE_PARSER)
    exp.add_parser(exp.TRANSLATOR_PARSER)
    exp.add_resource(name='compute_group_order', source='compute-group-order.py')
    exp.add_command('compute-group-order', ['{compute_group_order}'], time_limit=600, memory_limit=3584)
    exp.add_parser('symmetries-parser.py')

    generator_count_lifted = Attribute('generator_count_lifted', absolute=True, min_wins=False)
    generator_count_lifted_mapping_objects_predicates_functions = Attribute('generator_count_lifted_mapping_objects_predicates_functions', absolute=True, min_wins=False)
    time_symmetries1_symmetry_graph = Attribute('time_symmetries1_symmetry_graph', absolute=False, min_wins=True, functions=[geometric_mean])
    time_symmetries2_bliss = Attribute('time_symmetries2_bliss', absolute=False, min_wins=True, functions=[geometric_mean])
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    translator_completed = Attribute('translator_completed', absolute=True, min_wins=False)
    translate_out_of_memory = Attribute('translate_out_of_memory', absolute=True, min_wins=False)
    symmetry_graph_size = Attribute('symmetry_graph_size', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, functions=[geometric_mean])
    symmetry_group_order = Attribute('symmetry_group_order', absolute=True, min_wins=False)

    extra_attributes = [
        generator_count_lifted,
        generator_count_lifted_mapping_objects_predicates_functions,
        time_symmetries1_symmetry_graph,
        time_symmetries2_bliss,
        bliss_out_of_memory,
        bliss_out_of_time,
        translator_completed,
        translate_out_of_memory,
        symmetry_graph_size,
        time_symmetries,
        symmetry_group_order,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries*')

    exp.add_step('build', exp.build)
    exp.add_step('start', exp.start_runs)
    exp.add_fetcher(name='fetch')

    algorithm_nicks = [
        'translate-symm-stabgoal-stabinit',
        'translate-symm-stabinit',
        'translate-symm-stabgoal',
        'translate-symm',
    ]

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=['{}-{}'.format(REVISION, x) for x in algorithm_nicks])

    OLD_REV = 'e698d6049851'
    exp.add_fetcher('data/2018-09-12-lifted-eval',filter_algorithm=['{}-{}'.format(OLD_REV, x) for x in algorithm_nicks], merge=True)

    exp.add_report(
        ComparativeReport(
            algorithm_pairs=[('{}-{}'.format(OLD_REV, algorithm_nicks[i]), '{}-{}'.format(REVISION, algorithm_nicks[i])) for i in range(len(algorithm_nicks))],
            attributes=attributes,
        ),
        outfile=os.path.join(exp.eval_dir, exp.name + '-compare.html'),
    )

    exp.run_steps()

main(revisions=[REVISION])
