#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import logging
    
# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Resource, BasicAuth, errors as restkit_errors
from restkit.forms import multipart_form_encode

# connection_pool, , shared connection pool, internal
from yotta.lib import connection_pool
# access_common, , things shared between different component access modules, internal
from yotta.lib import access_common



# !!! TODO unit-ify this
def main():

    url = 'https://blobs.yottabuild.org/targets/stk3700-0.0.0.tar.gz'
    print 'get:', url
    resource = Resource(url)
    response = resource.get()
    print 'response:', response
    print 'headers:', dict(response.headers.items())
    print 'body len:', len(response.body_string())


    url = 'https://blobs.yottabuild.org/targets/stk3700-0.0.0.tar.gz'
    headers = { }
    print 'get:', url
    resource = Resource(url, pool=connection_pool.getPool(), follow_redirect=True)
    response = resource.get(
        headers = headers
    )
    print 'response:', response
    print 'headers:', dict(response.headers.items())
    print 'body len:', len(response.body_string())

    url = 'https://blobs.yottabuild.org/targets/stk3700-0.0.0.tar.gz'
    headers = { }
    print 'get:', url
    resource = Resource(url, pool=connection_pool.getPool(), follow_redirect=True)
    response = resource.get(
        headers = headers
    )
    access_common.unpackTarballStream(response.body_stream(), '/tmp/yttest/blobs/')

# main()

