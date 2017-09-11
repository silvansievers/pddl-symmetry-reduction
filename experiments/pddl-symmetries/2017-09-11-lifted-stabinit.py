#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

REVISION = '10e2e6a48a8b'

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    # optimal union satisficing
    suite = [
    'reformulated-openstacks-sat08-adl',
    'reformulated-miconic-simpleadl',
    'reformulated-barman-sat14-strips',
    'reformulated-transport-opt11-strips',
    'reformulated-openstacks-sat08-strips',
    'reformulated-logistics98',
    'reformulated-parking-sat11-strips',
    'reformulated-psr-large',
    'reformulated-rovers',
    'reformulated-floortile-opt14-strips',
    'reformulated-barman-opt14-strips',
    'reformulated-zenotravel',
    'reformulated-elevators-sat11-strips',
    'reformulated-nomystery-opt11-strips',
    'reformulated-parcprinter-08-strips',
    'reformulated-tidybot-opt11-strips',
    'reformulated-cavediving-14-adl',
    'reformulated-pegsol-opt11-strips',
    'reformulated-maintenance-opt14-adl',
    'reformulated-citycar-opt14-adl',
    'reformulated-pipesworld-notankage',
    'reformulated-woodworking-sat08-strips',
    'reformulated-woodworking-opt11-strips',
    'reformulated-driverlog',
    'reformulated-gripper',
    'reformulated-visitall-sat11-strips',
    'reformulated-openstacks',
    'reformulated-hiking-opt14-strips',
    'reformulated-sokoban-opt11-strips',
    'reformulated-tetris-sat14-strips',
    'reformulated-parcprinter-opt11-strips',
    'reformulated-openstacks-strips',
    'reformulated-parcprinter-sat11-strips',
    'reformulated-grid',
    'reformulated-sokoban-opt08-strips',
    'reformulated-elevators-opt08-strips',
    'reformulated-openstacks-sat14-strips',
    'reformulated-barman-sat11-strips',
    'reformulated-tidybot-sat11-strips',
    'reformulated-mystery',
    'reformulated-visitall-opt14-strips',
    'reformulated-childsnack-sat14-strips',
    'reformulated-sokoban-sat11-strips',
    'reformulated-trucks',
    'reformulated-sokoban-sat08-strips',
    'reformulated-barman-opt11-strips',
    'reformulated-childsnack-opt14-strips',
    'reformulated-parking-opt14-strips',
    'reformulated-openstacks-opt11-strips',
    'reformulated-elevators-sat08-strips',
    'reformulated-movie',
    'reformulated-tidybot-opt14-strips',
    'reformulated-freecell',
    'reformulated-openstacks-opt14-strips',
    'reformulated-scanalyzer-sat11-strips',
    'reformulated-ged-opt14-strips',
    'reformulated-pegsol-sat11-strips',
    'reformulated-transport-opt08-strips',
    'reformulated-mprime',
    'reformulated-floortile-opt11-strips',
    'reformulated-transport-sat08-strips',
    'reformulated-pegsol-08-strips',
    'reformulated-blocks',
    'reformulated-floortile-sat11-strips',
    'reformulated-thoughtful-sat14-strips',
    'reformulated-openstacks-opt08-strips',
    'reformulated-visitall-sat14-strips',
    'reformulated-pipesworld-tankage',
    'reformulated-scanalyzer-opt11-strips',
    'reformulated-storage',
    'reformulated-maintenance-sat14-adl',
    'reformulated-optical-telegraphs',
    'reformulated-elevators-opt11-strips',
    'reformulated-miconic',
    'reformulated-logistics00',
    'reformulated-depot',
    'reformulated-transport-sat11-strips',
    'reformulated-openstacks-opt08-adl',
    'reformulated-psr-small',
    'reformulated-satellite',
    'reformulated-assembly',
    'reformulated-citycar-sat14-adl',
    'reformulated-schedule',
    'reformulated-miconic-fulladl',
    'reformulated-pathways-noneg',
    'reformulated-tetris-opt14-strips',
    'reformulated-ged-sat14-strips',
    'reformulated-pathways',
    'reformulated-woodworking-opt08-strips',
    'reformulated-floortile-sat14-strips',
    'reformulated-nomystery-sat11-strips',
    'reformulated-transport-opt14-strips',
    'reformulated-woodworking-sat11-strips',
    'reformulated-philosophers',
    'reformulated-trucks-strips',
    'reformulated-hiking-sat14-strips',
    'reformulated-transport-sat14-strips',
    'reformulated-openstacks-sat11-strips',
    'reformulated-scanalyzer-08-strips',
    'reformulated-visitall-opt11-strips',
    'reformulated-psr-middle',
    'reformulated-airport',
    'reformulated-parking-opt11-strips',
    'reformulated-tpp',
    'reformulated-parking-sat14-strips']
    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH", "DOWNWARD_BENCHMARKS"])

    if is_test_run():
        suite = ['reformulated-gripper']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),
        IssueConfig('translate-stabinit', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--bliss-time-limit', '300', ], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),

        #IssueConfig('translate-stabinit-ground', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--bliss-time-limit', '300',], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),
        #IssueConfig('translate-stabinit-ground-noneofthose', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--add-none-of-those-mappings', '--bliss-time-limit', '300',], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '2G']),
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
    for run in exp.runs:
        del run.commands['compress-output-sas']

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
        'removed1_after_grounding',
        'removed2_after_sas_task',
        'removed3_after_filtering_props',
        'removed4_after_reordering_filtering_vars',
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

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=[
        '{}-translate'.format(REVISION),
        '{}-translate-stabinit'.format(REVISION),
        #'{}-translate-stabinit-ground'.format(REVISION),
        #'{}-translate-stabinit-ground-noneofthose'.format(REVISION),
    ],filter=[compute_removed_count_in_each_step])

    exp.run_steps()

main(revisions=[REVISION])
