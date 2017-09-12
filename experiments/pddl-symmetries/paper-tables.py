#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import numpy
import os

from collections import defaultdict

from downward.experiment import FastDownwardExperiment
from downward.reports import PlanningReport
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport

from lab.reports import Attribute, geometric_mean

class DomainAttributesReport(PlanningReport):
    def __init__(self, attribute_aggregation_pairs,
                 **kwargs):
        self.attribute_aggregation_pairs = attribute_aggregation_pairs
        kwargs.setdefault('format', 'txt')
        PlanningReport.__init__(self, **kwargs)

    def get_text(self):
        """
        We do not need any markup processing or loop over attributes here,
        so the get_text() method is implemented right here.
        """
        attributes = set()
        for attribute, aggregation in self.attribute_aggregation_pairs:
            attributes.add(attribute)
        domain_algorithm_attribute_to_values = {}
        for (domain, algo), runs in self.domain_algorithm_runs.items():
            for attribute in attributes:
                domain_algorithm_attribute_to_values[(domain, algo, attribute)] = [
                    run.get(attribute, None) for run in runs if run.get(attribute, None) is not None]

        lines = []

        # header lines
        algorithms_line = ['algorithm']
        for algorithm in self.algorithms:
            algorithms_line.append("\\multicolumn{{{}}}{{c}}{{{}}}".format(len(self.attribute_aggregation_pairs), algorithm))
        lines.append(self.format_line(algorithms_line))

        attributes_line = ['attributes']
        for algorithm in self.algorithms:
            for attribute, aggregation in self.attribute_aggregation_pairs:
                attributes_line.append(attribute)
        lines.append(self.format_line(attributes_line))

        # body lines
        algorithm_attribute_aggregation_to_values = defaultdict(list)
        for domain in sorted(self.domains.keys()):
            domain_line = ['\\textsc{{{}}}'.format(domain)]
            for algorithm in self.algorithms:
                for attribute, aggregation in self.attribute_aggregation_pairs:
                    values = domain_algorithm_attribute_to_values[(domain, algorithm, attribute)]
                    assert isinstance(values, list)
                    if values and isinstance(values[0], list): # flatten values
                        values = list(itertools.chain.from_iterable(values))
                    if values:
                        aggregated_value = aggregation(values)
                        if isinstance(aggregated_value, numpy.float64):
                            aggregated_value = float(aggregated_value)
                        algorithm_attribute_aggregation_to_values[(algorithm, attribute, aggregation)].append(aggregated_value)
                    else:
                        # No values for the attribute, hene no aggregated value
                        # we write an empty table cell, i.e. '', into the domain
                        # line. Note that we don't want to store this value in
                        # algorithm_attribute_aggregation_to_values, to avoid failing
                        # aggregation functions.
                        aggregated_value = ''
                    domain_line.append(aggregated_value)
            lines.append(self.format_line(domain_line))

        # summary line
        summary_line = ['summary']
        for algorithm in self.algorithms:
            for attribute, aggregation in self.attribute_aggregation_pairs:
                values = algorithm_attribute_aggregation_to_values[(algorithm, attribute, aggregation)]
                if values:
                    summary_value = aggregation(values)
                else:
                    summary_value = None
                summary_line.append(summary_value)
        lines.append(self.format_line(summary_line))

        return '\n'.join(lines)

    def format_line(self, values, min_wins=None):
        if min_wins is not None:
            min_value = float('inf')
            max_value = 0
            for index, value in enumerate(values):
                if value < min_value:
                    min_value = value
                if value > max_value:
                    max_value = value

            for index, value in enumerate(values):
                if min_wins and value == min_value:
                    values[index] = '\\textbf{{{}}}'.format(values[index])
                if not min_wins and value == max_value:
                    values[index] = '\\textbf{{{}}}'.format(values[index])

        line = ''
        for index, value in enumerate(values):
            if isinstance(value, float):
                if value != int(value):
                    value = '{:.1f}'.format(value)
                else:
                    value = str(int(value))
            value = str(value)
            if value.endswith('.0'):
                value = value.replace('.0', '')
            if value == '':
                value = '-'
            line += '{}'.format(value)
            if index == len(values) - 1:
                line += ' \\\\'
            else:
                line += ' & '
        return line

# optimal union satisficing
suite_all_opt_sat = [
'airport',
'assembly',
'barman-opt11-strips',
'barman-opt14-strips',
'barman-sat11-strips',
'barman-sat14-strips',
'blocks',
'cavediving-14-adl',
'childsnack-opt14-strips',
'childsnack-sat14-strips',
'citycar-opt14-adl',
'citycar-sat14-adl',
'depot',
'driverlog',
'elevators-opt08-strips',
'elevators-opt11-strips',
'elevators-sat08-strips',
'elevators-sat11-strips',
'floortile-opt11-strips',
'floortile-opt14-strips',
'floortile-sat11-strips',
'floortile-sat14-strips',
'freecell',
'ged-opt14-strips',
'ged-sat14-strips',
'grid',
'gripper',
'hiking-opt14-strips',
'hiking-sat14-strips',
'logistics00',
'logistics98',
'maintenance-opt14-adl',
'maintenance-sat14-adl',
'miconic',
'miconic-fulladl',
'miconic-simpleadl',
'movie',
'mprime',
'mystery',
'nomystery-opt11-strips',
'nomystery-sat11-strips',
'openstacks',
'openstacks-opt08-adl',
'openstacks-opt08-strips',
'openstacks-opt11-strips',
'openstacks-opt14-strips',
'openstacks-sat08-adl',
'openstacks-sat08-strips',
'openstacks-sat11-strips',
'openstacks-sat14-strips',
'openstacks-strips',
'optical-telegraphs',
'parcprinter-08-strips',
'parcprinter-opt11-strips',
'parcprinter-sat11-strips',
'parking-opt11-strips',
'parking-opt14-strips',
'parking-sat11-strips',
'parking-sat14-strips',
'pathways',
'pathways-noneg',
'pegsol-08-strips',
'pegsol-opt11-strips',
'pegsol-sat11-strips',
'philosophers',
'pipesworld-notankage',
'pipesworld-tankage',
'psr-large',
'psr-middle',
'psr-small',
'rovers',
'satellite',
'scanalyzer-08-strips',
'scanalyzer-opt11-strips',
'scanalyzer-sat11-strips',
'schedule',
'sokoban-opt08-strips',
'sokoban-opt11-strips',
'sokoban-sat08-strips',
'sokoban-sat11-strips',
'storage',
'tetris-opt14-strips',
'tetris-sat14-strips',
'thoughtful-sat14-strips',
'tidybot-opt11-strips',
'tidybot-opt14-strips',
'tidybot-sat11-strips',
'tpp',
'transport-opt08-strips',
'transport-opt11-strips',
'transport-opt14-strips',
'transport-sat08-strips',
'transport-sat11-strips',
'transport-sat14-strips',
'trucks',
'trucks-strips',
'visitall-opt11-strips',
'visitall-opt14-strips',
'visitall-sat11-strips',
'visitall-sat14-strips',
'woodworking-opt08-strips',
'woodworking-opt11-strips',
'woodworking-sat08-strips',
'woodworking-sat11-strips',
'zenotravel',
]
duplicates = [
'barman-opt11-strips',
'barman-sat11-strips',
'elevators-opt08-strips',
'elevators-sat08-strips',
'floortile-opt11-strips',
'floortile-sat11-strips',
'openstacks',
'openstacks-opt08-strips',
'openstacks-opt11-strips',
'openstacks-sat08-strips',
'openstacks-sat11-strips',
'openstacks-strips',
'parcprinter-08-strips',
'parking-opt11-strips',
'parking-sat11-strips',
'pegsol-08-strips',
'scanalyzer-08-strips',
'sokoban-opt08-strips',
'sokoban-sat08-strips',
'tidybot-opt11-strips',
'transport-opt08-strips',
'transport-opt11-strips',
'transport-sat08-strips',
'transport-sat11-strips',
'visitall-opt11-strips',
'visitall-sat11-strips',
'woodworking-opt08-strips',
'woodworking-sat08-strips',
]
suite = [domain for domain in suite_all_opt_sat if domain not in duplicates]
#suite = suite_all_opt_sat

def symmetries_or_not(props):
    generator_count_lifted = props.get('generator_count_lifted', 0)
    props['num_tasks'] = 1
    has_symmetries = False
    if generator_count_lifted > 0:
        has_symmetries = 1
    props['has_symmetries'] = has_symmetries
    return props

def parse_list_of_generator_orders(props):
    generator_orders_lifted_list = props.get('generator_orders_lifted_list', [])
    orders = []
    if generator_orders_lifted_list:
        assert len(generator_orders_lifted_list) == 1
        string_order_list = generator_orders_lifted_list[0]
        if string_order_list != '':
            string_order_list = string_order_list.split(',')
            if string_order_list:
                orders = [int(string_order) for string_order in string_order_list]
    props['orders'] = orders
    return props

exp = FastDownwardExperiment()

REV_REG = 'df0a8bea28c7'
REV_BAG = '10e2e6a48a8b'

def rename_revision(run):
    algo = run['algorithm']
    algo = algo.replace('{}-'.format(REV_REG), 'regular-')
    algo = algo.replace('{}-'.format(REV_BAG), 'baggy-')
    run['algorithm'] = algo
    return run

exp.add_fetcher(os.path.expanduser('~/repos/downward/pddl-symmetries/experiments/pddl-symmetries/data/2017-08-16-lifted-stabinit-eval'),filter=[symmetries_or_not,parse_list_of_generator_orders,rename_revision],filter_domain=suite)
exp.add_fetcher(os.path.expanduser('~/repos/downward/pddl-symmetries/experiments/pddl-symmetries/data/2017-09-11-lifted-stabinit-rerun-scicore-eval'),filter=[symmetries_or_not,parse_list_of_generator_orders,rename_revision],filter_domain=suite)

num_tasks = Attribute('num_tasks', absolute=True)
has_symmetries = Attribute('has_symmetries', absolute=True, min_wins=False)
generator_count_lifted_sum = Attribute('generator_count_lifted', absolute=True, min_wins=False, functions=[sum])
generator_count_lifted_gm = Attribute('generator_count_lifted', absolute=True, min_wins=False, functions=[numpy.median])
translator_time_symmetries0_computing_symmetries = Attribute('translator_time_symmetries0_computing_symmetries', absolute=False, min_wins=True, functions=[geometric_mean])
#orders_gm = Attribute('orders', absolute=True, min_wins=False, functions=[geometric_mean])
#orders_mean = Attribute('orders', absolute=True, min_wins=False, functions=[numpy.median])

def print_stuff(run):
    translator_time_symmetries0_computing_symmetries = run.get('translator_time_symmetries0_computing_symmetries', None)
    if translator_time_symmetries0_computing_symmetries is not None and translator_time_symmetries0_computing_symmetries >= 2:
        print("time_symmetries", translator_time_symmetries0_computing_symmetries, run.get('domain'), run.get('problem'))
    return run

exp.add_report(AbsoluteReport(attributes=[generator_count_lifted_sum]))

exp.add_report(
    DomainAttributesReport(
        filter_algorithm=[
            'regular-translate-stabinit',
        ],
        format='tex',
        attribute_aggregation_pairs=[
            ('num_tasks', sum),
            ('has_symmetries', sum),
            ('generator_count_lifted', sum),
            ('generator_count_lifted', numpy.median),
            ('translator_time_symmetries0_computing_symmetries', geometric_mean),
            ('orders', geometric_mean),
            ('orders', numpy.median),
        ],
        #filter=[print_stuff],
        ),
        outfile=os.path.join(exp.eval_dir, 'regular'),
    )

exp.add_report(
    DomainAttributesReport(
        filter_algorithm=[
            'baggy-translate-stabinit',
        ],
        format='tex',
        attribute_aggregation_pairs=[
            ('num_tasks', sum),
            ('has_symmetries', sum),
            ('generator_count_lifted', sum),
            ('generator_count_lifted', numpy.median),
            ('translator_time_symmetries0_computing_symmetries', geometric_mean),
            ('orders', geometric_mean),
            ('orders', numpy.median),
        ],
        #filter=[print_stuff],
        ),
        outfile=os.path.join(exp.eval_dir, 'baggy'),
    )

exp.add_report(
    ComparativeReport(
        attributes=[num_tasks, has_symmetries],
        algorithm_pairs=[
            #('regular-translate', 'baggy-translate'),
            ('regular-translate-stabinit', 'baggy-translate-stabinit'),
        ],
        format='tex',
        ),
    outfile=os.path.join(exp.eval_dir, 'compare-regular-baggy.tex')
)

exp.run_steps()
