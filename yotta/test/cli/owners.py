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

    # you have have to be authenticated to list owners, so this doesn't work
    # yet...
    #def test_listOwners(self):
    #    stdout = self.runCheckCommand(['owners', 'ls'])
    #    self.assertTrue(stdout.find('autopulated@gmail.com') != -1)

    def runCheckCommand(self, args):
        stdout, stderr, statuscode = cli.run(args, cwd=self.test_dir)
        self.assertEqual(statuscode, 0)
        return stdout or stderr


if __name__ == '__main__':
    unittest.main()


