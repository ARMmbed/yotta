#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import subprocess
from collections import namedtuple
import tempfile

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from . import cli
from yotta.lib import version
from yotta.lib import settings
from yotta import install


Test_Target = "x86-osx-native,*"

Private_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "description": "a test module",
  "private": true,
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

class TestCLIPublish(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        rmRf(self.test_dir)

    def test_publishPrivate(self):
        with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
            f.write(Private_Module_JSON)
        stdout, stderr, status = cli.run(['--target', Test_Target, 'publish'], cwd=self.test_dir)
        self.assertNotEqual(status, 0)
        self.assertTrue('is private and cannot be published' in ('%s %s' % (stdout, stderr)))


if __name__ == '__main__':
    unittest.main()




