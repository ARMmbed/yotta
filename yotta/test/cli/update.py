#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest

# internal modules:
from . import cli
from . import util

Test_Outdated = {
'module.json':'''{
  "name": "test-outdated",
  "version": "0.0.0",
  "description": "Test yotta outdated",
  "author": "James Crosby <james.crosby@arm.com>",
  "license": "Apache-2.0",
  "dependencies":{
    "test-testing-dummy": "*"
  }
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
# test-testing-dummy v0.0.1 (a newer version is available from the registry,
# and will be installed by yt up)
'yotta_modules/test-testing-dummy/module.json':'''{
  "name": "test-testing-dummy",
  "version": "0.0.1",
  "description": "Test yotta's compilation of tests.",
  "author": "James Crosby <james.crosby@arm.com>",
  "license": "Apache-2.0"
}
'''
}

class TestCLIUpdate(unittest.TestCase):
    def test_update(self):
        path = util.writeTestFiles(Test_Outdated, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'update'], cwd=path)
        self.assertEqual(statuscode, 0)
        self.assertIn('download test-testing-dummy', stdout + stderr)

        util.rmRf(path)

    def test_updateExplicit(self):
        path = util.writeTestFiles(Test_Outdated, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'update', 'test-testing-dummy'], cwd=path)
        self.assertEqual(statuscode, 0)
        self.assertIn('download test-testing-dummy', stdout + stderr)

        util.rmRf(path)

    def test_updateNothing(self):
        path = util.writeTestFiles(Test_Outdated, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'up'], cwd=path)
        self.assertEqual(statuscode, 0)
        self.assertIn('download test-testing-dummy', stdout + stderr)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'up'], cwd=path)
        self.assertEqual(statuscode, 0)
        self.assertNotIn('download test-testing-dummy', stdout + stderr)

        util.rmRf(path)
