# standard library modules, , ,
import argparse
import logging
import os

# version, , represent versions and specifications, internal
from lib import version
# Component, , represents an installed component, internal
from lib import component



def addOptions(parser):
    # no options
    pass


def execCommand(args):
    wd = os.getcwd()
    c = component.Component(wd)
    # skip testing for target if we already found a component
    t = None if c else target.Target(wd)
    if not (c or t):
        logging.debug(str(c.getError()))
        logging.debug(str(t.getError()))
        logging.error('The current directory does not contain a valid component or target.')
    
    if not (c or t).vcsIsClean():
        logging.error('The working directory is not clean. Commit before publishing!')
        return 1

    # standard library modules, , ,    
    from collections import OrderedDict
    import uuid
    
    # restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
    from restkit import Resource, BasicAuth, Connection, request
    from restkit.forms import multipart_form_encode
    # socket pool, Public Domain / MIT, installed with restkit
    from socketpool import ConnectionPool

    # settings, , load and save settings, internal
    from lib import settings
    # fsutils, , misc filesystem utils, internal
    from lib import fsutils
    # connection_pool, , shared connection pool, internal
    from lib import connection_pool


    # TODO, move appropriate parts of this into registry_access, also wrap for
    # github auth
    #upload_archive_name = 'upload.tar.gz'
    #fsutils.rmF(upload_archive_name)
    #fd = os.open(upload_archive_name, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    #with os.fdopen(fd, 'rb+') as tar_file:
    #    tar_file.truncate()
    #    (c or t).generateTarball(tar_file)
    #    tar_file.seek(0)

    #    with open((c or t).getDescriptionFile(), 'r') as description_file:
    #        description = description_file.read()

    #    url = '%s/%s?access_token=%s' % (
    #        (c or t).getRegistryURL(),
    #        (c or t).getVersion(),
    #        settings.getProperty('github', 'authtoken')
    #    )

    #    body = OrderedDict([('metadata',description), ('tarball',tar_file)])
    #    headers = { }
    #    body, headers = multipart_form_encode(body, headers, uuid.uuid4().hex)

    #    # basic auth until we release publicly, to prevent outside registry access:
    #    auth = BasicAuth('yotta','h297fb08625rixmzw7s9')

    #    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    #    response = resource.put(
    #        headers = headers,
    #        payload = body
    #    )
    #    print 'headers:', dict(response.headers.items())
    #    print 'body:', response.body_string()
    
    # list versions of the package:
    url = '%s?access_token=%s' % (
        (c or t).getRegistryURL(),
        settings.getProperty('github', 'authtoken')
    )
    headers = { }
    # basic auth until we release publicly, to prevent outside registry access:
    auth = BasicAuth('yotta','h297fb08625rixmzw7s9')

    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    response = resource.get(
        headers = headers
    )
    print 'headers:', dict(response.headers.items())
    print 'body:', response.body_string()

    
    # get description of the current version:
    url = '%s/%s?access_token=%s' % (
        (c or t).getRegistryURL(),
        (c or t).getVersion(),
        settings.getProperty('github', 'authtoken')
    )
    headers = { }
    # basic auth until we release publicly, to prevent outside registry access:
    auth = BasicAuth('yotta','h297fb08625rixmzw7s9')

    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    response = resource.get(
        headers = headers
    )
    print 'headers:', dict(response.headers.items())
    print 'body:', response.body_string()

    
    
    # get tarball of the current version:
    url = '%s/%s/tarball?access_token=%s' % (
        (c or t).getRegistryURL(),
        (c or t).getVersion(),
        settings.getProperty('github', 'authtoken')
    )
    headers = { }
    # basic auth until we release publicly, to prevent outside registry access:
    auth = BasicAuth('yotta','h297fb08625rixmzw7s9')

    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    response = resource.get(
        headers = headers
    )
    print 'headers:', dict(response.headers.items())
    print 'body:', response.body_string()
