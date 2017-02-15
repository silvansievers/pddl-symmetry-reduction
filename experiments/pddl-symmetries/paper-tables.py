#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import numpy

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
        for domain in sorted(self.domains.keys()):
            domain_line = ['{}'.format(domain)]
            for algorithm in self.algorithms:
                for index, attribute in enumerate(self.sorted_attributes):
                    values = domain_algorithm_attribute_to_values[(domain, algorithm, attribute)]
                    assert isinstance(values, list)
                    if values and isinstance(values[0], list): # flatten values
                        values = list(itertools.chain(*values))
                    aggregated_value = self.aggregation_functions[index](values)
                    if isinstance(aggregated_value, numpy.float64):
                        aggregated_value = float(aggregated_value)
                    if isinstance(aggregated_value, float):
                        if aggregated_value != int(aggregated_value):
                            aggregated_value = '{:.1f}'.format(aggregated_value)
                        else:
                            aggregated_value = int(aggregated_value)
                    domain_line.append(aggregated_value)
            lines.append(self.format_line(domain_line))

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
            line += '{}'.format(value)
            if index == len(values) - 1:
                line += ' \\\\'
            else:
                line += ' & '
        return line

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
        string_order_list = generator_orders_lifted_list[0].split(',')
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
])

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
attributes=['num_tasks', 'has_symmetries', time_symmetries, generator_count_lifted, generator_count_lifted, 'orders', 'orders'],
aggregation_functions=[sum, sum, geometric_mean, sum, numpy.median, geometric_mean, numpy.median]))

exp.run_steps()
