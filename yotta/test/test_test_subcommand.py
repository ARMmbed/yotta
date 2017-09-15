#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest

# module to test:
from yotta import test_subcommand
from yotta.lib import paths


class TestTestSubcommandModule(unittest.TestCase):
    def test_moduleFromDirname(self):
        # Fstrings would be handy here
        self.assertEqual(test_subcommand.moduleFromDirname(
            '{m}/b/{m}/c/d'.format(m=paths.BUILT_MODULES_DIR), {'b': 'b', 'c': 'c'}, 'a'),
            'c'
        )
        self.assertEqual(test_subcommand.moduleFromDirname(
            '{m}/b/q/c/d'.format(m=paths.BUILT_MODULES_DIR), {'b': 'b', 'c': 'c'}, 'a'),
            'b'
        )
        self.assertEqual(test_subcommand.moduleFromDirname(
            'z/b/q/c/d'.format(m=paths.BUILT_MODULES_DIR), {'b': 'b', 'c': 'c'}, 'a'),
            'a'
        )
        self.assertEqual(test_subcommand.moduleFromDirname(
            '{m}/e/d'.format(m=paths.BUILT_MODULES_DIR), {'b': 'b', 'c': 'c'}, 'a'),
            'a'
        )
        self.assertEqual(test_subcommand.moduleFromDirname(
            '{m}/e/d'.format(m=paths.BUILT_MODULES_DIR), {'b': 'b', 'c': 'c', 'e': 'e'}, 'a'),
            'e'
        )

        # see also yotta/test/cli/test.py for cli-driven testing
