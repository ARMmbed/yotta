#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import copy

# internal modules:
from yotta.test.cli import cli
from yotta.test.cli import util

Test_Target = "x86-osx-native,*"
Test_Target_Name = 'x86-osx-native'
Test_Target_Old_Version = '0.0.7'

Test_Shrinkwrap = {
'module.json':'''{
  "name": "test-shrinkwrap",
  "version": "0.0.0",
  "description": "Test yotta shrinkwrap",
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
# test-testing-dummy v0.0.1 (a newer version is available from the registry)
'yotta_modules/test-testing-dummy/module.json':'''{
  "name": "test-testing-dummy",
  "version": "0.0.1",
  "description": "Test yotta's compilation of tests.",
  "author": "James Crosby <james.crosby@arm.com>",
  "license": "Apache-2.0"
}
'''
}

Test_Shrinkwrap_Missing_Dependency = {
'module.json':'''{
  "name": "test-shrinkwrap",
  "version": "0.0.0",
  "description": "Test yotta shrinkwrap",
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
}'''
}

Test_Existing_Shrinkwrap_Missing_Dependency = copy.copy(Test_Shrinkwrap_Missing_Dependency)
Test_Existing_Shrinkwrap_Missing_Dependency['yotta-shrinkwrap.json'] = '''
{
  "modules": [
    {
      "version": "0.0.0",
      "name": "test-shrinkwrap"
    },
    {
      "version": "0.0.1",
      "name": "test-testing-dummy"
    }
  ],
  "targets": [
    {
      "version": "%s",
      "name": "%s"
    }
  ]
}''' % (Test_Target_Old_Version, Test_Target_Name)

Test_Existing_Shrinkwrap = copy.copy(Test_Shrinkwrap)
Test_Existing_Shrinkwrap['yotta_targets/inherits-from-test-target/target.json'] = '''{
  "name": "inherits-from-test-target",
  "version": "1.0.0",
  "license": "Apache-2.0",
  "inherits": {
     "%s": "*"
  }
}''' % Test_Target_Name
Test_Existing_Shrinkwrap['yotta-shrinkwrap.json'] = '''
{
  "modules": [
    {
      "version": "0.0.0",
      "name": "test-shrinkwrap"
    },
    {
      "version": "0.0.1",
      "name": "test-testing-dummy"
    }
  ],
  "targets": [
    {
      "version": "%s",
      "name": "%s"
    }
  ]
}''' % (Test_Target_Old_Version, Test_Target_Name)

class TestCLIShrinkwrap(unittest.TestCase):

    def testCreateShrinkwrap(self):
        test_dir = util.writeTestFiles(Test_Shrinkwrap, True)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'shrinkwrap'], cwd=test_dir)
        self.assertEqual(statuscode, 0)
        self.assertTrue(os.path.exists(os.path.join(test_dir, 'yotta-shrinkwrap.json')))

        util.rmRf(test_dir)

    def testMissingDependenciesShrinkwrap(self):
        test_dir = util.writeTestFiles(Test_Shrinkwrap_Missing_Dependency, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'shrinkwrap'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        self.assertFalse(os.path.exists(os.path.join(test_dir, 'yotta-shrinkwrap.json')))
        self.assertIn('is missing', stdout+stderr)
        util.rmRf(test_dir)

    def testInstallWithShrinkwrap(self):
        test_dir = util.writeTestFiles(Test_Existing_Shrinkwrap_Missing_Dependency, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'install'], cwd=test_dir)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'list'], cwd=test_dir)
        self.assertEqual(statuscode, 0)
        # as opposed to 0.0.2 which is the latest
        self.assertIn('test-testing-dummy 0.0.1', stdout+stderr)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'target'], cwd=test_dir)
        self.assertEqual(statuscode, 0)
        self.assertIn('%s %s' % (Test_Target_Name, Test_Target_Old_Version), stdout+stderr)

        util.rmRf(test_dir)

    def testBaseTargetInstallWithShrinkwrap(self):
        test_dir = util.writeTestFiles(Test_Existing_Shrinkwrap, True)
        stdout, stderr, statuscode = cli.run(['-t', 'inherits-from-test-target', '--plain', 'install'], cwd=test_dir)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', 'inherits-from-test-target', '--plain', 'target'], cwd=test_dir)
        self.assertEqual(statuscode, 0)
        self.assertIn('%s %s' % (Test_Target_Name, Test_Target_Old_Version), stdout+stderr)

        util.rmRf(test_dir)

    def testUpdateWithShrinkwrap(self):
        test_dir = util.writeTestFiles(Test_Existing_Shrinkwrap, True)
        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'update'], cwd=test_dir)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', Test_Target, '--plain', 'list'], cwd=test_dir)
        self.assertEqual(statuscode, 0)
        # as opposed to 0.0.2 which is the latest
        self.assertIn('test-testing-dummy 0.0.1', stdout+stderr)

        util.rmRf(test_dir)

