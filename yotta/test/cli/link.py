#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile

# internal modules:
from yotta.lib.folders import globalInstallDirectory

from . import cli
from . import util

Test_Target = 'x86-linux-native'

class TestCLILink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prefix_dir = tempfile.mkdtemp()
        os.environ['YOTTA_PREFIX'] = cls.prefix_dir

    @classmethod
    def tearDownClass(cls):
        util.rmRf(cls.prefix_dir)
        cls.prefix_dir = None

    def testLink(self):
        linked_in_module = util.writeTestFiles(util.Test_Trivial_Lib, True)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'link'], cwd=linked_in_module)
        self.assertEqual(statuscode, 0)
        self.assertTrue(os.path.exists(os.path.join(globalInstallDirectory(), 'test-trivial-lib')))

        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'list'], cwd=test_module)
        self.assertIn('missing', stdout+stderr)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'link', 'test-trivial-lib'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        self.assertNotIn('broken', stdout+stderr)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'list'], cwd=test_module)
        self.assertNotIn('missing', stdout+stderr)

        util.rmRf(test_module)
        util.rmRf(linked_in_module)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on this platform yet")
    def testLinkedBuild(self):
        linked_in_module = util.writeTestFiles(util.Test_Trivial_Lib, True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)

        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link'], cwd=linked_in_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link', 'test-trivial-lib'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'build'], cwd=test_module)
        self.assertEqual(statuscode, 0)

        util.rmRf(test_module)
        util.rmRf(linked_in_module)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on this platform yet")
    def testLinkedReBuild(self):
        # test that changing which module is linked triggers a re-build
        linked_in_module_1 = util.writeTestFiles(util.Test_Trivial_Lib, True)
        linked_in_module_2 = util.writeTestFiles(util.Test_Trivial_Lib, True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)

        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link'], cwd=linked_in_module_1)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link', 'test-trivial-lib'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'build'], cwd=test_module)
        self.assertEqual(statuscode, 0)

        # check that rebuild is no-op
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'build'], cwd=test_module)
        self.assertIn('no work to do', stdout+stderr)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link'], cwd=linked_in_module_2)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'build'], cwd=test_module)
        self.assertNotIn('no work to do', stdout+stderr)
        self.assertEqual(statuscode, 0)

        util.rmRf(test_module)
        util.rmRf(linked_in_module_1)
        util.rmRf(linked_in_module_2)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on this platform yet")
    def testTargetLinkedBuild(self):
        linked_in_target = util.writeTestFiles(util.getNativeTargetDescription(), True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep_Preinstalled, True)

        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target'], cwd=linked_in_target)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target', 'test-native-target'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'build'], cwd=test_module)
        self.assertEqual(statuscode, 0)

        util.rmRf(test_module)
        util.rmRf(linked_in_target)

