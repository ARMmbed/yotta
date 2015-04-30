#! /usr/bin/env python2.7
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import unittest
import logging
from collections import OrderedDict

from yotta.lib import target

logging.basicConfig(
    level=logging.ERROR
)

class ComponentTestCase(unittest.TestCase):
    def test_mergeDictionaries(self):
        a = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('subdict', OrderedDict([('a',7), ('c',0)]))])
        b = OrderedDict([('a', 2), ('d', 4), ('e', 5), ('subdict', {'a':12, 'b':8, 'subsubdict':{1:'a', 2:'b'}})])
        c = OrderedDict([('subdict', {'subsubdict':{3:'c'}})])

        self.assertEqual(target._mergeDictionaries(a, {}), a)
        self.assertEqual(target._mergeDictionaries(b, {}), b)
        self.assertEqual(target._mergeDictionaries(c, {}), c)
        self.assertEqual(
            target._mergeDictionaries(a, b),
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
            target._mergeDictionaries(target._mergeDictionaries(a, b), c),
            OrderedDict([
                ('a', 1),
                ('b', 2),
                ('c', 3),
                ('subdict', OrderedDict([('a', 7), ('c', 0), ('subsubdict', {1: 'a', 2: 'b', 3:'c'}), ('b', 8)])),
                ('d', 4),
                ('e', 5)
            ])
        )

