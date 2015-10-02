# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import re
import logging
from collections import OrderedDict
import functools
import binascii
import calendar
import datetime
import hashlib
import base64
import os
try:
    from urllib import quote as quoteURL
except ImportError:
    from urllib.parse import quote as quoteURL #pylint: disable=no-name-in-module,import-error

# requests, apache2
import requests

# PyJWT, MIT, Jason Web Tokens, pip install PyJWT
import jwt
# cryptography, Apache License, Python Cryptography library,
#import cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# settings, , load and save settings, internal
import settings
# access_common, , things shared between different component access modules, internal
import access_common
# Ordered JSON, , read & write json, internal
import ordered_json
# export key, , export pycrypto keys, internal
import exportkey
# auth, , authenticate users, internal
import auth
# globalconf, share global arguments between modules, internal
import yotta.lib.globalconf as globalconf

Registry_Base_URL = 'https://registry.yottabuild.org'
Website_Base_URL  = 'http://yottabuild.org'
_OpenSSH_Keyfile_Strip = re.compile(b"^(ssh-[a-z0-9]*\s+)|(\s+.+\@.+)|\n", re.MULTILINE)

logger = logging.getLogger('access')

# suppress logging from the requests library
logging.getLogger("requests").setLevel(logging.WARNING)

class AuthError(RuntimeError):
    pass

# Internal functions

def generate_jwt_token(private_key, registry=None):
    registry = registry or Registry_Base_URL
    expires = calendar.timegm((datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timetuple())
    prn = _fingerprint(private_key.public_key())
    logger.debug('fingerprint: %s' % prn)
    token_fields = {
        "iss": 'yotta',
        "aud": registry,
        "prn": prn,
        "exp": str(expires)
    }
    logger.debug('token fields: %s' % token_fields)
    private_key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    token = jwt.encode(token_fields, private_key_pem.decode('ascii'), 'RS256').decode('ascii')
    logger.debug('encoded token: %s' % token)

    return token

def _pubkeyWireFormat(pubkey):
    pubk_numbers = pubkey.public_numbers()
    logger.debug('openssh format publickey:\n%s' % exportkey.openSSH(pubk_numbers))
    return quoteURL(_OpenSSH_Keyfile_Strip.sub(b'', exportkey.openSSH(pubk_numbers)))

def _fingerprint(pubkey):
    stripped = _OpenSSH_Keyfile_Strip.sub(b'', exportkey.openSSH(pubkey.public_numbers()))
    decoded  = base64.b64decode(stripped)
    khash    = hashlib.md5(decoded).hexdigest()
    return ':'.join([khash[i:i+2] for i in range(0, len(khash), 2)])


def _retryConnectionErrors(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        attempts_remaining = 5
        delay = 0.1
        while True:
            attempts_remaining -= 1
            try:
                return fn(*args, **kwargs)
            except requests.exceptions.ConnectionError as e:
                errmessage = e.message
                import socket
                # try to format re-packaged get-address-info exceptions
                # into a nice message (this will be the normal exception
                # you see if you aren't connected to the internet)
                try:
                    errmessage = str(e.message[1])
                except Exception as e:
                    pass
                if attempts_remaining:
                    logger.warning('connection error: %s, retrying...', errmessage)
                else:
                    logger.error('connection error: %s', errmessage)
                    raise
            except requests.exceptions.Timeout as e:
                if attempts_remaining:
                    logger.warning('request timed out: %s, retrying...', e.message)
                else:
                    logger.error('request timed out: %s', e.message)
                    raise
            import time
            time.sleep(delay)
            delay = delay * 1.6 + 0.1
    return wrapped

def _returnRequestError(fn):
    ''' Decorator that captures requests.exceptions.RequestException errors
        and returns them as an error message. If no error occurs the reture
        value of the wrapped function is returned (normally None). '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            return "server returned status %s: %s" % (e.response.status_code, e.message)
    return wrapped

def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # if yotta is being run noninteractively, then we never retry, but we
        # do call auth.authorizeUser, so that a login URL can be displayed:
        interactive = globalconf.get('interactive')
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.unauthorized: #pylint: disable=no-member
                logger.debug('%s unauthorised', fn)
                # any provider is sufficient for registry auth
                auth.authorizeUser(provider=None, interactive=interactive)
                if interactive:
                    logger.debug('retrying after authentication...')
                    return fn(*args, **kwargs)
            raise
    return wrapped

def _friendlyAuthError(fn):
    ''' Decorator to print a friendly you-are-not-authorised message. Use
        **outside** the _handleAuth decorator to only print the message after
        the user has been given a chance to login. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.unauthorized: #pylint: disable=no-member
                logger.error('insufficient permission')
            else:
                logger.error('server returned status %s: %s', e.response.status_code, e.response.text)
            raise
    return wrapped

def _raiseUnavailableFor401(message):
    ''' Returns a decorator to swallow a requests exception for modules that
        are not accessible without logging in, and turn it into an Unavailable
        exception.
    '''
    def __raiseUnavailableFor401(fn):
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.unauthorized:
                    raise access_common.Unavailable(message)
                else:
                    raise
        return wrapped
    return __raiseUnavailableFor401

def _swallowRequestExceptions(fail_return=None):
    def __swallowRequestExceptions(fn):
        ''' Decorator to swallow known exceptions: use with _friendlyAuthError,
            returns non-None if an exception occurred
        '''
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                return fail_return
        return wrapped
    return __swallowRequestExceptions

def _getPrivateRegistryKey():
    if 'YOTTA_PRIVATE_REGISTRY_API_KEY' in os.environ:
        return os.environ['YOTTA_PRIVATE_REGISTRY_API_KEY']
    return None

@_retryConnectionErrors
def _listVersions(namespace, name):
    sources = _getSources()

    registry_urls = [s['url'] for s in sources if 'type' in s and s['type'] == 'registry']

    # look in the public registry last
    registry_urls.append(Registry_Base_URL)

    versions = []

    for registry in registry_urls:
        # list versions of the package:
        url = '%s/%s/%s/versions' % (
            registry,
            namespace,
            name
        )

        request_headers = _headersForRegistry(registry)

        logger.debug("GET %s, %s", url, request_headers)
        response = requests.get(url, headers=request_headers)

        if response.status_code == 404:
            continue

        # raise any other HTTP errors
        response.raise_for_status()

        for x in ordered_json.loads(response.text):
            rtv = RegistryThingVersion(x, namespace, name, registry=registry)
            if not rtv in versions:
                versions.append(rtv)

    if not len(versions):
        raise access_common.Unavailable(
            ('%s does not exist in the %s registry. '+
            'Check that the name is correct, and that it has been published.') % (name, namespace)
        )

    return versions

def _tarballURL(namespace, name, version, registry=None):
    registry = registry or Registry_Base_URL
    return '%s/%s/%s/versions/%s/tarball' % (
        registry, namespace, name, version
    )

@_retryConnectionErrors
@_raiseUnavailableFor401("dependency is not available without logging in")
@_friendlyAuthError
@_handleAuth
def _getTarball(url, directory, sha256):
    logger.debug('registry: get: %s' % url)

    if not sha256:
        logger.warn('tarball %s has no hash to check' % url)

    try:
        access_common.unpackFromCache(sha256, directory)
    except KeyError as e:
        # figure out which registry we're fetching this tarball from (if any)
        # and add appropriate headers
        registry = Registry_Base_URL

        for source in _getSources():
            if ('type' in source and source['type'] == 'registry' and
                 'url' in source and url.startswith(source['url'])):
                registry = source['url']
                break

        request_headers = _headersForRegistry(registry)

        logger.debug('GET %s, %s', url, request_headers)
        response = requests.get(url, headers=request_headers, allow_redirects=True, stream=True)
        response.raise_for_status()

        access_common.unpackTarballStream(
                    stream = response,
            into_directory = directory,
                      hash = {'sha256':sha256},
                 cache_key = sha256
        )

def _getSources():
    sources = settings.get('sources')
    if sources is None:
        sources = []
    return sources

def _isPublicRegistry(registry):
    return (registry is None) or (registry == Registry_Base_URL)

def _friendlyRegistryName(registry):
    if registry == Registry_Base_URL:
        return 'the public module registry'
    else:
        return registry

def _getPrivateKey(registry):
    if _isPublicRegistry(registry):
        return settings.getProperty('keys', 'private')
    else:
        for s in _getSources():
            if _sourceMatches(s, registry):
                if 'keys' in s and s['keys'] and 'private' in s['keys']:
                    return s['keys']['private']
        return None

def _sourceMatches(source, registry):
    return ('type' in source and source['type'] == 'registry' and
             'url' in source and source['url'] == registry)

def _generateAndSaveKeys(registry=None):
    registry = registry or Registry_Base_URL
    k = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    privatekey_pem = k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )

    pubkey_pem = k.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    if _isPublicRegistry(registry):
        settings.setProperty('keys', 'private', privatekey_pem.decode('ascii'))
        settings.setProperty('keys', 'public', pubkey_pem.decode('ascii'))
    else:
        sources = _getSources()
        keys = None
        for s in sources:
            if _sourceMatches(s, registry):
                if not 'keys' in s:
                    s['keys'] = dict()
                keys = s['keys']
                break
        if keys is None:
            keys = dict()
            sources.append({
               'type':'registry',
                'url':registry,
               'keys':keys
            })
        keys['private'] = privatekey_pem.decode('ascii')
        keys['public']  = pubkey_pem.decode('ascii')
        settings.set('sources', sources)
    return pubkey_pem, privatekey_pem

def _getPrivateKeyObject(registry=None):
    registry = registry or Registry_Base_URL
    privatekey_pem = _getPrivateKey(registry)
    if not privatekey_pem:
        pubkey_pem, privatekey_pem = _generateAndSaveKeys(registry)
    else:
        # settings are unicode, we should be able to safely decode to ascii for
        # the key though, as it will either be hex or PEM encoded:
        privatekey_pem = privatekey_pem.encode('ascii')
    # if the key doesn't look like PEM, it might be hex-encided-DER (which we
    # used historically), so try loading that:
    if b'-----BEGIN PRIVATE KEY-----' in privatekey_pem:
        return serialization.load_pem_private_key(
            privatekey_pem, None, default_backend()
        )
    else:
        privatekey_der = binascii.unhexlify(privatekey_pem)
        return serialization.load_der_private_key(
            privatekey_der, None, default_backend()
        )

_yotta_version = None
def _getYottaVersion():
    global _yotta_version
    if _yotta_version is None:
        import pkg_resources
        _yotta_version = pkg_resources.require("yotta")[0].version
    return _yotta_version

def _getYottaClientUUID():
    import uuid
    current_uuid = settings.get('uuid')
    if current_uuid is None:
        current_uuid = u'%s' % uuid.uuid4()
        settings.set('uuid', current_uuid)
    return current_uuid

def _headersForRegistry(registry):
    registry = registry or Registry_Base_URL
    auth_token = generate_jwt_token(_getPrivateKeyObject(registry), registry)
    r = {
        'Authorization': 'Bearer %s' % auth_token,
        'X-Yotta-Client-Version': _getYottaVersion(),
        'X-Yotta-Client-ID': _getYottaClientUUID()
    }
    if registry == Registry_Base_URL:
        return r
    for s in _getSources():
        if _sourceMatches(s, registry):
            if 'apikey' in s:
                r['X-Api-Key'] = s['apikey']
                break
    return r

# API
class RegistryThingVersion(access_common.RemoteVersion):
    def __init__(self, data, namespace, name, registry=None):
        logger.debug('RegistryThingVersion %s/%s data: %s' % (namespace, name, data))
        version = data['version']
        self.namespace = namespace
        self.name      = name
        self.version   = version
        if 'hash' in data and 'sha256' in data['hash']:
            self.sha256 = data['hash']['sha256']
        else:
            self.sha256 = None
        url = _tarballURL(self.namespace, self.name, version, registry)
        super(RegistryThingVersion, self).__init__(
            version, url, name=name, friendly_source=_friendlyRegistryName(registry)
        )

    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory, self.sha256)

class RegistryThing(access_common.RemoteComponent):
    def __init__(self, name, version_spec, namespace):
        self.name = name
        self.spec = version_spec
        self.namespace = namespace

    @classmethod
    def createFromSource(cls, vs, name, registry):
        ''' returns a registry component for anything that's a valid package
            name (this does not guarantee that the component actually exists in
            the registry: use availableVersions() for that).
        '''
        # we deliberately allow only lowercase, hyphen, and (unfortunately)
        # numbers in package names, to reduce the possibility of confusingly
        # similar names: if the name doesn't match this then escalate to make
        # the user fix it
        name_match = re.match('^([a-z0-9-]+)$', name)
        if not name_match:
            raise ValueError('Dependency name "%s" is not valid (must contain only lowercase letters, hyphen, and numbers)' % name)
        assert(vs.semantic_spec)
        return RegistryThing(name, vs.semantic_spec, registry)

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        ''' return a list of Version objects, each able to retrieve a tarball '''
        return _listVersions(self.namespace, self.name)

    def tipVersion(self):
        raise NotImplementedError()

    @classmethod
    def remoteType(cls):
        return 'registry'

@_swallowRequestExceptions(fail_return="request exception occurred")
@_retryConnectionErrors
@_friendlyAuthError
@_handleAuth
def publish(namespace, name, version, description_file, tar_file, readme_file,
            readme_file_ext, registry=None):
    ''' Publish a tarblob to the registry, if the request fails, an exception
        is raised, which either triggers re-authentication, or is turned into a
        return value by the decorators. (If successful, the decorated function
        returns None)
    '''
    registry = registry or Registry_Base_URL

    url = '%s/%s/%s/versions/%s' % (
        registry,
        namespace,
        name,
        version
    )

    if readme_file_ext == '.md':
        readme_section_name = 'readme.md'
    elif readme_file_ext == '':
        readme_section_name = 'readme'
    else:
        raise ValueError('unsupported readme type: "%s"' % readme_file_ext)

    # description file is in place as text (so read it), tar file is a file
    body = OrderedDict([('metadata', (None, description_file.read(),'application/json')),
                        ('tarball',('tarball', tar_file)),
                        (readme_section_name, (readme_section_name, readme_file))])

    headers = _headersForRegistry(registry)

    response = requests.put(url, headers=headers, files=body)
    response.raise_for_status()

    return None

@_swallowRequestExceptions(fail_return="request exception occurred")
@_retryConnectionErrors
@_friendlyAuthError
@_handleAuth
def unpublish(namespace, name, version, registry=None):
    ''' Try to unpublish a recently published version. Return any errors that
        occur.
    '''
    registry = registry or Registry_Base_URL

    url = '%s/%s/%s/versions/%s' % (
        registry,
        namespace,
        name,
        version
    )

    headers = _headersForRegistry(registry)
    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    return None

@_swallowRequestExceptions(fail_return=None)
@_retryConnectionErrors
@_friendlyAuthError
@_handleAuth
def listOwners(namespace, name, registry=None):
    ''' List the owners of a module or target (owners are the people with
        permission to publish versions and add/remove the owners).
    '''
    registry = registry or Registry_Base_URL

    url = '%s/%s/%s/owners' % (
        registry,
        namespace,
        name
    )

    request_headers = _headersForRegistry(registry)

    response = requests.get(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return None

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()

    return ordered_json.loads(response.text)

@_swallowRequestExceptions(fail_return=None)
@_retryConnectionErrors
@_friendlyAuthError
@_handleAuth
def addOwner(namespace, name, owner, registry=None):
    ''' Add an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners).
    '''
    registry = registry or Registry_Base_URL

    url = '%s/%s/%s/owners/%s' % (
        registry,
        namespace,
        name,
        owner
    )

    request_headers = _headersForRegistry(registry)

    response = requests.put(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()

    return True


@_swallowRequestExceptions(fail_return=None)
@_retryConnectionErrors
@_friendlyAuthError
@_handleAuth
def removeOwner(namespace, name, owner, registry=None):
    ''' Remove an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners).
    '''
    registry = registry or Registry_Base_URL

    url = '%s/%s/%s/owners/%s' % (
        registry,
        namespace,
        name,
        owner
    )

    request_headers = _headersForRegistry(registry)

    response = requests.delete(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()

    return True

@_retryConnectionErrors
def whoami(registry=None):
    registry = registry or Registry_Base_URL
    url = '%s/users/me' % (
        registry
    )

    request_headers = _headersForRegistry(registry)

    logger.debug('test login...')
    response = requests.get(url, headers=request_headers)
    if response.status_code == 401:
        # not logged in
        return None
    elif response.status_code != 200:
        logger.error('error getting user information: %s', response.error)
        return None
    return ', '.join(ordered_json.loads(response.text).get('primary_emails', {}).values())

@_retryConnectionErrors
def search(query='', keywords=[], registry=None):
    ''' generator of objects returned by the search endpoint (both modules and
        targets).

        Query is a full-text search (description, name, keywords), keywords
        search only the module/target description keywords lists.

        If both parameters are specified the search is the intersection of the
        two queries.
    '''
    registry = registry or Registry_Base_URL

    url = '%s/search' % registry

    headers = _headersForRegistry(registry)

    params = {
         'skip': 0,
        'limit': 50
    }
    if len(query):
        params['query'] = query
    if len(keywords):
        params['keywords[]'] = keywords

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        objects = ordered_json.loads(response.text)
        if len(objects):
            for o in objects:
                yield o
            params['skip'] += params['limit']
        else:
            break


def deauthorize(registry=None):
    registry = registry or Registry_Base_URL
    if _isPublicRegistry(registry):
        if settings.get('keys'):
            settings.set('keys', dict())
    else:
        sources = [s for s in _getSources() if not _sourceMatches(s, registry)]
        settings.set('sources', sources)

def setAPIKey(registry, api_key):
    ''' Set the api key for accessing a registry. This is only necessary for
        development/test registries.
    '''
    if (registry is None) or (registry == Registry_Base_URL):
        return
    sources = _getSources()
    source = None
    for s in sources:
        if _sourceMatches(s, registry):
            source = s
    if source is None:
        source = {
           'type':'registry',
            'url':registry,
        }
        sources.append(source)
    source['apikey'] = api_key
    settings.set('sources', sources)


def getPublicKey(registry=None):
    ''' Return the user's public key (generating and saving a new key pair if necessary) '''
    registry = registry or Registry_Base_URL
    pubkey_pem = None
    if _isPublicRegistry(registry):
        pubkey_pem = settings.getProperty('keys', 'public')
    else:
        for s in _getSources():
            if _sourceMatches(s, registry):
                if 'keys' in s and s['keys'] and 'public' in s['keys']:
                    pubkey_pem = s['keys']['public']
                    break
    if not pubkey_pem:
        pubkey_pem, privatekey_pem = _generateAndSaveKeys()
    else:
        # settings are unicode, we should be able to safely decode to ascii for
        # the key though, as it will either be hex or PEM encoded:
        pubkey_pem = pubkey_pem.encode('ascii')
    # if the key doesn't look like PEM, it might be hex-encided-DER (which we
    # used historically), so try loading that:
    if b'-----BEGIN PUBLIC KEY-----' in pubkey_pem:
        pubkey = serialization.load_pem_public_key(pubkey_pem, default_backend())
    else:
        pubkey_der = binascii.unhexlify(pubkey_pem)
        pubkey = serialization.load_der_public_key(pubkey_der, default_backend())
    return _pubkeyWireFormat(pubkey)

@_retryConnectionErrors
def getAuthData(registry=None):
    ''' Poll the registry to get the result of a completed authentication
        (which, depending on the authentication the user chose or was directed
        to, will include a github or other access token)
    '''
    registry = registry or Registry_Base_URL
    url = '%s/tokens' % (
        registry
    )

    request_headers = _headersForRegistry(registry)

    logger.debug('poll for tokens... %s', request_headers)

    try:
        response = requests.get(url, headers=request_headers)
    except requests.RequestException as e:
        logger.debug(str(e))
        return None

    if response.status_code == requests.codes.unauthorized: #pylint: disable=no-member
        logger.debug('Unauthorised')
        return None
    elif response.status_code == requests.codes.not_found: #pylint: disable=no-member
        logger.debug('Not Found')
        return None

    body = response.text
    logger.debug('auth data response: %s' % body);
    r = {}

    parsed_response = ordered_json.loads(body)

    if 'error' in parsed_response:
        raise AuthError(parsed_response['error'])

    for token in parsed_response:
        if 'provider' in token and token['provider'] and 'accessToken' in token:
            r[token['provider']] = token['accessToken']
            break

    logger.debug('parsed auth tokens %s' % r);
    return r

def getLoginURL(provider=None, registry=None):
    registry = registry or Registry_Base_URL
    if provider:
        query = ('?provider=%s' % provider)
    else:
        query = ''
    if not _isPublicRegistry(registry):
        if not len(query):
            query = '?'
        query += '&private=1'
    return  Website_Base_URL + '/' + query + '#login/' + getPublicKey(registry)

