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
from yotta.lib.detect import systemDefaultTarget
from . import cli

Test_Complex = {
'module.json': '''{
  "name": "test-testdep-a",
  "version": "0.0.2",
  "description": "Module to test test-dependencies",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
    "test-testdep-b": "*",
    "test-testdep-c": "*",
    "test-testdep-d": "*"
  },
  "testDependencies": {
    "test-testdep-e": "*"
  }
}
''',

'source/a.c': '''
#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"

int a(){
    return 1 + b() + c() + d(); // 35
}
''',

'source/a.c': '''
#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"

int a(){
    return 1 + b() + c() + d(); // 35
}
''',

'a/a.h':'''
#ifndef __A_H__
#define __A_H__
int a();
#endif
''',

'test/check.c': '''
#include <stdio.h>

#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"
#include "e/e.h"


int main(){
    int result = a() + b() + c() + d() + e();
    printf("%d\\n", result);
    return !(result == 86);
}
'''
}


Test_Trivial_Lib = {
'module.json':'''{
  "name": "test-trivial-lib",
  "version": "0.0.2",
  "description": "Module to test trivial lib compilation",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
  }
}''',

'test-trivial-lib/lib.h': '''
int foo();
''',

'source/lib.c':'''
#include "test-trivial-lib/lib.h"

int foo(){
    return 7;
}
'''
}

Test_Trivial_Exe = {
'module.json':'''{
  "name": "test-trivial-exe",
  "version": "0.0.2",
  "description": "Module to test trivial exe compilation",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
  }
}''',

'source/lib.c':'''
int main(){
    return 0;
}
'''
}

Test_Tests = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "keywords": [],
  "author": "James Crosby <james.crosby@arm.com>",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {},
  "targetDependencies": {}
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

def isWindows():
    # can't run tests that hit github without an authn token
    return os.name == 'nt'


class TestCLIBuild(unittest.TestCase):
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
    def test_buildTrivialLib(self):
        test_dir = self.writeTestFiles(Test_Trivial_Lib)

        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)

        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_buildTrivialExe(self):
        test_dir = self.writeTestFiles(Test_Trivial_Exe)

        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)

        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_buildComplex(self):
        test_dir = self.writeTestFiles(Test_Complex)

        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)

        rmRf(test_dir)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_buildComplexSpaceInPath(self):
        test_dir = self.writeTestFiles(Test_Complex, True)

        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)

        rmRf(test_dir)
    
    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_buildTests(self):
        test_dir = self.writeTestFiles(Test_Tests, True)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        self.assertIn('test-a', stdout)
        self.assertIn('test-c', stdout)
        self.assertIn('test-d', stdout)
        self.assertIn('test-e', stdout)
        self.assertIn('test-f', stdout)
        self.assertIn('test-g', stdout)
        rmRf(test_dir)


    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return stdout or stderr
