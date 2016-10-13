#! /usr/bin/env python

import normalize
import options
import pddl_parser
import symmetries_module

if __name__ == "__main__":
    only_object_symmetries = options.only_object_symmetries
    task = pddl_parser.open()
    normalize.normalize(task)
    task.dump()
    symmetries_module.main(task, only_object_symmetries)

