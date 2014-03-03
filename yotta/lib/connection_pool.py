
# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Connection
# socket pool, Public Domain / MIT, installed with restkit
from socketpool import ConnectionPool

# This module provides a socketpool ConnectionPool of restkit Connections to be
# shared by all other modules that use restkit

_pool = None
def getPool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(factory=Connection)
    return _pool
