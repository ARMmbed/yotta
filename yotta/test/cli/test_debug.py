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

def _nopDebugTargetDescription(name):
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
        "debug": ["./scripts/nop.py", "$program"]
      }
    }
    ''' % (name, native_target),
    './scripts/nop.py':'''
import os
print('would debug %s' % os.environ['YOTTA_PROGRAM'])
    '''
    }

class TestCLIDebug(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_noop_debug(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        util.writeTestFiles(_nopDebugTargetDescription('debug-test-target'), test_dir=os.path.join(test_dir, 'yotta_targets', 'debug-test-target'))
        output = util.runCheckCommand(['--target', 'debug-test-target', 'build'], test_dir)
        output = util.runCheckCommand(['--target', 'debug-test-target', 'debug'], test_dir)
        self.assertIn('would debug source/test-trivial-exe', output)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_notfound_debug(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        target_descr = _nopDebugTargetDescription('debug-test-target')
        del target_descr['./scripts/nop.py']
        util.writeTestFiles(target_descr, test_dir=os.path.join(test_dir, 'yotta_targets', 'debug-test-target'))

        # in this case, without the script present we expect a failure
        output = util.runCheckCommand(['--target', 'debug-test-target', 'build'], test_dir)
        stdout, stderr, statuscode = cli.run(['--target', 'debug-test-target', 'debug'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        util.rmRf(test_dir)


