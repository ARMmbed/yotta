#!/usr/bin/env python
# Copyright 2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import os

# internal modules:
from yotta.test.cli import util
from yotta.test.cli import cli

def _nopStartTargetDescription(name):
    native_target = util.nativeTarget()
    if ',' in native_target:
        native_target = native_target[:native_target.find(',')]
    return {
    'target.json':'''{
      "name": "%s",
      "version": "1.0.0",
      "license": "Apache-2.0",
      "inherits": {
        "%s": "*"
      },
      "scripts": {
        "start": ["./scripts/nop.py", "$program"]
      }
    }
    ''' % (name, native_target),
    './scripts/nop.py':'''
import os
print('would start %s' % os.environ['YOTTA_PROGRAM'])
    '''
    }

class TestCLIStart(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_noop_start(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        util.writeTestFiles(_nopStartTargetDescription('start-test-target'), test_dir=os.path.join(test_dir, 'yotta_targets', 'start-test-target'))
        output = util.runCheckCommand(['--target', 'start-test-target', 'build'], test_dir)
        output = util.runCheckCommand(['--target', 'start-test-target', 'start'], test_dir)
        self.assertIn('would start source/test-trivial-exe', output)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_native_start(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        output = util.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        output = util.runCheckCommand(['--target', util.nativeTarget(), 'start'], test_dir)
        self.assertIn('[trivial-exe-running]', output)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_notfound_start(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        target_descr = _nopStartTargetDescription('start-test-target')
        del target_descr['./scripts/nop.py']
        util.writeTestFiles(target_descr, test_dir=os.path.join(test_dir, 'yotta_targets', 'start-test-target'))

        # in this case, without the script present we expect a failure
        output = util.runCheckCommand(['--target', 'start-test-target', 'build'], test_dir)
        stdout, stderr, statuscode = cli.run(['--target', 'start-test-target', 'start'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_dir)


