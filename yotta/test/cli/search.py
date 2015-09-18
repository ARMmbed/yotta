#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest

# internal modules:
from . import cli

class TestCLISearch(unittest.TestCase):
    def test_bothModule(self):
        stdout = self.runCheckCommand(['search', 'polyfill'])
        self.assertTrue(stdout.find('compiler-polyfill') != -1)

    def test_bothTarget(self):
        stdout = self.runCheckCommand(['search', 'frdm-k64f'])
        self.assertTrue(stdout.find('frdm-k64f-gcc') != -1)

    def test_both(self):
        stdout = self.runCheckCommand(['search', 'both', 'polyfill'])
        self.assertTrue(stdout.find('compiler-polyfill') != -1)

    def test_modules(self):
        stdout = self.runCheckCommand(['search', 'module', 'polyfill'])
        self.assertTrue(stdout.find('compiler-polyfill') != -1)

    def test_targets(self):
        stdout = self.runCheckCommand(['search', 'target', 'frdm-k64f'])
        self.assertTrue(stdout.find('frdm-k64f-gcc') != -1)

    def test_keywords(self):
        stdout = self.runCheckCommand(['search', 'module', 'polyfill', '-k', 'polyfill'])
        self.assertTrue(stdout.find('compiler-polyfill') != -1)

    def test_limit(self):
        stdout = self.runCheckCommand(['search', 'module', 'compiler-polyfill', '-l', '5', '-k', 'polyfill'])
        self.assertTrue(stdout.find('compiler-polyfill') != -1)

    def runCheckCommand(self, args):
        stdout, stderr, statuscode = cli.run(args)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return stdout or stderr


if __name__ == '__main__':
    unittest.main()



