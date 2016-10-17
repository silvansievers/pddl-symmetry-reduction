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
        IssueConfig('translate', [], driver_options=['--translate']),
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

    time_prolog_model = Attribute('time_prolog_model', absolute=True, min_wins=True)
    extra_attributes = [
        time_prolog_model,
    ]
    attributes = [] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_*')

    exp.add_absolute_report_step(attributes=attributes)

    exp()

main(revisions=['572f481e6ebb'])
