#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import tempfile
import os

# internal modules:
from . import cli
from . import util

Test_Target = 'x86-linux-native'

class TestCLIUnLink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prefix_dir = tempfile.mkdtemp()
        os.environ['YOTTA_PREFIX'] = cls.prefix_dir

    @classmethod
    def tearDownClass(cls):
        util.rmRf(cls.prefix_dir)
        cls.prefix_dir = None

    def testUnlinkNonexistentModule(self):
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink', 'doesnotexist'], cwd=test_module)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_module)

    def testUnlinkNonexistentTarget(self):
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink-target', 'doesnotexist'], cwd=test_module)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_module)

    def testUnlinkNotLinkedModuleGlobally(self):
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink'], cwd=test_module)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_module)

    def testUnlinkNotLinkedTargetGlobally(self):
        test_target = util.writeTestFiles(util.getNativeTargetDescription(), True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink'], cwd=test_target)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_target)

    def testUnlinkModuleGlobally(self):
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'link'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        util.rmRf(test_module)

    def testUnlinkTargetGlobally(self):
        test_target = util.writeTestFiles(util.getNativeTargetDescription(), True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'link-target'], cwd=test_target)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'unlink-target'], cwd=test_target)
        self.assertEqual(statuscode, 0)
        util.rmRf(test_target)

    def testUnlinkModule(self):
        linked_in_module = util.writeTestFiles(util.Test_Trivial_Lib, True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)

        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link'], cwd=linked_in_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'link', 'test-trivial-lib'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        self.assertTrue(os.path.exists(os.path.join(test_module, 'yotta_modules', 'test-trivial-lib')))
        stdout, stderr, statuscode = cli.run(['-t', util.nativeTarget(), '--plain', 'unlink', 'test-trivial-lib'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        self.assertTrue(not os.path.exists(os.path.join(test_module, 'yotta_modules', 'test-trivial-lib')))

        util.rmRf(test_module)
        util.rmRf(linked_in_module)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on this platform yet")
    def testUnlinkTarget(self):
        linked_in_target = util.writeTestFiles(util.getNativeTargetDescription(), True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep_Preinstalled, True)

        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target'], cwd=linked_in_target)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target', 'test-native-target'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        self.assertTrue(os.path.exists(os.path.join(test_module, 'yotta_targets', 'test-native-target')))
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'unlink-target', 'test-native-target'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        self.assertTrue(not os.path.exists(os.path.join(test_module, 'yotta_targets', 'test-native-target')))

        util.rmRf(test_module)
        util.rmRf(linked_in_target)


