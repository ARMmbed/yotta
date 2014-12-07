#! /usr/bin/env python2.7
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


import unittest
import os
import shutil
import errno
import logging

from yotta.lib import access
from yotta.lib import component
from yotta.lib.pool import pool
from yotta.lib.fsutils import mkDirP

testdir = '/tmp/ytcomponenttest'

# !!! currently: discard all log messages. maybe we want to use a more
# sophisticated logging handler that stores the messages so we can inspect them
# in tests
logging.basicConfig(
    level=logging.ERROR
)


class ComponentTestCase(unittest.TestCase):
    test_json = '''{
  "name": "yottos",
  "version": "0.0.7",
  "description": "The core Yottos scheduler.",
  "private": false,
  "repository": {
    "type": "git",
    "url": "ssh://nadc-login2.nadc.arm.com//projects/pd/randd/git/iot/yottos/yottos"
  },
  "homepage": "ssh://nadc-login2.nadc.arm.com//projects/pd/randd/git/iot/yottos/yottos",
  "bugs": {
    "url": "about:blank",
    "email": "project@hostname.com"
  },
  "author": "James Crosby <James.Crosby@arm.com>",
  "licenses": [
    {
      "type": "Copyright (C) 2013 ARM Limited, all rights reserved.",
      "url": "about:blank"
    }
  ],
  "dependencies": {
    "toolchain": "ARM-RD/toolchain",
    "libc": "ARM-RD/libc",
    "libobjc2": "ARM-RD/libobjc2 @>0.0.7",
    "yottos-platform": "ARM-RD/yottos-platform @0.0.3",
    "emlib": "ARM-RD/emlib",
    "nsobject": "ARM-RD/nsobject",
    "nslog": "ARM-RD/nslog",
    "nsassert": "ARM-RD/nsassert",
    "thisdoesnotexist": "ARM-RD/thisdoesnotexist"
  },
  "devDependencies": {}
}
'''
    deps_in_order = [
        'toolchain', 'libc', 'libobjc2', 'yottos-platform', 'emlib',
        'nsobject', 'nslog', 'nsassert', 'thisdoesnotexist'
    ]
    def test_component_init(self):
        # test things about components that don't (and shouldn't) require
        # hitting the network
        try:
            shutil.rmtree(testdir)
        except OSError: pass

        mkDirP(testdir)
        with open(os.path.join(testdir, 'module.json'), 'w') as f:
            f.write(self.test_json)

        c = component.Component(testdir)
        self.assertTrue(c)

        self.assertEqual(c.getName(), 'yottos')
        self.assertEqual(str(c.getVersion()), '0.0.7')

        deps = c.getDependencies()
        self.assertEqual(list(deps.keys()), self.deps_in_order)

if __name__ == '__main__':
    unittest.main()
