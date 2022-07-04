#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('num_object_symmetries', 'Number of transpositions: (\d+)', required=False, type=int)
parser.add_pattern('number_symmetric_object_sets', 'Number of non-trivial symmetric object sets: (\d+)', required=False, type=int)

def duplicate_attribute(content, props):
    from_sym = props.get('translator_time_computing_object_symmetries_from_symmetries', None)
    directly = props.get('translator_time_computing_object_symmetries_directly', None)
    if from_sym is not None or directly is not None:
        assert(from_sym is None or directly is None)
        if from_sym is not None:
            props['time_symm_obj_sets'] = from_sym
        if directly is not None:
            props['time_symm_obj_sets'] = directly
    # set default values
    props['num_object_symmetries'] = props.get('num_object_symmetries', 0)
    props['number_symmetric_object_sets'] = props.get('number_symmetric_object_sets', 0)

parser.add_function(duplicate_attribute)

parser.parse()
