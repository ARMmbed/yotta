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
        self.assertTrue(test_subcommand.moduleFromDirname('ym/b/ym/c/d', {'b':'b', 'c':'c'}, 'a') == 'c')
        self.assertTrue(test_subcommand.moduleFromDirname('ym/b/q/c/d', {'b':'b', 'c':'c'}, 'a') == 'b')
        self.assertTrue(test_subcommand.moduleFromDirname('z/b/q/c/d', {'b':'b', 'c':'c'}, 'a') == 'a')
        self.assertTrue(test_subcommand.moduleFromDirname('ym/e/d', {'b':'b', 'c':'c'}, 'a') == 'a')
        self.assertTrue(test_subcommand.moduleFromDirname('ym/e/d', {'b':'b', 'c':'c', 'e':'e'}, 'a') == 'e')

    # see also yotta/test/cli/test.py for cli-driven testing


