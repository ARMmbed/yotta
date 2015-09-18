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
from yotta.lib import component
from .cli import cli

Test_Files = {
    '.yotta_ignore': '''
#comment
/moo
b/c/d
b/c/*.txt
/a/b/test.txt
b/*.c
/source/a/b/test.txt
/test/foo
sometest/a
someothertest
ignoredbyfname.c
''',
    'module.json': '''
{
  "name": "test-testdep-f",
  "version": "0.0.6",
  "description": "Module to test test-dependencies and ignoring things",
  "author": "autopulated",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {},
  "testDependencies": {}
}
''',

'a/b/c/d/e/f/test.txt': '',
'a/b/c/d/e/test.c': '#error should be ignored',
'a/b/c/d/e/test.txt': '',
'a/b/c/d/test.c': '#error should be ignored',
'a/b/c/d/test.txt': '',
'a/b/c/d/z/test.c':'#error should be ignored',
'a/b/c/test.txt': '',
'a/b/test.txt':'',
'a/test.txt':'',
'comment':'# should not be ignored',
'f/f.h':'''
#ifndef __F_H__
#define __F_H__
int f();
#endif
''',
'source/moo/test.txt':'',
'source/a/b/c/d/e/f/test.txt': '',
'source/a/b/c/d/e/test.c': '#error should be ignored',
'source/a/b/c/d/e/test.txt': '',
'source/a/b/c/d/test.c': '#error should be ignored',
'source/a/b/c/d/test.txt': '',
'source/a/b/c/d/z/test.c':'#error should be ignored',
'source/a/b/c/test.txt': '',
'source/a/b/test.txt':'',
'source/a/test.txt':'',
'source/f.c':'''

int f(){
    return 6;
}
''',
'test/anothertest/ignoredbyfname.c':'#error should be ignored',
'test/anothertest/ignoredbyfname.c':'''
#include <stdio.h>

#include "f/f.h"

int main(){
    int result = f();
    printf("%d\n", result);
    return !(result == 6);
}
''',
'test/foo/ignored.c':'''
#error should be ignored
''',
'test/someothertest/alsoignored.c':'''
#error should be ignored
''',
'test/sometest/a/ignored.c':'''
#error should be ignored
'''
}

def isWindows():
    # can't run tests that hit github without an authn token
    return os.name == 'nt'

class TestPackIgnores(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        for path, contents in Test_Files.items():
            path_dir, file_name =  os.path.split(path)
            path_dir = os.path.join(self.test_dir, path_dir)
            mkDirP(path_dir)
            with open(os.path.join(path_dir, file_name), 'w') as f:
                f.write(contents)

    def tearDown(self):
        rmRf(self.test_dir)

    def test_absolute_ignores(self):
        c = component.Component(self.test_dir)
        self.assertTrue(c.ignores('moo'))
        self.assertTrue(c.ignores('test/foo/ignored.c'))

    def test_glob_ignores(self):
        c = component.Component(self.test_dir)
        self.assertTrue(c.ignores('a/b/c/test.txt'))
        self.assertTrue(c.ignores('a/b/test.txt'))
        self.assertTrue(c.ignores('a/b/test.c'))
        self.assertTrue(c.ignores('source/a/b/c/test.txt'))
        self.assertTrue(c.ignores('source/a/b/test.txt'))
        self.assertTrue(c.ignores('source/a/b/test.c'))

    def test_relative_ignores(self):
        c = component.Component(self.test_dir)
        self.assertTrue(c.ignores('a/b/c/d/e/f/test.txt'))
        self.assertTrue(c.ignores('a/b/test.txt'))
        self.assertTrue(c.ignores('source/a/b/c/d/e/f/test.txt'))
        self.assertTrue(c.ignores('source/a/b/test.txt'))
        self.assertTrue(c.ignores('test/anothertest/ignoredbyfname.c'))
        self.assertTrue(c.ignores('test/someothertest/alsoignored.c'))

    def test_comments(self):
        c = component.Component(self.test_dir)
        self.assertFalse(c.ignores('comment'))

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_build(self):
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'clean'], self.test_dir)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], self.test_dir)
        self.assertNotIn('ignoredbyfname', stdout)
        self.assertNotIn('someothertest', stdout)
        self.assertNotIn('sometest', stdout)

    @unittest.skipIf(isWindows(), "can't build natively on windows yet")
    def test_test(self):
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'clean'], self.test_dir)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], self.test_dir)
        self.assertNotIn('ignoredbyfname', stdout)
        self.assertNotIn('someothertest', stdout)
        self.assertNotIn('sometest', stdout)

    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=self.test_dir)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return stdout or stderr

if __name__ == '__main__':
    unittest.main()



