#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import copy
import time
import tempfile

# internal modules:
from yotta.lib.detect import systemDefaultTarget
from yotta.test.cli import cli
from yotta.test.cli import util

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

Test_Reporter_Script = '''
#! python

import threading
import sys
try:
    import Queue as queue
except ImportError:
    # queue module has a different name in python 3 :(
    import queue

args = sys.argv[1:]

def tryFloat(x):
    try:
        return float(x)
    except:
        return None

Verbose = '--verbose' in args
Delay = sum([x for x in [tryFloat(x) for x in args] if x is not None])

exitcode = 1

def consumeNonBlocking():
    global exitcode
    all_output = ''
    buf = sys.stdin.read(1)
    while buf:
        all_output += buf
        if Verbose:
            print('[[ >>>', buf, ']]')
        if '[pass]' in all_output:
            exitcode = 0
            sys.exit(0)
        if '[fail]' in all_output:
            exitcode = 1
            sys.exit(1)
        buf = sys.stdin.read(1)

if Verbose:
    print('[[starting consume thread]]')
t = threading.Thread(target=consumeNonBlocking)
t.daemon = True
t.start()

if Verbose:
    print('[[thread was started]]')

t.join(4.5)

if Verbose:
    print('[[thread was joined]]')
    print('[[doing some more stuff before process exit]]')
    print('[[' + 'verbose'*1000+ ']]')
    print('[[script args were:', sys.argv[1:], ']]')

if Delay:
    import time
    time.sleep(Delay)
sys.exit(exitcode)
'''

# matrix of test configurations:
#  * Test passes / fails
#  * Test is slow / fast
#  * Test reporter is present / not
#  * If the test reporter is present:
#       * the test does / doesn't print extra data after pass/fail
#       * the reporter does/doesn't wait after the script has exited
#       * the reporter does/doesn't print information to stdout

def forAllReporterTests(fn):
    for reporter in [True, False]:
        for test_passes in [True, False]:
            for test_speed in ['slow', 'fast']:
                for test_verbose in [True, False]:
                    if reporter:
                        for reporter_waits in [2, 0]:
                            for reporter_verbose in [True, False]:
                                fn(
                                           reporter=reporter,
                                        test_passes=test_passes,
                                         test_speed=test_speed,
                                       test_verbose=test_verbose,
                                     reporter_waits=reporter_waits,
                                   reporter_verbose=reporter_verbose
                               )
                    else:
                        fn(
                                   reporter=reporter,
                                test_passes=test_passes,
                                 test_speed=test_speed,
                               test_verbose=test_verbose,
                             reporter_waits=0,
                           reporter_verbose=None
                       )

def cFileForReporterTest(**kwargs):
    r = '#include <unistd.h>\n#include <stdio.h>\n\nint main(){\n'
    if kwargs['reporter']:
        # slow reporter tests delay after printing
        if kwargs['test_verbose']:
            r += '  printf("'+'testverbose0'*77+'");\n'
        r += '  printf("[pass]\\n\\r");\n' if kwargs['test_passes'] else ' printf("[fail]\\n\\r");\n'
        if kwargs['test_verbose']:
            r += '  printf("'+'testverbose1'*22+'");\n'
        if kwargs['test_speed'] == 'slow':
            r += '  sleep(2);\n'
        if kwargs['test_verbose']:
            r += '  printf("'+'testverbose2'*33+'");\n'
        r += '  return 1;\n'
    else:
        if kwargs['test_verbose']:
            r += '  printf("'+'testverbose0'*22+'");\n'
        # slow non-reporter tests delay before exiting
        if kwargs['test_speed'] == 'slow':
            r += '  sleep(2);\n'
            if kwargs['test_verbose']:
                r += '  printf("'+'testverbose1'*77+'");\n'
        r += ' return 0;\n' if kwargs['test_passes'] else '  return 17;\n'
    r += '}\n'
    return r



def filesForReporterTest(**kwargs):
    Test = {
    }
    if kwargs['reporter']:
        reporter_command = '["python", "./report.py"'
        if kwargs['reporter_verbose']:
            reporter_command += ', "--verbose"'
        if kwargs['reporter_waits']:
            reporter_command += (', "%s"' % kwargs['reporter_waits'])
        reporter_command += "]"
        Test['module.json'] = '{"name": "reporter", "version": "0.0.0", "license": "Apache-2.0", "scripts":{"testReporter":'+reporter_command+'}}\n'
        Test['report.py'] = Test_Reporter_Script
    else:
        Test['module.json'] = '{"name": "reporter", "version": "0.0.0", "license": "Apache-2.0"}\n'
    Test['test/x.c'] = cFileForReporterTest(**kwargs)
    return Test


class TestCLITest(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_tests(self):
        test_dir = util.writeTestFiles(Test_Tests, True)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'build'], test_dir)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        self.assertIn('test-a passed', output)
        self.assertIn('test-c passed', output)
        self.assertIn('test-d passed', output)
        self.assertIn('test-e passed', output)
        self.assertIn('test-f passed', output)
        self.assertIn('test-g passed', output)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_testOutputFilterPassing(self):
        test_dir = util.writeTestFiles(Test_Fitler_Pass, True)
        stdout = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_testOutputFilterFailing(self):
        test_dir = util.writeTestFiles(Test_Fitler_Fail, True)
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
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_testOutputFilterNotFound(self):
        test_dir = util.writeTestFiles(Test_Fitler_NotFound, True)
        stdout, stderr, statuscode = cli.run(['--target', systemDefaultTarget(), 'test'], cwd=test_dir)
        if statuscode == 0:
            print(stdout)
            print(stderr)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_testCustomCMake(self):
        test_dir = util.writeTestFiles(util.Test_Test_Custom_CMake, True)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        self.assertIn('test-trivial-lib-maintest passed', output)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_testAdditionalCMake(self):
        test_dir = util.writeTestFiles(util.Test_Test_Extra_CMake, True)
        output = self.runCheckCommand(['--target', systemDefaultTarget(), 'test'], test_dir)
        self.assertIn('test-trivial-lib-test-main passed', output)
        util.rmRf(test_dir)

    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return '%s %s' % (stdout, stderr)

# the generated tests share a single test directory, so that the target
# descriptions etc. don't have to be re-downloaded many times (this makes them
# much faster)
class TestCLITestGenerated(TestCLITest):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp() + 'spaces in path'

    @classmethod
    def tearDownClass(cls):
        util.rmRf(cls.test_dir)

# generate the filter-testing tests dynamically:
def generateTestMethod(**kwargs):
    def generatedTestMethod(self):
        test_dir = util.writeTestFiles(filesForReporterTest(**kwargs), test_dir=self.test_dir)

        # build first, to make test timing more accurate:
        stdout, stderr, statuscode = cli.run(['--target', systemDefaultTarget(), 'build'], cwd=test_dir)
        #print('build:', stdout)
        #print('build:', stderr)
        #print('build statuscode was:', statuscode)
        self.assertEqual(statuscode, 0)

        tstart = time.time()
        stdout, stderr, statuscode = cli.run(['-vvv', '--target', systemDefaultTarget(), 'test'], cwd=test_dir)
        duration = time.time() - tstart

        # useful output for debugging failed tests:
        if bool(statuscode) == bool(kwargs['test_passes']) or \
                duration >= 5.5 + kwargs['reporter_waits'] or \
                (kwargs['test_speed'] == 'fast' and (duration >= 1.5 + kwargs['reporter_waits'])):
            print(stdout + stderr)
            print(statuscode)
            print('duration:', duration)

        if kwargs['test_passes']:
            self.assertEqual(statuscode, 0)
        else:
            self.assertNotEqual(statuscode, 0)

        # **no** tests should cause a timeout (Which is set at 4.5 seconds in
        # the test reporter), + the wait-for duration (+ 1 second slack for
        # process startup etc.)
        self.assertTrue(duration < 5.5 + kwargs['reporter_waits'])

        # if a test isn't slow, then it should run in less than 1 seconds
        if kwargs['test_speed'] == 'fast':
            self.assertTrue(duration < 1.5 + kwargs['reporter_waits'])
    return generatedTestMethod

def generateTest(**kwargs):
    test_name = "test_" + '_'.join([ '%s_%s' % (k, v) for k, v in sorted(kwargs.items(), key=lambda x: x[0])])
    test_method = generateTestMethod(**kwargs)
    test_method.__name__ = test_name
    setattr(TestCLITestGenerated, test_name, test_method)

if util.canBuildNatively():
    forAllReporterTests(generateTest)
else:
    print('WARNING: skipping test reporter tests (cannot build natively on this platform)')
