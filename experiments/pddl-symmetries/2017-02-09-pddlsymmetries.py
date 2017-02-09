#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, MaiaEnvironment
from lab.reports import Attribute

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    suite=DEFAULT_OPTIMAL_SUITE
    environment = MaiaEnvironment(priority=0, email="silvan.sievers@unibas.ch")

    if is_test_run():
        suite = ['depot:p01.pddl', 'gripper:prob01.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m']),
        IssueConfig('translate-allsymmetries-staticinit', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300'], driver_options=['--translate', '--translate-time-limit', '30m']),
        #IssueConfig('translate-objectsymmetries', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300', '--only-object-symmetries'], driver_options=['--translate', '--translate-time-limit', '30m']),
        IssueConfig('translate-allsymmetries-onlyPNEinit', ['--translate-options', '--compute-symmetries', '--only-functions-from-initial-state', '--bliss-time-limit', '300'], driver_options=['--translate', '--translate-time-limit', '30m']),
        IssueConfig('translate-allsymmetries-staticinit-preserve', ['--translate-options', '--compute-symmetries', '--preserve-symmetries-during-grounding', '--keep-unreachable-facts', '--keep-unimportant-variables', '--bliss-time-limit', '300'], driver_options=['--translate', '--translate-time-limit', '30m']),
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
    generator_count_grounded = Attribute('generator_count_grounded', absolute=True, min_wins=False)
    generator_count_removed = Attribute('generator_count_removed', absolute=True, min_wins=True)
    generator_count_affecting_actions_axioms = Attribute('generator_count_affecting_actions_axioms', absolute=True, min_wins=True)
    generator_count_mapping_actions_axioms = Attribute('generator_count_mapping_actions_axioms', absolute=True, min_wins=True)
    generator_count_lifted_grounded = Attribute('generator_count_lifted_grounded')
    generator_orders = Attribute('generator_orders', absolute=True)
    generator_order_2 = Attribute('generator_order_2', absolute=True, min_wins=False)
    generator_order_3 = Attribute('generator_order_3', absolute=True, min_wins=False)
    generator_order_4 = Attribute('generator_order_4', absolute=True, min_wins=False)
    generator_order_5 = Attribute('generator_order_5', absolute=True, min_wins=False)
    generator_order_6 = Attribute('generator_order_6', absolute=True, min_wins=False)
    generator_order_7 = Attribute('generator_order_7', absolute=True, min_wins=False)
    generator_order_8 = Attribute('generator_order_8', absolute=True, min_wins=False)
    generator_order_9 = Attribute('generator_order_9', absolute=True, min_wins=False)
    time_prolog_model = Attribute('time_prolog_model', absolute=False, min_wins=True)
    time_bliss = Attribute('time_bliss', absolute=False, min_wins=True)
    time_translate_automorphisms = Attribute('time_translate_automorphisms', absolute=False, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True)
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    translator_completed = Attribute('translator_completed', absolute=True, min_wins=False)
    timeout = Attribute('timeout', absolute=True, min_wins=True)

    extra_attributes = [
        generator_count_lifted,
        generator_count_lifted_mapping_objects_predicates,
        generator_count_grounded,
        generator_count_removed,
        generator_count_affecting_actions_axioms,
        generator_count_mapping_actions_axioms,
        generator_count_lifted_grounded,
        generator_orders,
        generator_order_2,
        generator_order_3,
        generator_order_4,
        generator_order_5,
        generator_order_6,
        generator_order_7,
        generator_order_8,
        generator_order_9,
        time_prolog_model,
        time_bliss,
        time_translate_automorphisms,
        time_symmetries,
        bliss_out_of_memory,
        bliss_out_of_time,
        translator_completed,
        timeout
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_*')

    def check_completion(props):
        translator_time_done = props.get('translator_time_done', None)
        translator_completed = False
        if translator_time_done is not None:
            translator_completed = True
        props['translator_completed'] = translator_completed
        return props

    exp.add_absolute_report_step(attributes=attributes,filter=[check_completion])

    exp.run_steps()

main(revisions=['8754ab6ebdb4'])
