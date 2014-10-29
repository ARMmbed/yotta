# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import json
import getpass
import os
import re
import functools
import datetime
import time
import sys

# settings, , load and save settings, internal
import settings
# version, , represent versions and specifications, internal
import version
# access_common, , things shared between different component access modules, internal
import access_common
# connection_pool, , shared connection pool, internal
import connection_pool
# Registry Access, , access packages in the registry, internal
import registry_access

# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Resource, BasicAuth, Connection, request

# PyGithub, LGPL, Python library for Github API v3, pip install PyGithub
import github
from github import Github

# Constants
_github_url = 'https://api.github.com'

logger = logging.getLogger('access')

## NOTE
## It may be tempting to re-use resources (like Github instances) between
## functions below, however it must be possible to call these functions in
## parallel, so they must not share resources that are stateful and do not
## maintain their state in a threadsafe way

# Internal functions

def _userAuthorized():
    return settings.getProperty('github', 'authtoken')
 
def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except github.BadCredentialsException:
            authorizeUser()
            logger.debug('trying with authtoken:', settings.getProperty('github', 'authtoken'))
            return fn(*args, **kwargs)
        except github.UnknownObjectException:
            # some endpoints return 404 if the user doesn't have access, maybe
            # it would be better to prompt for another username and password,
            # and store multiple tokens that we can try for each request....
            # but for now we assume that if the user is logged in then a 404
            # really is a 404
            if not _userAuthorized():
                logger.info('failed to fetch Github object, re-trying with authentication...')
                authorizeUser()
                return fn(*args, **kwargs)
            else:
                raise
    return wrapped

@_handleAuth
def _getTags(repo):
    ''' return a dictionary of {tag: tarball_url}'''
    g = Github(settings.getProperty('github', 'authtoken'))
    logger.info('get versions for ' + repo)
    repo = g.get_repo(repo)
    tags = repo.get_tags()
    return {t.name: t.tarball_url for t in tags}

@_handleAuth
def _getTipArchiveURL(repo):
    ''' return a string containing a tarball url '''
    g = Github(settings.getProperty('github', 'authtoken'))
    repo = g.get_repo(repo)
    return repo.get_archive_link('tarball')

    
@_handleAuth
def _getTarball(url, into_directory):
    '''unpack the specified tarball url into the specified directory'''
    resource = Resource(url, pool=connection_pool.getPool(), follow_redirect=True)
    response = resource.get(
        headers = {'Authorization': 'token ' + settings.getProperty('github', 'authtoken')}, 
    )
    logger.debug('getting file: %s', url)
    # TODO: there's an MD5 in the response headers, verify it
    access_common.unpackTarballStream(response.body_stream(), into_directory)

def _pollForAuth():
    tokens = registry_access.getAuthData()
    if tokens and 'github' in tokens:
        settings.setProperty('github', 'authtoken', tokens['github'])
        return True
    return False


# API
def authorizeUser():
    # poll once with any existing public key, just in case a previous login
    # attempt was interrupted after it completed
    if _pollForAuth():
        return

    raw_input('''
You need to log in with Github. Press enter to continue.

(Your browser will open to complete login.)''')

    registry_access.openBrowserLogin(provider='github')

    sys.stdout.write('waiting for response...')
    sys.stdout.flush()

    poll_start = datetime.datetime.utcnow()
    while datetime.datetime.utcnow() - poll_start < datetime.timedelta(minutes=5):
        time.sleep(5)
        sys.stdout.write('.')
        sys.stdout.flush()
        if _pollForAuth():
            sys.stdout.write('\n')
            return

    raise Exception('Login timed out: please try again.')

def deauthorize():
    if settings.getProperty('github', 'authtoken'):
        settings.setProperty('github', 'authtoken', '')

class GithubComponentVersion(access_common.RemoteVersion):
    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory)

class GithubComponent(access_common.RemoteComponent):
    def __init__(self, repo, version_spec=''):
        logging.debug('create Github component for repo:%s version spec:%s' % (repo, version_spec))
        self.repo = repo
        self.spec = version.Spec(version_spec)
    
    @classmethod
    def createFromNameAndSpec(cls, url, name=None):    
        ''' returns a github component for any github url (including
            git+ssh:// git+http:// etc. or None if this is not a Github URL.
            For all of these we use the github api to grab a tarball, because
            that's faster.

            Normally version will be empty, unless the original url was of the
            form: 'owner/repo @version' or 'url://...#version', which can be used
            to grab a particular tagged version.

            (Note that for github components we ignore the package name, and
             just test to see if the "spec" looks like one of the supported URI
             schemes)
        '''
        # owner/package [@1.2.3] format
        url = url.strip()
        m = re.match('([^:/\s]*/[^:/\s]*) *@?([><=.0-9a-zA-Z\*-]*)', url)
        if m:
            return GithubComponent(*m.groups())
        # something://[anything.|anything@]github.com/owner/package[#1.2.3] format
        m = re.match('(?:[^:/]*://)?(?:[^:/]*\.|[^:/]*@)?github\.com[:/]([^/]*/[^/#]*)#?([><=.0-9a-zA-Z\*-]*)', url)
        if m:
            repo = m.group(1)
            spec = m.group(2)
            if repo.endswith('.git'):
                repo = repo[:-4]
            return GithubComponent(repo, spec)
        return None

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        ''' return a list of Version objects, each with a tarball URL set '''
        try:
            return [GithubComponentVersion(t[0], url=t[1]) for t in _getTags(self.repo).iteritems()]
        except github.UnknownObjectException, e:
            raise access_common.ComponentUnavailable(
                'could not locate github component "%s", either the name is misspelt, you do not have access to it, or it does not exist' % self.repo
            )

    def tipVersion(self):
        return GithubComponentVersion('', _getTipArchiveURL(self.repo))
    
    @classmethod
    def remoteType(cls):
        return 'github'
