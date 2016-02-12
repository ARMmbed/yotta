#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import copy

# internal modules:
from yotta.test.cli import cli
from yotta.test.cli import util

Test_Min_Version_Insufficient = copy.copy(util.Test_Trivial_Lib)
Test_Min_Version_Insufficient['module.json'] = '''{
  "name": "test-trivial-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "dependencies": {
  },
  "yotta": ">9999.9999.9999"
}'''

Test_Min_Version_OK = copy.copy(util.Test_Trivial_Lib)
Test_Min_Version_OK['module.json'] = '''{
  "name": "test-trivial-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "dependencies": {
  },
  "yotta": ">0.0.1 !0.0.2 <999.999.999"
}'''

class TestCLIYottaVersionSpecs(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_yottaVersionCheckTooLowBuilding(self):
        test_dir = util.writeTestFiles(Test_Min_Version_Insufficient)
        stdout, stderr, statuscode = cli.run(['--target', util.nativeTarget(), 'build'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('requires yotta version >', stdout+stderr)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_yottaVersionCheckOKBuilding(self):
        test_dir = util.writeTestFiles(Test_Min_Version_OK)
        stdout, stderr, statuscode = cli.run(['--target', util.nativeTarget(), 'build'], cwd=test_dir)
        if statuscode:
            print stderr
            print stdout
        self.assertEqual(statuscode, 0)
        self.assertNotIn('requires yotta version >', stdout+stderr)
        util.rmRf(test_dir)

    def test_yottaVersionCheckTooLowInstalling(self):
        test_dir = util.writeTestFiles(Test_Min_Version_Insufficient)
        stdout, stderr, statuscode = cli.run(['--target', 'x86-linux-native', 'install'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('requires yotta version >', stdout+stderr)
        util.rmRf(test_dir)

    def test_yottaVersionCheckOKInstalling(self):
        test_dir = util.writeTestFiles(Test_Min_Version_OK)
        stdout, stderr, statuscode = cli.run(['--target', 'x86-linux-native', 'install'], cwd=test_dir)
        if statuscode:
            print stderr
            print stdout
        self.assertEqual(statuscode, 0)
        self.assertNotIn('requires yotta version >', stdout+stderr)
        util.rmRf(test_dir)
