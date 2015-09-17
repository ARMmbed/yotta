#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from . import cli


Test_Module_JSON = '''{
  "name": "git-access-testing",
  "version": "0.0.2",
  "description": "Git Access Testing",
  "author": "autopulated",
  "homepage": "https://github.com/autopulated/git-access-testing",
  "licenses": [
    {
      "url": "about:blank",
      "type": ""
    }
  ],
  "dependencies": {
    "testing-dummy": "git@bitbucket.org:autopulated/testing-dummy.git",
    "other-testing-dummy": "git@bitbucket.org:autopulated/other-testing-dummy.git#0.0.2"
  }
}
'''

class TestCLIOwners(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        
    def tearDown(self):
        rmRf(self.test_dir)

    # you have have to be authenticated to list owners, so currently we only
    # test that the commands fail correctly in noninteractive mode:

    def test_listOwners(self):
        stdout, stderr, statuscode = cli.run(['-n', 'owners', 'ls'], cwd=self.test_dir)
        if statuscode != 0:
            self.assertTrue((stdout+stderr).find('login required') != -1)

    def test_addOwner(self):
        stdout, stderr, statuscode = cli.run(['-n', 'owners', 'add', 'friend@example.com'], cwd=self.test_dir)
        if statuscode != 0:
            self.assertTrue((stdout+stderr).find('login required') != -1)

    def test_rmOwner(self):
        stdout, stderr, statuscode = cli.run(['-n', 'owners', 'rm', 'friend@example.com'], cwd=self.test_dir)
        if statuscode != 0:
            self.assertTrue((stdout+stderr).find('login required') != -1)


if __name__ == '__main__':
    unittest.main()


