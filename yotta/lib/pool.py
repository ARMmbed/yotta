# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

from multiprocessing.pool import ThreadPool

# this module just provides a shared thread pool for all multiprocessing users
# to use: the number of threads is high because tasks are expected to be
# IO-bound

pool = ThreadPool(4)

