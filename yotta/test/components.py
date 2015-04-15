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
import tempfile
from collections import OrderedDict

from yotta.lib import access
from yotta.lib import component
from yotta.lib.pool import pool
from yotta.lib.fsutils import mkDirP, rmRf

test_json = '''{
  "name": "something",
  "version": "0.0.7",
  "description": "some description.",
  "private": false,
  "homepage": "https://github.com/somewhere/something",
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
  "testDependencies": {
    "atestdep": "~0.2.3"
  },
  "targetDependencies": {
    "sometarget": {
      "atargetdep": "~1.3.4"
    }
  },
  "testTargetDependencies": {
    "sometarget": {
      "anothertargetdep": "~1.3.4"
    },
    "someothertarget": {
      "adifferenttargetdep": "~1.3.4"
    }
  }
}
'''

deps_in_order = [
    'toolchain', 'libc', 'libobjc2', 'yottos-platform', 'emlib',
    'nsobject', 'nslog', 'nsassert', 'thisdoesnotexist'
]

test_deps_in_order = deps_in_order + ['atestdep']

logging.basicConfig(
    level=logging.ERROR
)

class ComponentTestCase(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        rmRf(self.test_dir)


    def test_component_init(self):
        # test things about components that don't (and shouldn't) require
        # hitting the network

        with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
            f.write(test_json)

        c = component.Component(self.test_dir)
        self.assertTrue(c)

        self.assertEqual(c.getName(), 'something')
        self.assertEqual(str(c.getVersion()), '0.0.7')

        deps = c.getDependencies()
        self.assertEqual(list(deps.keys()), deps_in_order)

        test_deps = c.getDependencies(test=True)
        self.assertEqual(list(test_deps.keys()), test_deps_in_order)


    def test_mergeDictionaries(self):
        a = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('subdict', OrderedDict([('a',7), ('c',0)]))])
        b = OrderedDict([('a', 2), ('d', 4), ('e', 5), ('subdict', {'a':12, 'b':8, 'subsubdict':{1:'a', 2:'b'}})])
        c = OrderedDict([('subdict', {'subsubdict':{3:'c'}})])

        self.assertEqual(component._mergeDictionaries(a, {}), a)
        self.assertEqual(component._mergeDictionaries(b, {}), b)
        self.assertEqual(component._mergeDictionaries(c, {}), c)
        self.assertEqual(
            component._mergeDictionaries(a, b),
            OrderedDict([
                ('a', 1),
                ('b', 2),
                ('c', 3),
                ('subdict', OrderedDict([('a', 7), ('c', 0), ('subsubdict', {1: 'a', 2: 'b'}), ('b', 8)])),
                ('d', 4),
                ('e', 5)
            ])
        )
        self.assertEqual(
            component._mergeDictionaries(component._mergeDictionaries(a, b), c),
            OrderedDict([
                ('a', 1),
                ('b', 2),
                ('c', 3),
                ('subdict', OrderedDict([('a', 7), ('c', 0), ('subsubdict', {1: 'a', 2: 'b', 3:'c'}), ('b', 8)])),
                ('d', 4),
                ('e', 5)
            ])
        )

if __name__ == '__main__':
    unittest.main()
