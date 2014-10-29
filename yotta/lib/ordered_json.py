# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
from collections import OrderedDict

# provide read & write methods for json files that maintain the order of
# dictionary keys, and indent consistently

# Internals
def load(path):
    with open(path, 'r') as f:
        # using an ordered dictionary for objects so that we preserve the order
        # of keys in objects (including, for example, dependencies)
        return json.load(f, object_pairs_hook=OrderedDict)

def dump(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, separators=(',', ': '))

def loads(string):
    return json.loads(string, object_pairs_hook=OrderedDict)
