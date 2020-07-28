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

REVISION = 'e028b93170de'

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

    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        suite = ['gripper:prob01.pddl', 'depot:p01.pddl', 'mystery:prob07.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),
        IssueConfig('translate-symm-stabinit', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--bliss-time-limit', '300', ], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    exp.add_parser('lab_driver_parser', exp.LAB_DRIVER_PARSER)
    exp.add_parser('exitcode_parser', exp.EXITCODE_PARSER)
    exp.add_parser('translator_parser', exp.TRANSLATOR_PARSER)
    exp.add_parser('symmetries_parser', 'symmetries-parser.py')

    generator_count_lifted = Attribute('generator_count_lifted', absolute=True, min_wins=False)
    generator_count_lifted_mapping_objects_predicates = Attribute('generator_count_lifted_mapping_objects_predicates', absolute=True, min_wins=False)
    generator_orders_lifted = Attribute('generator_orders_lifted', absolute=True)
    generator_orders_lifted_list = Attribute('generator_orders_lifted_list', absolute=True)
    generator_order_lifted_2 = Attribute('generator_order_lifted_2', absolute=True, min_wins=False)
    generator_order_lifted_3 = Attribute('generator_order_lifted_3', absolute=True, min_wins=False)
    generator_order_lifted_4 = Attribute('generator_order_lifted_4', absolute=True, min_wins=False)
    generator_order_lifted_5 = Attribute('generator_order_lifted_5', absolute=True, min_wins=False)
    generator_order_lifted_6 = Attribute('generator_order_lifted_6', absolute=True, min_wins=False)
    generator_order_lifted_7 = Attribute('generator_order_lifted_7', absolute=True, min_wins=False)
    generator_order_lifted_8 = Attribute('generator_order_lifted_8', absolute=True, min_wins=False)
    generator_order_lifted_9 = Attribute('generator_order_lifted_9', absolute=True, min_wins=False)
    generator_order_lifted_max = Attribute('generator_order_lifted_max', absolute=True, min_wins=False)
    generator_count_grounded_1_after_grounding = Attribute('generator_count_grounded_1_after_grounding', absolute=True, min_wins=False)
    generator_count_grounded_2_after_sas_task = Attribute('generator_count_grounded_2_after_sas_task', absolute=True, min_wins=False)
    generator_count_grounded_3_after_filtering_props = Attribute('generator_count_grounded_3_after_filtering_props', absolute=True, min_wins=False)
    generator_count_grounded_4_after_reordering_filtering_vars = Attribute('generator_count_grounded_4_after_reordering_filtering_vars', absolute=True, min_wins=False)
    generator_count_grounded = Attribute('generator_count_grounded', absolute=True, min_wins=False)
    generator_count_removed = Attribute('generator_count_removed', absolute=True, min_wins=True)
    generator_lifted_affecting_actions_axioms = Attribute('generator_lifted_affecting_actions_axioms', absolute=True, min_wins=True)
    generator_lifted_mapping_actions_axioms = Attribute('generator_lifted_mapping_actions_axioms', absolute=True, min_wins=True)
    generator_not_well_defined_for_search = Attribute('generator_not_well_defined_for_search', absolute=True, min_wins=True)
    generator_count_lifted_grounded = Attribute('generator_count_lifted_grounded')
    generator_orders_grounded = Attribute('generator_orders_grounded', absolute=True)
    generator_orders_grounded_list = Attribute('generator_orders_grounded_list', absolute=True)
    generator_order_grounded_2 = Attribute('generator_order_grounded_2', absolute=True, min_wins=False)
    generator_order_grounded_3 = Attribute('generator_order_grounded_3', absolute=True, min_wins=False)
    generator_order_grounded_4 = Attribute('generator_order_grounded_4', absolute=True, min_wins=False)
    generator_order_grounded_5 = Attribute('generator_order_grounded_5', absolute=True, min_wins=False)
    generator_order_grounded_6 = Attribute('generator_order_grounded_6', absolute=True, min_wins=False)
    generator_order_grounded_7 = Attribute('generator_order_grounded_7', absolute=True, min_wins=False)
    generator_order_grounded_8 = Attribute('generator_order_grounded_8', absolute=True, min_wins=False)
    generator_order_grounded_9 = Attribute('generator_order_grounded_9', absolute=True, min_wins=False)
    time_symmetries1_symmetry_graph = Attribute('time_symmetries1_symmetry_graph', absolute=False, min_wins=True, functions=[geometric_mean])
    time_symmetries2_bliss = Attribute('time_symmetries2_bliss', absolute=False, min_wins=True, functions=[geometric_mean])
    time_symmetries3_translate_automorphisms = Attribute('time_symmetries3_translate_automorphisms', absolute=False, min_wins=True, functions=[geometric_mean])
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    translator_completed = Attribute('translator_completed', absolute=True, min_wins=False)
    timeout = Attribute('timeout', absolute=True, min_wins=True)
    ignore_none_of_those_mapping = Attribute('ignore_none_of_those_mapping', absolute=True, min_wins=True)
    symmetry_graph_size = Attribute('symmetry_graph_size', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, functions=[geometric_mean])

    extra_attributes = [
        generator_count_lifted,
        generator_count_lifted_mapping_objects_predicates,
        generator_orders_lifted,
        generator_orders_lifted_list,
        generator_order_lifted_2,
        generator_order_lifted_3,
        generator_order_lifted_4,
        generator_order_lifted_5,
        generator_order_lifted_6,
        generator_order_lifted_7,
        generator_order_lifted_8,
        generator_order_lifted_9,
        generator_order_lifted_max,
        generator_count_grounded_1_after_grounding,
        generator_count_grounded_2_after_sas_task,
        generator_count_grounded_3_after_filtering_props,
        generator_count_grounded_4_after_reordering_filtering_vars,
        generator_count_grounded,
        generator_count_removed,
        generator_lifted_affecting_actions_axioms,
        generator_lifted_mapping_actions_axioms,
        generator_not_well_defined_for_search,
        generator_count_lifted_grounded,
        generator_orders_grounded,
        generator_orders_grounded_list,
        generator_order_grounded_2,
        generator_order_grounded_3,
        generator_order_grounded_4,
        generator_order_grounded_5,
        generator_order_grounded_6,
        generator_order_grounded_7,
        generator_order_grounded_8,
        generator_order_grounded_9,
        time_symmetries1_symmetry_graph,
        time_symmetries2_bliss,
        time_symmetries3_translate_automorphisms,
        bliss_out_of_memory,
        bliss_out_of_time,
        translator_completed,
        timeout,
        ignore_none_of_those_mapping,
        'removed1_after_grounding',
        'removed2_after_sas_task',
        'removed3_after_filtering_props',
        'removed4_after_reordering_filtering_vars',
        symmetry_graph_size,
        time_symmetries,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries*')

    def compute_removed_count_in_each_step(props):
        count_lifted = props.get('generator_count_lifted', 0)
        count_grounded_1 = props.get('generator_count_grounded_1_after_grounding', 0)
        count_grounded_2 = props.get('generator_count_grounded_2_after_sas_task', 0)
        count_grounded_3 = props.get('generator_count_grounded_3_after_filtering_props', 0)
        count_grounded_4 = props.get('generator_count_grounded_4_after_reordering_filtering_vars', 0)
        props['removed1_after_grounding'] = count_lifted - count_grounded_1
        props['removed2_after_sas_task'] = count_grounded_1 - count_grounded_2
        props['removed3_after_filtering_props'] = count_grounded_2 - count_grounded_3
        props['removed4_after_reordering_filtering_vars'] = count_grounded_3 - count_grounded_4
        return props

    def duplicate_attribute(props):
        props['time_symmetries'] = props.get('translator_time_symmetries0_computing_symmetries', None)
        return props

    algorithm_nicks = [
        'translate',
        'translate-symm-stabinit',
    ]

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=['{}-{}'.format(REVISION, x) for x in algorithm_nicks],filter=[compute_removed_count_in_each_step,duplicate_attribute])

    exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=['{}-{}'.format(REVISION, x) for x in algorithm_nicks],filter=[compute_removed_count_in_each_step,duplicate_attribute],filter_domain=strips_suite),outfile='{}-strips-subset-abs.html'.format(exp.name))

    OLD_REV = 'ac5e5c9486fc'
    # exp.add_fetcher('data/2018-03-21-lifted-stabinit-eval',filter_algorithm=['{}-{}'.format(OLD_REV, x) for x in algorithm_nicks])
    exp.add_fetcher('data/2018-03-21-lifted-stabinit-eval',filter_algorithm=['{}-{}'.format(OLD_REV, x) for x in ['translate', 'translate-stabinit']])

    exp.add_report(
        ComparativeReport(
            # algorithm_pairs=[('{}-{}'.format(OLD_REV, x), '{}-{}'.format(REVISION, x)) for x in algorithm_nicks],
            algorithm_pairs=[
                ('{}-translate'.format(OLD_REV), '{}-translate'.format(REVISION)),
                ('{}-translate-stabinit'.format(OLD_REV), '{}-translate-symm-stabinit'.format(REVISION)),
            ],
            attributes=attributes,
        ),
        outfile=os.path.join(exp.eval_dir, exp.name + '-compare.html'),
    )

    exp.run_steps()

main(revisions=[REVISION])