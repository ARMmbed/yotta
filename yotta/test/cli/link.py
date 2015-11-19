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

class TestCLILink(unittest.TestCase):
    pass
    # TODO: test
    #   linking a dependency
    #   building with a linked dependency
    #   linking a target
    #   building with a linked target
    #   linking a base target
    #   building with a linked base target
    #   changing a linked dependency (check that a rebuild is triggered)



