#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean

from downward.reports.compare import ComparativeReport

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

def main(revisions=[]):
    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        environment = LocalEnvironment(processes=4)

    configs = {}

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )

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

    REV = '6a3ab5b31169'
    def remove_revision(run):
        algo = run['algorithm']
        algo = algo.replace('{}-'.format(REV), '')
        run['algorithm'] = algo
        return run

    exp.add_fetcher(os.path.expanduser('~/repos/downward/pddl-symmetries/experiments/pddl-symmetries/data/2017-10-10-lifted-stabinit-eval'),filter=[remove_revision])
    exp.add_fetcher(os.path.expanduser('~/repos/downward/pddl-symmetries/experiments/pddl-symmetries/data/2017-10-10-lifted-stabinit-baggy-eval'),filter=[remove_revision])

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
        'translate',
        'translate-stabinit',
        'baggy-translate',
        'baggy-translate-stabinit',
    ],filter=[compute_removed_count_in_each_step])

    exp.add_report(ComparativeReport(attributes=attributes,algorithm_pairs=[
        ('translate', 'baggy-translate'),
        ('translate-stabinit', 'baggy-translate-stabinit'),
    ],filter=[compute_removed_count_in_each_step]),outfile=os.path.join(exp.eval_dir, 'compare-regular-baggy.html'))

    exp.run_steps()

main()
