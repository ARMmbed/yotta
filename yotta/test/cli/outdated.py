#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import os
import tempfile

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from . import cli

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

class TestCLIOutdated(unittest.TestCase):
    def writeTestFiles(self, files, add_space_in_path=False):
        test_dir = tempfile.mkdtemp()
        if add_space_in_path:
            test_dir = test_dir + ' spaces in path'

        for path, contents in files.items():
            path_dir, file_name =  os.path.split(path)
            path_dir = os.path.join(test_dir, path_dir)
            mkDirP(path_dir)
            with open(os.path.join(path_dir, file_name), 'w') as f:
                f.write(contents)
        return test_dir

    def test_outdated(self):
        path = self.writeTestFiles(Test_Outdated, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'outdated'], cwd=path)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('test-testing-dummy', stdout + stderr)

        rmRf(path)

    def test_notOutdated(self):
        path = self.writeTestFiles(Test_Outdated, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'up'], cwd=path)
        self.assertEqual(statuscode, 0)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'outdated'], cwd=path)
        self.assertEqual(statuscode, 0)
        self.assertNotIn('test-testing-dummy', stdout + stderr)

        rmRf(path)
