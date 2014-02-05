import multiprocessing

from lib import github_access
from lib.pool import pool


tags = github_access.getTags('ARM-RD/libobjc2')

pool.map(
    lambda (tag, url): github_access.getTarball(url, '/tmp/yttest/download/'+tag),
    tags.items()
)

