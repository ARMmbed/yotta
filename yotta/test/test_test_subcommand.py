#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest


# module to test:
from yotta import test_subcommand

class TestTestSubcommandModule(unittest.TestCase):
    def test_moduleFromDirname(self):
        self.assertEqual(test_subcommand.moduleFromDirname('modules/b/modules/c/d', {'b':'b', 'c':'c'}, 'a') , 'c')
        self.assertEqual(test_subcommand.moduleFromDirname('modules/b/q/c/d', {'b':'b', 'c':'c'}, 'a') , 'b')
        self.assertEqual(test_subcommand.moduleFromDirname('z/b/q/c/d', {'b':'b', 'c':'c'}, 'a') , 'a')
        self.assertEqual(test_subcommand.moduleFromDirname('modules/e/d', {'b':'b', 'c':'c'}, 'a') , 'a')
        self.assertEqual(test_subcommand.moduleFromDirname('modules/e/d', {'b':'b', 'c':'c', 'e':'e'}, 'a') , 'e')

    # see also yotta/test/cli/test.py for cli-driven testing


