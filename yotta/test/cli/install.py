#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import subprocess
from collections import namedtuple

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from . import cli
from yotta.lib import version
from yotta.lib import settings
from yotta import install


Test_Dir = '/tmp/yotta/version_cli_test'
Test_Name = 'testing-dummy'
Test_Github_Name = "autopulated/github-access-testing"
Test_Target = "x86-osx-native,*"
Test_Username = 'yottatest'
Test_Access_Token = 'c53aadbd89caefdcadb0d43d18ef863e1d9cbcf4'

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
  "dependencies": {
    "testing-dummy": "*"
  },
  "targetDependencies": {
    "x86-osx-native": {
        "other-testing-dummy": "git@bitbucket.org:autopulated/other-testing-dummy.git#0.0.1"
    }
  }
}
'''

def ensureGithubConfig():
    # ensure we have authentication for the test github account
    if not settings.getProperty('github', 'authtoken'):
        settings.setProperty('github', 'authtoken', Test_Access_Token)

class TestCLIInstall(unittest.TestCase):
    def setUp(self):
        mkDirP(Test_Dir)
        ensureGithubConfig()

    def tearDown(self):
        rmRf(Test_Dir)

    def test_installRegistryRef(self):
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', Test_Name])

    def test_installGithubRef(self):
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', Test_Github_Name])

    def test_installDeps(self):
        with open(os.path.join(Test_Dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'])

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'])
        self.assertTrue(stdout.find('testmod') != -1)
        self.assertTrue(stdout.find('other-testing-dummy') != -1)

        # and test install --save
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', '--save', 'hg-access-testing'])
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'])
        self.assertTrue(stdout.find('hg-access-testing') != -1)

    def runCheckCommand(self, args):
        stdout, stderr, statuscode = cli.run(args, cwd=Test_Dir)
        self.assertEqual(statuscode, 0)
        return stdout or stderr


if __name__ == '__main__':
    unittest.main()



