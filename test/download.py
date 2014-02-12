#! /usr/bin/env python2.7
import multiprocessing

from yotta.lib import github_access
from yotta.lib.pool import pool


tags = github_access._getTags('ARM-RD/libobjc2')

pool.map(
    lambda (tag, url): github_access._getTarball(url, '/tmp/yttest/download/'+tag),
    tags.items()
)

