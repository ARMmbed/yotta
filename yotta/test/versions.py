#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import unittest

from yotta.lib import version

# test the extra things we add to python-semanticversion by subclassing Version
# and Spec

class VersionTestCase(unittest.TestCase):
    matches = {
        '>=0.1.1,<0.1.2': (
            ['v0.1.1', '0.1.1+4', '0.1.1-alpha'],
            ['0.1.2-alpha', '0.1.2', '1.3.4'],
        ),
        '>=0.1.0+,!=0.1.3-rc1,<0.1.4': (
            ['0.1.1', 'v0.1.0+b4', '0.1.2', '0.1.3-rc2'],
            ['0.0.1', '0.1.4', '0.1.4-alpha', '0.1.3-rc1+4',
             '0.1.0-alpha', 'v0.2.2', '0.2.2', '0.1.4-rc1'],
        ),
        '^1.2.3':(
            ['1.2.3', '1.5.1'],
            ['1.2.2', '2.0.0-beta']
        ),
        '^0.1.2': (
            ['0.1.2'],
            ['0.1.3']
        ),
        '~1.2.3':(
            ['1.2.3', '1.2.4'],
            ['1.3.0-beta', '1.4.0']
        ),
        '>4.5.6':(
            ['4.5.7', ''],
            ['4.5.5', '4.5.6-a1', '4.5.6']
        ),
        '>=4.5.6':(
            ['4.5.7', '4.5.6', '4.5.6-a1', ''],
            ['4.5.5']
        ),
        '==0.1.7':(
            ['0.1.7', '0.1.7-a4'],
            ['0.1.6', '0.1.8', ''],
        ),
        '=0.1.7':(
            ['0.1.7', '0.1.7-a4'],
            ['0.1.6', '0.1.8', ''],
        ),
        '':(
            ['0.0.1', 'v0.1.4', '0.1.4-alpha', '0.1.3-rc1+4',
             '0.1.0-alpha', '0.2.2', '0.1.4-rc1', ''],
            []
        ),
        '*':(
            ['0.0.1', 'v0.1.4', '0.1.4-alpha', '0.1.3-rc1+4',
             '0.1.0-alpha', '0.2.2', '0.1.4-rc1', ''],
            []
        ),
    }

    def test_matches(self):
        for spec, (matching, failing) in self.matches.items():
            spec = version.Spec(spec)

            for v in [version.Version(v) for v in matching]:
                self.assertTrue(
                    v in spec,
                    "%r should be in %r" % (v, spec)
                )
                self.assertTrue(
                    spec.match(v),
                    "%r should match %r" % (v, spec)
                )

            for v in [version.Version(v) for v in failing]:
                self.assertFalse(
                    v in spec,
                    "%r should not be in %r" % (v, spec)
                )
                self.assertFalse(
                    spec.match(v),
                    "%r should not match %r" % (v, spec)
                )

    def test_hash(self):
        sets = [
            ['0.1.1', '==0.1.1', '=0.1.1'],
            ['', '*'],
        ]
        for s in [set([version.Spec(x) for x in l]) for l in sets]:
            self.assertEqual(1, len(s))

if __name__ == '__main__':
    unittest.main()
