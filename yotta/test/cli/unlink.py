#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile
import re

# internal modules:
from . import cli
from . import util

class TestCLIUnLink(unittest.TestCase):
    def testUnlinkModule(self):
        pass

    def testUnlinkNonexistentModule(self):
        pass
    
    def testUnlinkNotLinkedModuleGlobally(self):
        pass

    def testUnlinkModuleGlobally(self):
        pass

    def testUnlinkTargetGlobally(self):
        pass

    def testUnlinkNotLinkedTargetGlobally(self):
        pass

    def testUnlinkTarget(self):
        linked_in_target = util.writeTestFiles(util.getNativeTargetDescription(), True)
        test_module = util.writeTestFiles(util.Test_Testing_Trivial_Lib_Dep, True)

        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target'], cwd=linked_in_target)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'link-target', 'test-native-target'], cwd=test_module)
        self.assertEqual(statuscode, 0)
        stdout, stderr, statuscode = cli.run(['-t', 'test-native-target', '--plain', 'build'], cwd=test_module)
        print(stdout+stderr)
        self.assertEqual(statuscode, 0)

        util.rmRf(test_module)
        util.rmRf(linked_in_module)

    def testUnlinkNonexistentTarget(self):
        pass


