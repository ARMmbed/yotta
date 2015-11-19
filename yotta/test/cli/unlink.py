#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile
import re

# internal modules:
from . import cli
from . import util

class TestCLIUnLink(unittest.TestCase):
    pass
    # TODO: test
    #   unlinking dependency
    #   unlink target
    #   unlink globally in a module
    #   unlink globally in a target
    #   unlink unknown dependency (what is expected behavior?)
    #   unlink unknown target (what is expected behavior?)
    #   unlink when not linked globally (what is expected behaviour?)



