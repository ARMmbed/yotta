#!/usr/bin/env python
# Copyright 2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import unittest
import os

# internal modules:
from yotta.test.cli import util
from yotta.test.cli import cli

JSON_MARKER = '###---###'
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
        "debug": ["./scripts/nop.py", "$program", "$build_dir", "$target_dir"]
      }
    }
    ''' % (name, native_target),
    './scripts/nop.py':'''
import os
import sys
import json

env_keys = ["YOTTA_PROGRAM", "YOTTA_BUILD_DIR", "YOTTA_TARGET_DIR"]
print(json.dumps({"argv": sys.argv[1:], "env": {k: v for k, v in os.environ.items() if k in env_keys}}))
print('%s')
    ''' % JSON_MARKER
    }

class TestCLIDebug(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_noop_debug(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe, True)
        target_dir = os.path.realpath(os.path.join(test_dir, 'yotta_targets', 'debug-test-target'))
        build_dir = os.path.realpath(os.path.join(test_dir, 'build', 'debug-test-target'))

        util.writeTestFiles(_nopDebugTargetDescription('debug-test-target'), test_dir=target_dir)
        output = util.runCheckCommand(['--target', 'debug-test-target', 'build'], test_dir)
        output = util.runCheckCommand(['--target', 'debug-test-target', 'debug'], test_dir)
        json_output = output[:output.index(JSON_MARKER)]
        result = json.loads(json_output)

        self.assertTrue(result is not None)
        self.assertEqual(len(result['argv']), 3)
        self.assertEqual(result['argv'][0], 'source/test-trivial-exe')
        self.assertEqual(result['env']['YOTTA_PROGRAM'], 'source/test-trivial-exe')
        self.assertEqual(result['argv'][1], build_dir)
        self.assertEqual(result['env']['YOTTA_BUILD_DIR'], build_dir)
        self.assertEqual(result['argv'][2], target_dir)
        self.assertEqual(result['env']['YOTTA_TARGET_DIR'], target_dir)

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


