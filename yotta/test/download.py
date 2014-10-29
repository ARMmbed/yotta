# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import multiprocessing

from yotta.lib import github_access
from yotta.lib.pool import pool


# !!! TODO unit-ify this

def main():

    tags = github_access._getTags('ARM-RD/libobjc2')

    pool.map(
        lambda (tag, url): github_access._getTarball(url, '/tmp/yttest/download/'+tag),
        tags.items()
    )

# main()
