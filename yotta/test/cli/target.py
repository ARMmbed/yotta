#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile
import stat

# internal modules:
from yotta.lib.fsutils import rmRf
from . import cli


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

Check_Not_Stat = stat.S_IRWXG | stat.S_IRWXO

class TestCLITarget(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)

    def tearDown(self):
        rmRf(self.test_dir)

    def test_setTarget(self):
        rmRf(os.path.join(self.test_dir, '.yotta.json'))
        stdout = self.runCheckCommand(['target', 'testtarget', '-g'])
        stdout = self.runCheckCommand(['target'])
        self.assertTrue(stdout.find('testtarget') != -1)
        stdout = self.runCheckCommand(['target', 'x86-linux-native', '-g'])
        if os.name == 'posix':
            # check that the settings file was created with the right permissions
            self.assertFalse(
                os.stat(os.path.join(os.path.expanduser('~'), '.yotta', 'config.json')).st_mode & Check_Not_Stat
            )

    def test_setTargetLocal(self):
        stdout = self.runCheckCommand(['target', 'testtarget'])
        stdout = self.runCheckCommand(['target'])
        self.assertTrue(stdout.find('testtarget') != -1)
        stdout = self.runCheckCommand(['target', 'x86-linux-native'])
        if os.name == 'posix':
            # check that the settings file was created with the right permissions
            self.assertFalse(
                os.stat(os.path.join(self.test_dir, '.yotta.json')).st_mode & Check_Not_Stat
            )

    def runCheckCommand(self, args):
        stdout, stderr, statuscode = cli.run(args, cwd=self.test_dir)
        self.assertEqual(statuscode, 0)
        return stdout or stderr


if __name__ == '__main__':
    unittest.main()


