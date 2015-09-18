#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import tempfile
import os

# validate, , validate various things, internal
from yotta.lib import settings
from yotta.lib.fsutils import rmRf

class TestSettings(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        test_files = [
            ('1.json', '{"a":{"b":{"c":"1-value"}}}'),
            ('2.json', '{"a":{"b":{"c":"2-value"}, "b2":"2-value"}}'),
            ('3.json', '{"a":{"b":{"c":"3-value"}, "b2":"3-value"}, "a2":"3-value"}')
        ]
        self.filenames = []
        for fn, s in test_files:
            self.filenames.append(os.path.join(self.test_dir, fn))
            with open(self.filenames[-1], 'w') as f:
                f.write(s)

    def tearDown(self):
        rmRf(self.test_dir)

    def test_merging(self):
        p = settings._JSONConfigParser()
        p.read(self.filenames)
        self.assertEqual(p.get('a.b.c'), '1-value')
        self.assertEqual(p.get('a.b2'), '2-value')
        self.assertEqual(p.get('a2'), '3-value')

    def test_setting(self):
        p = settings._JSONConfigParser()
        p.read(self.filenames)

        p.set('foo', 'xxx')
        self.assertEqual(p.get('foo'), 'xxx')

        p.set('someLongNameHere_etc_etc', 'xxx')
        self.assertEqual(p.get('someLongNameHere_etc_etc'), 'xxx')

        p.set('someLongNameHere_etc_etc.with.a.path', True, filename=self.filenames[1])
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.a.path'), True)

        p.set('someLongNameHere_etc_etc.with.a.path', False, filename=self.filenames[1])
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.a.path'), False)

        # NB: don't expect it to change when we set a value that's shadowed by
        # an earlier file:
        p.set('someLongNameHere_etc_etc.with.a.path', 7, filename=self.filenames[2])
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.a.path'), False)

        p.set('someLongNameHere_etc_etc.with.another.path', 7, filename=self.filenames[2])
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.another.path'), 7)


    def test_writing(self):
        p = settings._JSONConfigParser()
        p.read(self.filenames)

        p.set('foo', 'xxx')
        p.set('someLongNameHere_etc_etc', 'xxx')
        p.set('someLongNameHere_etc_etc.with.a.path', True, filename=self.filenames[1])
        p.set('someLongNameHere_etc_etc.with.a.path', False, filename=self.filenames[1])
        p.set('someLongNameHere_etc_etc.with.a.path', 7, filename=self.filenames[2])
        p.set('someLongNameHere_etc_etc.with.another.path', 7, filename=self.filenames[2])

        # NB: only write settings to the first file
        p.write()

        self.assertEqual(p.get('foo'), 'xxx')
        self.assertEqual(p.get('someLongNameHere_etc_etc'), 'xxx')
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.a.path'), False)
        self.assertEqual(p.get('someLongNameHere_etc_etc.with.another.path'), 7)

        p2 = settings._JSONConfigParser()
        p2.read(self.filenames)
        self.assertEqual(p2.get('foo'), 'xxx')
        self.assertEqual(p2.get('someLongNameHere_etc_etc'), 'xxx')

        # check that we only wrote settings to the first file
        self.assertEqual(p2.get('someLongNameHere_etc_etc.with.a.path'), None)

        # now write settings for the other files, and continue
        p.write(self.filenames[1])
        p.write(self.filenames[2])

        p3 = settings._JSONConfigParser()
        p3.read(self.filenames)
        self.assertEqual(p3.get('someLongNameHere_etc_etc.with.a.path'), False)
        self.assertEqual(p3.get('someLongNameHere_etc_etc.with.another.path'), 7)


        p4 = settings._JSONConfigParser()
        p4.read([self.filenames[1]])
        self.assertEqual(p4.get('foo'), None)
        self.assertEqual(p4.get('someLongNameHere_etc_etc.with.a.path'), False)
        self.assertEqual(p4.get('someLongNameHere_etc_etc.with.another.path'), None)

        p5 = settings._JSONConfigParser()
        p5.read([self.filenames[2]])
        self.assertEqual(p5.get('foo'), None)
        self.assertEqual(p5.get('someLongNameHere_etc_etc.with.a.path'), 7)
        self.assertEqual(p5.get('someLongNameHere_etc_etc.with.another.path'), 7)



if __name__ == '__main__':
    unittest.main()




