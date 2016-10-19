#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites
from lab.reports import Attribute, gm

from common_setup import IssueConfig, IssueExperiment
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    suite=suites.suite_all()

    configs = {
        IssueConfig('translate-allsymmetries', ['--translate-options', '--only-find-symmetries', '--bliss-time-limit', '300'], driver_options=['--translate']),
        IssueConfig('translate-objectsymmetries', ['--translate-options', '--only-find-symmetries', '--bliss-time-limit', '300', '--only-object-symmetries'], driver_options=['--translate']),
    }

    exp = IssueExperiment(
        benchmarks_dir=benchmarks_dir,
        suite=suite,
        revisions=revisions,
        configs=configs,
        test_suite=['depot:p01.pddl', 'gripper:prob01.pddl'],
        processes=4,
        email='silvan.sievers@unibas.ch',
    )

    exp.add_resource('symmetries_parser', 'symmetries-parser.py', dest='symmetries-parser.py')
    exp.add_command('symmetries-parser', ['symmetries_parser'])

    generators_count = Attribute('generators_count', absolute=False, min_wins=False)
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    time_bliss = Attribute('time_bliss', absolute=True, min_wins=True)
    time_translate_automorphisms = Attribute('time_translate_automorphisms', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=True, min_wins=True)
    extra_attributes = [
        generators_count,
        bliss_out_of_memory,
        bliss_out_of_time,
        time_bliss,
        time_translate_automorphisms,
        time_symmetries,
    ]
    attributes = [] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    #attributes.append('translator_*')

    exp.add_fetcher(name='parse-again', parsers=['symmetries-parser.py'])
    exp.add_absolute_report_step(attributes=attributes)

    exp()

main(revisions=['85b6eadec1a9'])
