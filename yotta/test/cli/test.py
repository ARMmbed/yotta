#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import os
import tempfile
import copy

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from yotta.lib.detect import systemDefaultTarget
from . import cli


Test_Tests = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "author": "James Crosby <james.crosby@arm.com>",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ]
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
'test-tests/foo.h':'int foo();',
'test/a/bar.c':'#include "test-tests/foo.h"\nint main(){ foo(); return 0; }',
'test/b/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/b/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/c/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/c/b/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/d/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/d/a/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/e/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/e/b/a/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/f/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/f/a/b/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/g/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/g/a/a/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }'
}

Test_Fitler_Pass = copy.copy(Test_Tests)
Test_Fitler_Pass['module.json'] = '''{
  "name": "test-tests",
  "version": "0.0.0",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "scripts": {
    "testReporter": [
      "grep",
      "!"
    ]
  }
}'''

Test_Fitler_Fail = copy.copy(Test_Tests)
Test_Fitler_Fail['module.json'] = '''{
  "name": "test-tests",
  "version": "0.0.0",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "scripts": {
    "testReporter": [
      "grep",
      "string that isnt in the output"
    ]
  }
}'''

Test_Fitler_NotFound = copy.copy(Test_Tests)
Test_Fitler_NotFound['module.json'] = '''{
  "name": "test-tests",
  "version": "0.0.0",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "scripts": {
    "testReporter": [
      "commandthatshouldntexist"
    ]
  }
}'''

def isWindows():
    return os.name == 'nt'

class TestCLITest(unittest.TestCase):
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

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_tests(self):
        test_dir = self.writeTestFiles(Test_Tests, True)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        self.assertIn('test-a passed', output)
        self.assertIn('test-c passed', output)
        self.assertIn('test-d passed', output)
        self.assertIn('test-e passed', output)
        self.assertIn('test-f passed', output)
        self.assertIn('test-g passed', output)
        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_testOutputFilterPassing(self):
        test_dir = self.writeTestFiles(Test_Fitler_Pass, True)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_testOutputFilterFailing(self):
        test_dir = self.writeTestFiles(Test_Fitler_Fail, True)
        stdout, stderr, statuscode = cli.run(['--target', systemDefaultTarget(), 'test'], cwd=test_dir)
        if statuscode == 0:
            print(stdout)
            print(stderr)
        self.assertIn('test-a failed', '%s %s' % (stdout, stderr))
        self.assertIn('test-c failed', '%s %s' % (stdout, stderr))
        self.assertIn('test-d failed', '%s %s' % (stdout, stderr))
        self.assertIn('test-e failed', '%s %s' % (stdout, stderr))
        self.assertIn('test-f failed', '%s %s' % (stdout, stderr))
        self.assertIn('test-g failed', '%s %s' % (stdout, stderr))
        self.assertNotEqual(statuscode, 0)
        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_testOutputFilterNotFound(self):
        test_dir = self.writeTestFiles(Test_Fitler_NotFound, True)
        stdout, stderr, statuscode = cli.run(['--target', systemDefaultTarget(), 'test'], cwd=test_dir)
        if statuscode == 0:
            print(stdout)
            print(stderr)
        self.assertNotEqual(statuscode, 0)
        rmRf(test_dir)

    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return '%s %s' % (stdout, stderr)
