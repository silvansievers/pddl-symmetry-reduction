#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import numpy

from collections import defaultdict

from downward.experiment import FastDownwardExperiment
from downward.reports import PlanningReport

from lab.reports import Attribute, geometric_mean

class DomainAttributesReport(PlanningReport):
    def __init__(self, aggregation_functions,
                 **kwargs):
        self.sorted_attributes = kwargs['attributes']
        self.aggregation_functions = aggregation_functions
        kwargs.setdefault('format', 'txt')
        PlanningReport.__init__(self, **kwargs)
        assert(len(self.attributes) == len(self.aggregation_functions))
        #assert(len(self.algorithms) == 1)

    def get_text(self):
        """
        We do not need any markup processing or loop over attributes here,
        so the get_text() method is implemented right here.
        """
        domain_algorithm_attribute_to_values = {}
        for (domain, algo), runs in self.domain_algorithm_runs.items():
            for attribute in self.sorted_attributes:
                domain_algorithm_attribute_to_values[(domain, algo, attribute)] = [
                    run.get(attribute, None) for run in runs if run.get(attribute, None) is not None]

        lines = []

        # header lines
        algorithms_line = ['algorithm']
        for algorithm in self.algorithms:
            algorithms_line.append("\\multicolumn{{{}}}{{c}}{{{}}}".format(len(self.sorted_attributes), algorithm))
        lines.append(self.format_line(algorithms_line))

        attributes_line = ['attributes']
        for algorithm in self.algorithms:
            for attribute in self.sorted_attributes:
                attributes_line.append(attribute)
        lines.append(self.format_line(attributes_line))

        #print(len(self.problem_runs))
        #print(len(self.domains.keys()))

        # body lines
        algorithm_attribute_to_values = defaultdict(list)
        for domain in sorted(self.domains.keys()):
            domain_line = ['{}'.format(domain)]
            for algorithm in self.algorithms:
                for index, attribute in enumerate(self.sorted_attributes):
                    values = domain_algorithm_attribute_to_values[(domain, algorithm, attribute)]
                    assert isinstance(values, list)
                    if values and isinstance(values[0], list): # flatten values
                        values = list(itertools.chain.from_iterable(values))
                    if values:
                        aggregated_value = self.aggregation_functions[index](values)
                        if isinstance(aggregated_value, numpy.float64):
                            aggregated_value = float(aggregated_value)
                        domain_line.append(aggregated_value)
                        algorithm_attribute_to_values[(algorithm, attribute)].append(aggregated_value)
            lines.append(self.format_line(domain_line))

        # summary line
        summary_line = ['summary']
        for algorithm in self.algorithms:
            for index, attribute in enumerate(self.sorted_attributes):
                values = algorithm_attribute_to_values[(algorithm, attribute)]
                summary_value = self.aggregation_functions[index](values)
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
                    value = int(value)
            line += '{}'.format(value)
            if index == len(values) - 1:
                line += ' \\\\'
            else:
                line += ' & '
        return line

# optimal union satisficing
suite = [
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

REVISION = '57a726092208'

exp.add_fetcher('data/2017-02-15-lifted-stabinit-eval',filter=[symmetries_or_not,parse_list_of_generator_orders],filter_algorithm=[
    #'{}-translate'.format(REVISION),
    '{}-translate-stabinit'.format(REVISION),
    #'{}-translate-stabinit-noblisslimit'.format(REVISION),
    #'{}-translate-stabinit-ground'.format(REVISION),
    #'{}-translate-stabinit-ground-noneofthose'.format(REVISION),
],filter_domain=suite)

generator_count_lifted = Attribute('generator_count_lifted', absolute=True, min_wins=False)
time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True)
has_symmetries = Attribute('has_symmetries', absolute=True, min_wins=False)
num_tasks = Attribute('num_tasks', absolute=True)

def print_max_order(run):
    generator_order_lifted_max = run.get('generator_order_lifted_max', 0)
    if generator_order_lifted_max >= 17:
        print(generator_order_lifted_max, run.get('domain'), run.get('problem'))
    return run

exp.add_report(DomainAttributesReport(filter_algorithm=[
    '{}-translate-stabinit'.format(REVISION),
],format='tex',
attributes=['num_tasks', 'has_symmetries', generator_count_lifted, generator_count_lifted, time_symmetries, 'orders', 'orders'],
aggregation_functions=[sum, sum, sum, numpy.median, geometric_mean, geometric_mean, numpy.median]))

exp.run_steps()
