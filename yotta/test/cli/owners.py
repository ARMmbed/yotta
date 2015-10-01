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
from yotta.lib.fsutils import rmRf
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
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        with open(os.path.join(cls.test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        cls.saved_settings_dir = None
        # override the settings directory, so that we can be sure we're not
        # logged in
        if 'YOTTA_USER_SETTINGS_DIR' in os.environ:
            cls.saved_settings_dir = os.environ['YOTTA_USER_SETTINGS_DIR']
        # use a directory called tmp_yotta_settings in the working directory:
        os.environ['YOTTA_USER_SETTINGS_DIR'] = 'tmp_yotta_settings'

    @classmethod
    def tearDownClass(cls):
        rmRf(cls.test_dir)
        cls.test_dir = None
        if cls.saved_settings_dir is not None:
            os.environ['YOTTA_USER_SETTINGS_DIR'] = cls.saved_settings_dir
            cls.saved_settings_dir = None
        else:
            del os.environ['YOTTA_USER_SETTINGS_DIR']

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


