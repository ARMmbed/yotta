# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# we need circular imports, and circular imports of relative paths aren't
# supported in python 3, so unfortunately we have to do this:
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

