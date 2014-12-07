#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from . import cli


Test_Dir = '/tmp/yotta/version_cli_test'
Test_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "description": "a test module",
  "keywords": [
  ],
  "author": "Someone Somewhere <someone.somewhere@yottabuild.org>",
  "repository": {
    "url": "git@github.com:mbedmicro/testmod.git",
    "type": "git"
  },
  "homepage": "https://github.com/mbedmicro/testmod",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {},
  "targetDependencies": {}
}
'''

class TestCLIVersion(unittest.TestCase):
    def setUp(self):
        mkDirP(Test_Dir)
        with open(os.path.join(Test_Dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        
    def tearDown(self):
        rmRf(Test_Dir)

    def test_displayVersion(self):
        stdout = self.runCheckCommand(['version'])
        self.assertTrue(stdout.find('0.0.0') != -1)

    def test_bumpVersion(self):
        stdout = self.runCheckCommand(['version', 'patch'])
        stdout = self.runCheckCommand(['version'])
        self.assertTrue(stdout.find('0.0.1') != -1)

        stdout = self.runCheckCommand(['version', 'major'])
        stdout = self.runCheckCommand(['version'])
        self.assertTrue(stdout.find('1.0.0') != -1)

        stdout = self.runCheckCommand(['version', 'minor'])
        stdout = self.runCheckCommand(['version'])
        self.assertTrue(stdout.find('1.1.0') != -1)

        stdout = self.runCheckCommand(['version', '1.2.3-alpha1'])
        stdout = self.runCheckCommand(['version'])
        self.assertTrue(stdout.find('1.2.3-alpha1') != -1)

    def runCheckCommand(self, args):
        stdout, stderr, statuscode = cli.run(args, cwd=Test_Dir)
        self.assertEqual(statuscode, 0)
        return stdout or stderr


if __name__ == '__main__':
    unittest.main()

