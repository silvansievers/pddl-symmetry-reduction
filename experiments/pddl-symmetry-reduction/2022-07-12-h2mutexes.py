#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import subprocess
import sys

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print('matplotlib not available, scatter plots not available')
    matplotlib = False

OLD_REV = 'd5a3faf0962a'
NEW_REV = '5a1872f2b027654f9f83e58c3704cc966666b135'

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/benchmarks/downward')
    # optimal union satisficing
    suite = [
    'openstacks-sat08-adl', 'miconic-simpleadl', 'barman-sat14-strips',
    'transport-opt11-strips', 'openstacks-sat08-strips', 'logistics98',
    'parking-sat11-strips', 'psr-large', 'rovers', 'floortile-opt14-strips',
    'barman-opt14-strips', 'zenotravel', 'elevators-sat11-strips',
    'nomystery-opt11-strips', 'parcprinter-08-strips', 'tidybot-opt11-strips',
    'cavediving-14-adl', 'pegsol-opt11-strips', 'maintenance-opt14-adl',
    'citycar-opt14-adl', 'pipesworld-notankage', 'woodworking-sat08-strips',
    'woodworking-opt11-strips', 'driverlog', 'gripper', 'visitall-sat11-strips',
    'openstacks', 'hiking-opt14-strips', 'sokoban-opt11-strips',
    'tetris-sat14-strips', 'parcprinter-opt11-strips', 'openstacks-strips',
    'parcprinter-sat11-strips', 'grid', 'sokoban-opt08-strips',
    'elevators-opt08-strips', 'openstacks-sat14-strips', 'barman-sat11-strips',
    'tidybot-sat11-strips', 'mystery', 'visitall-opt14-strips',
    'childsnack-sat14-strips', 'sokoban-sat11-strips', 'trucks',
    'sokoban-sat08-strips', 'barman-opt11-strips', 'childsnack-opt14-strips',
    'parking-opt14-strips', 'openstacks-opt11-strips', 'elevators-sat08-strips',
    'movie', 'tidybot-opt14-strips', 'freecell', 'openstacks-opt14-strips',
    'scanalyzer-sat11-strips', 'ged-opt14-strips', 'pegsol-sat11-strips',
    'transport-opt08-strips', 'mprime', 'floortile-opt11-strips',
    'transport-sat08-strips', 'pegsol-08-strips', 'blocks',
    'floortile-sat11-strips', 'thoughtful-sat14-strips', 'openstacks-opt08-strips',
    'visitall-sat14-strips', 'pipesworld-tankage', 'scanalyzer-opt11-strips',
    'storage', 'maintenance-sat14-adl', 'optical-telegraphs',
    'elevators-opt11-strips', 'miconic', 'logistics00', 'depot',
    'transport-sat11-strips', 'openstacks-opt08-adl', 'psr-small', 'satellite',
    'assembly', 'citycar-sat14-adl', 'schedule', 'miconic-fulladl',
    'pathways', 'tetris-opt14-strips', 'ged-sat14-strips', 'pathways',
    'woodworking-opt08-strips', 'floortile-sat14-strips', 'nomystery-sat11-strips',
    'transport-opt14-strips', 'woodworking-sat11-strips', 'philosophers',
    'trucks-strips', 'hiking-sat14-strips', 'transport-sat14-strips',
    'openstacks-sat11-strips', 'scanalyzer-08-strips', 'visitall-opt11-strips',
    'psr-middle', 'airport', 'parking-opt11-strips', 'tpp', 'parking-sat14-strips']

    strips_suite = ['airport', 'barman-opt11-strips', 'barman-opt14-strips',
    'blocks', 'childsnack-opt14-strips', 'depot', 'driverlog',
    'elevators-opt08-strips', 'elevators-opt11-strips',
    'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell',
    'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips',
    'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery',
    'nomystery-opt11-strips', 'openstacks-opt08-strips',
    'openstacks-opt11-strips', 'openstacks-opt14-strips', 'openstacks-strips',
    'parcprinter-08-strips', 'parcprinter-opt11-strips',
    'parking-opt11-strips', 'parking-opt14-strips', 'pathways',
    'pegsol-08-strips', 'pegsol-opt11-strips', 'pipesworld-notankage',
    'pipesworld-tankage', 'psr-small', 'rovers', 'satellite',
    'scanalyzer-08-strips', 'scanalyzer-opt11-strips', 'sokoban-opt08-strips',
    'sokoban-opt11-strips', 'storage', 'tetris-opt14-strips',
    'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp',
    'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips',
    'visitall-opt14-strips', 'woodworking-opt08-strips',
    'woodworking-opt11-strips', 'zenotravel']

    environment = BaselSlurmEnvironment(
        email="silvan.sievers@unibas.ch",
        partition="infai_2",
        export=[],
        # paths obtained via:
        # module purge
        # module -q load Python/3.7.4-GCCcore-8.3.0
        # module -q load CMake/3.15.3-GCCcore-8.3.0
        # module -q load GCC/8.3.0
        # echo $PATH
        # echo $LD_LIBRARY_PATH
        setup='export PATH=/scicore/soft/apps/CMake/3.15.3-GCCcore-8.3.0/bin:/scicore/soft/apps/cURL/7.66.0-GCCcore-8.3.0/bin:/scicore/soft/apps/Python/3.7.4-GCCcore-8.3.0/bin:/scicore/soft/apps/XZ/5.2.4-GCCcore-8.3.0/bin:/scicore/soft/apps/SQLite/3.29.0-GCCcore-8.3.0/bin:/scicore/soft/apps/Tcl/8.6.9-GCCcore-8.3.0/bin:/scicore/soft/apps/ncurses/6.1-GCCcore-8.3.0/bin:/scicore/soft/apps/bzip2/1.0.8-GCCcore-8.3.0/bin:/scicore/soft/apps/binutils/2.32-GCCcore-8.3.0/bin:/scicore/soft/apps/GCCcore/8.3.0/bin:/infai/sieverss/repos/bin:/infai/sieverss/local:/export/soft/lua_lmod/centos7/lmod/lmod/libexec:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:$PATH\nexport LD_LIBRARY_PATH=/scicore/soft/apps/cURL/7.66.0-GCCcore-8.3.0/lib:/scicore/soft/apps/Python/3.7.4-GCCcore-8.3.0/lib:/scicore/soft/apps/libffi/3.2.1-GCCcore-8.3.0/lib64:/scicore/soft/apps/libffi/3.2.1-GCCcore-8.3.0/lib:/scicore/soft/apps/GMP/6.1.2-GCCcore-8.3.0/lib:/scicore/soft/apps/XZ/5.2.4-GCCcore-8.3.0/lib:/scicore/soft/apps/SQLite/3.29.0-GCCcore-8.3.0/lib:/scicore/soft/apps/Tcl/8.6.9-GCCcore-8.3.0/lib:/scicore/soft/apps/libreadline/8.0-GCCcore-8.3.0/lib:/scicore/soft/apps/ncurses/6.1-GCCcore-8.3.0/lib:/scicore/soft/apps/bzip2/1.0.8-GCCcore-8.3.0/lib:/scicore/soft/apps/binutils/2.32-GCCcore-8.3.0/lib:/scicore/soft/apps/zlib/1.2.11-GCCcore-8.3.0/lib:/scicore/soft/apps/GCCcore/8.3.0/lib64:/scicore/soft/apps/GCCcore/8.3.0/lib')

    if is_test_run():
        suite = suite = [
            'gripper:prob01.pddl',
            # 'depot:p01.pddl',
            'transport-opt08-strips:p01.pddl',
            'pathways:p01.pddl',
            'mystery:prob07.pddl',
            'miconic:s1-0.pddl',
        ]
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate-h2mutexes', ['--translate-options', '--h2-mutexes'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-reduced-h2mutexes-stabinit', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300', '--only-object-symmetries', '--compute-symmetric-object-sets-from-symmetries', '--symmetry-reduced-grounding-for-h2-mutexes','--h2-mutexes', '--do-not-stabilize-goal'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
        IssueConfig('translate-reduced-h2mutexes-expand-stabinit', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300', '--only-object-symmetries', '--compute-symmetric-object-sets-from-symmetries', '--symmetry-reduced-grounding-for-h2-mutexes','--h2-mutexes', '--expand-reduced-h2-mutexes', '--do-not-stabilize-goal'], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3584M']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    exp.add_parser(exp.EXITCODE_PARSER)
    exp.add_parser(exp.TRANSLATOR_PARSER)
    exp.add_parser('symmetries-parser.py')
    exp.add_parser('symm-obj-parser.py')
    exp.add_parser('symmetry-reduction-parser.py')

    num_lifted_generators = Attribute('num_lifted_generators', absolute=True, min_wins=False)
    time_symmetries1_symmetry_graph = Attribute('time_symmetries1_symmetry_graph', absolute=False, min_wins=True, function=geometric_mean)
    time_symmetries2_bliss = Attribute('time_symmetries2_bliss', absolute=False, min_wins=True, function=geometric_mean)
    time_symmetries3_translate = Attribute('time_symmetries3_translate', absolute=False, min_wins=True, function=geometric_mean)
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    symmetry_graph_size = Attribute('symmetry_graph_size', absolute=True, min_wins=True)
    time_symmetries = Attribute('time_symmetries', absolute=False, min_wins=True, function=geometric_mean)
    symmetry_group_order = Attribute('symmetry_group_order', absolute=False, min_wins=False)
    symmetries_only_affect_objects = Attribute('symmetries_only_affect_objects', absolute=True, min_wins=False)
    symmetries_only_affect_predicates = Attribute('symmetries_only_affect_predicates', absolute=True, min_wins=False)
    symmetries_only_affect_functions = Attribute('symmetries_only_affect_functions', absolute=True, min_wins=False)

    num_object_symmetries = Attribute('num_object_symmetries', absolute=True, min_wins=False)
    number_symmetric_object_sets = Attribute('number_symmetric_object_sets', absolute=True, min_wins=False)
    time_symm_obj_sets = Attribute('time_symm_obj_sets', absolute=False, min_wins=True, function=geometric_mean)

    time_bounds_and_subsets = Attribute('time_bounds_and_subsets', absolute=True, min_wins=True)
    time_grounding_program = Attribute('time_grounding_program', absolute=True, min_wins=True)
    time_grounding_model = Attribute('time_grounding_model', absolute=True, min_wins=True)
    time_grounding_expand = Attribute('time_grounding_expand', absolute=True, min_wins=True)
    time_h2mutexes_program = Attribute('time_h2mutexes_program', absolute=True, min_wins=True)
    time_h2mutexes_model = Attribute('time_h2mutexes_model', absolute=True, min_wins=True)
    time_h2mutexes_expand = Attribute('time_h2mutexes_expand', absolute=True, min_wins=True)
    num_used_symmetric_object_sets = Attribute('num_used_symmetric_object_sets', absolute=True, min_wins=False)
    num_reachable_pairs = Attribute('num_reachable_pairs', absolute=True, min_wins=False)
    num_unreachable_pairs = Attribute('num_unreachable_pairs', absolute=True, min_wins=False)
    num_expanded_unreachable_pairs = Attribute('num_expanded_unreachable_pairs', absolute=True, min_wins=False)
    performed_reduction = Attribute('performed_reduction', absolute=True, min_wins=False)

    extra_attributes = [
        num_lifted_generators,
        time_symmetries1_symmetry_graph,
        time_symmetries2_bliss,
        time_symmetries3_translate,
        bliss_out_of_memory,
        bliss_out_of_time,
        symmetry_graph_size,
        time_symmetries,
        symmetry_group_order,
        symmetries_only_affect_objects,
        symmetries_only_affect_predicates,
        symmetries_only_affect_functions,

        num_object_symmetries,
        number_symmetric_object_sets,
        time_symm_obj_sets,

        time_bounds_and_subsets,
        time_grounding_program,
        time_grounding_model,
        time_grounding_expand,
        time_h2mutexes_program,
        time_h2mutexes_model,
        time_h2mutexes_expand,
        num_used_symmetric_object_sets,
        num_reachable_pairs,
        num_unreachable_pairs,
        num_expanded_unreachable_pairs,
        performed_reduction,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries*')

    exp.add_step('build', exp.build)
    exp.add_step('start', exp.start_runs)
    exp.add_fetcher(name='fetch')

    algorithm_nicks = [
        'translate-h2mutexes',
        'translate-reduced-h2mutexes-stabinit',
        'translate-reduced-h2mutexes-expand-stabinit',
    ]

    exp.add_absolute_report_step(
        attributes=attributes,
        filter_algorithm=['{}-{}'.format(NEW_REV, x) for x in algorithm_nicks])

    # data from the zenodo entry of roeger-et-al-icaps2018, file
    # roeger-et-al-icaps2018-data.zip
    old_algorithm_nicks = [
        'translate-h2mutexes',
        'translate-reduced-h2mutexes-nogoal',
        'translate-reduced-h2mutexes-expand-nogoal',
    ]
    exp.add_fetcher(
        'data/2018-03-13-h2mutexes-eval',
        filter_algorithm=['{}-{}'.format(OLD_REV, x) for x in old_algorithm_nicks],
        merge=True)

    algorithm_pairs=[]
    for i in range(len(algorithm_nicks)):
        algorithm_pairs.append((f"{OLD_REV}-{old_algorithm_nicks[i]}", f"{NEW_REV}-{algorithm_nicks[i]}"))
    report_name=f'{exp.name}-compare-against-paper'
    report_file=Path(exp.eval_dir) / f'{report_name}.html'
    exp.add_report(
        ComparativeReport(
            attributes=attributes,
            algorithm_pairs=algorithm_pairs,
        ),
        name=report_name,
        outfile=report_file,
    )
    exp.add_step(
        f'publish-{report_name}', subprocess.call, ['publish', report_file])

    # exp.add_comparison_table_step(revisions=[OLD_REV, NEW_REV], attributes=attributes)

    exp.run_steps()

main(revisions=[NEW_REV])
