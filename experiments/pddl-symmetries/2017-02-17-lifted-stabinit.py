#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, MaiaEnvironment
from lab.reports import Attribute, geometric_mean

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

REVISION = 'd418d67d127b'

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
    environment = MaiaEnvironment(priority=0, email="silvan.sievers@unibas.ch")

    if is_test_run():
        suite = ['depot:p01.pddl', 'gripper:prob01.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m']),
        IssueConfig('translate-stabinit', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--bliss-time-limit', '300', ], driver_options=['--translate', '--translate-time-limit', '30m']),

        IssueConfig('translate-stabinit-ground', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--bliss-time-limit', '300',], driver_options=['--translate', '--translate-time-limit', '30m']),
        IssueConfig('translate-stabinit-ground-noneofthose', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--add-none-of-those-mappings', '--bliss-time-limit', '300',], driver_options=['--translate', '--translate-time-limit', '30m']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)
    exp.add_resource('symmetries_parser', 'symmetries-parser.py', dest='symmetries-parser.py')
    exp.add_command('symmetries-parser', ['{symmetries_parser}'])
    del exp.commands['parse-search']

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
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries*')

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=[
        '{}-translate'.format(REVISION),
        '{}-translate-stabinit'.format(REVISION),
        '{}-translate-stabinit-ground'.format(REVISION),
        '{}-translate-stabinit-ground-noneofthose'.format(REVISION),
    ])

    exp.run_steps()

main(revisions=[REVISION])
