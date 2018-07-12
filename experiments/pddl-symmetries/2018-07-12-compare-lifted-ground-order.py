#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import suites

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, arithmetic_mean, geometric_mean
from downward.reports import PlanningReport
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport
from downward.reports.scatter import ScatterPlotReport

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

REVISION = 'af5fe90d4c29'

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    # optimal union satisficing, strips only
    suite = ['airport', 'barman-opt11-strips', 'barman-opt14-strips', 'blocks',
    'childsnack-opt14-strips', 'depot', 'driverlog', 'elevators-opt08-strips',
    'elevators-opt11-strips', 'floortile-opt11-strips',
    'floortile-opt14-strips', 'freecell', 'ged-opt14-strips', 'grid',
    'gripper', 'hiking-opt14-strips', 'logistics00', 'logistics98', 'miconic',
    'movie', 'mprime', 'mystery', 'nomystery-opt11-strips',
    'openstacks-opt08-strips', 'openstacks-opt11-strips',
    'openstacks-opt14-strips', 'openstacks-strips', 'parcprinter-08-strips',
    'parcprinter-opt11-strips', 'parking-opt11-strips', 'parking-opt14-strips',
    'pathways-noneg', 'pegsol-08-strips', 'pegsol-opt11-strips',
    'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers',
    'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips',
    'sokoban-opt08-strips', 'sokoban-opt11-strips', 'storage',
    'tetris-opt14-strips', 'tidybot-opt11-strips', 'tidybot-opt14-strips',
    'tpp', 'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips',
    'visitall-opt14-strips', 'woodworking-opt08-strips',
    'woodworking-opt11-strips', 'zenotravel', 'barman-sat11-strips',
    'barman-sat14-strips', 'childsnack-sat14-strips', 'elevators-sat08-strips',
    'elevators-sat11-strips', 'floortile-sat11-strips',
    'floortile-sat14-strips', 'ged-sat14-strips', 'hiking-sat14-strips',
    'nomystery-sat11-strips', 'openstacks-sat08-strips',
    'openstacks-sat11-strips', 'openstacks-sat14-strips',
    'parcprinter-sat11-strips', 'parking-sat11-strips', 'parking-sat14-strips',
    'pegsol-sat11-strips', 'scanalyzer-sat11-strips', 'sokoban-sat08-strips',
    'sokoban-sat11-strips', 'tetris-sat14-strips', 'thoughtful-sat14-strips',
    'tidybot-sat11-strips', 'transport-sat08-strips', 'transport-sat11-strips',
    'transport-sat14-strips', 'visitall-sat11-strips', 'visitall-sat14-strips',
    'woodworking-sat08-strips', 'woodworking-sat11-strips']

    configs = {}

    exp = IssueExperiment(
        revisions=revisions,
    )

    generators_count = Attribute('generators_count', absolute=True, min_wins=False)
    generators_identity_count = Attribute('generators_identity_count', absolute=True, min_wins=False)
    generators_orders = Attribute('generators_orders', absolute=True, min_wins=False)
    symmetry_graph_size = Attribute('symmetry_graph_size', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, functions=[geometric_mean])
    symmetry_group_order = Attribute('symmetry_group_order', absolute=True, min_wins=False)

    extra_attributes = [
        generators_count,
        generators_identity_count,
        generators_orders,
        symmetry_graph_size,
        time_symmetries,
        symmetry_group_order,
    ]
    attributes = exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)

    exp.add_fetcher('data/2018-07-12-lifted-eval')
    exp.add_fetcher('data/2018-07-12-ground-order-eval',merge=True)

    # exp.add_absolute_report_step(attributes=attributes,filter_domain=suite)

    algorithm_pairs=[
        ('{}-translate-symm-stabgoal-stabinit'.format(REVISION), '{}-lmcut-dks-stabgoal-stabinit'.format(REVISION)),
        ('{}-translate-symm-stabinit'.format(REVISION), '{}-lmcut-dks-stabinit'.format(REVISION)),
        ('{}-translate-symm-stabgoal'.format(REVISION), '{}-lmcut-dks-stabgoal'.format(REVISION)),
        ('{}-translate-symm'.format(REVISION), '{}-lmcut-dks'.format(REVISION)),
    ]

    exp.add_report(
        ComparativeReport(
            algorithm_pairs=algorithm_pairs,
            attributes=attributes,
            filter_domain=suite,
        ),
        outfile=os.path.join(exp.eval_dir, exp.name + '-compare.html'),
    )

    class TasksWithDifferentValuesOfAttributeReport(PlanningReport):
        def __init__(self, **kwargs):
            PlanningReport.__init__(self, **kwargs)

        def get_text(self):
            if len(self.attributes) > 1:
                print("please pass exactly one attribute")
                sys.exit(1)

            attribute = self.attributes[0]
            tasks_with_value_for_attribute = set()
            for (domain, task), runs in self.problem_runs.items():
                same_value = True
                the_value = None
                for run in runs:
                    run_value = run.get(attribute, None)
                    if run_value is not None:
                        if the_value is None:
                            the_value = run_value
                        if run_value != the_value:
                            same_value = False
                            break
                if not same_value and the_value is not None:
                    tasks_with_value_for_attribute.add('{}:{}'.format(domain, task))

            formatted_result = []
            for task in sorted(tasks_with_value_for_attribute):
                formatted_result.append("'{}',".format(task))
            return '\n'.join(formatted_result)

    algo_pair = ['{}-translate-symm-stabgoal-stabinit'.format(REVISION), '{}-lmcut-dks-stabgoal-stabinit'.format(REVISION)]
    exp.add_report(
        TasksWithDifferentValuesOfAttributeReport(
            filter_algorithm=algo_pair,
            attributes=[symmetry_group_order],
            filter_domain=suite,
        ),
        outfile=os.path.join(exp.eval_dir, exp.name + '-domains-different-values.txt'),
    )

    # result of above report
    tasks_with_different_symmetry_group_orders_for_full_stabilizing = [
    ]

    if matplotlib:
        # for (algo1, algo2) in algorithm_pairs:
            # exp.add_report(
                # ScatterPlotReport(
                    # filter_algorithm=[algo1, algo2],
                    # attributes=[symmetry_group_order],
                    # get_category=lambda run1, run2: run1["domain"],
                    # filter_domain=suite,
                # ),
                # outfile=os.path.join(exp.eval_dir, 'a' + exp.name + '-scatter-order-%s-%s.png' % (algo1, algo2)),
            # )
        exp.add_report(
            ScatterPlotReport(
                filter_algorithm=algo_pair,
                attributes=[symmetry_group_order],
                get_category=lambda run1, run2: run1["domain"],
                filter=lambda props: "{}:{}".format(props['domain'], props['problem']) in tasks_with_different_symmetry_group_orders_for_full_stabilizing,
            ),
            outfile=os.path.join(exp.eval_dir, 'a' + exp.name + '-scatter-order-%s-%s.png' % (algo_pair[0], algo_pair[1])),
        )


    exp.run_steps()

main(revisions=[])
