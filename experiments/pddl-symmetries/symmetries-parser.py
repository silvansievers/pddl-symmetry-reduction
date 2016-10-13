#! /usr/bin/env python

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generators_count', 'Found (\d+) generators', required=False, type=int)

parser.parse()
