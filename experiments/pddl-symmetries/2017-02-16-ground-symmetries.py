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

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    suite=DEFAULT_OPTIMAL_SUITE
    environment = MaiaEnvironment(priority=0, email="silvan.sievers@unibas.ch")

    if is_test_run():
        suite = ['depot:p01.pddl', 'gripper:prob01.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('lmcut', ['--search', 'astar(lmcut())']),
        IssueConfig('lmcut-dks', ['--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=dks,stabilize_initial_state=true)', '--search', 'astar(lmcut(),symmetries=sym)']),
        IssueConfig('lmcut-oss', ['--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=oss,stabilize_initial_state=true)', '--search', 'astar(lmcut(),symmetries=sym)']),
        IssueConfig('lmcut-dks-liftedsymmetries-stabinit-noneofthose', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--add-none-of-those-mappings', '--bliss-time-limit', '300', '--search-options', '--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=dks,source_of_symmetries=translator)', '--search', "astar(lmcut(), symmetries=sym)"], driver_options=['--translate-time-limit', '30m']),
        IssueConfig('lmcut-oss-liftedsymmetries-stabinit-noneofthose', ['--translate-options', '--compute-symmetries', '--stabilize-initial-state', '--ground-symmetries', '--add-none-of-those-mappings', '--bliss-time-limit', '300', '--search-options', '--symmetries', 'sym=structural_symmetries(time_bound=0,search_symmetries=oss,source_of_symmetries=translator)', '--search', "astar(lmcut(), symmetries=sym)"], driver_options=['--translate-time-limit', '30m']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)
    exp.add_resource('search_symmetries_parser', 'search-symmetries-parser.py', dest='search-symmetries-parser.py')
    exp.add_command('search-symmetries-parser', ['{search_symmetries_parser}'])

    generators_count = Attribute('generators_count', absolute=True, min_wins=False)
    generators_orders = Attribute('generators_orders', absolute=True, min_wins=False)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, functions=[geometric_mean])

    extra_attributes = [
        generators_count,
        generators_orders,
        time_symmetries,
    ]
    attributes = exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)

    def add_time_symmetries(props):
        # add time_symmetries for the "lifted symmetries" configuration
        time_symmetries = props.get('time_symmetries', None)
        if time_symmetries is None:
            time_symmetries = props.get('translator_time_symmetries0_computing_symmetries', None)
        props['time_symmetries'] = time_symmetries
        return props

    exp.add_absolute_report_step(attributes=attributes,filter=[add_time_symmetries])

    exp.run_steps()

main(revisions=['cccfaad9fa04'])
