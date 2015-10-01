# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import re
import functools

# requests, apache2
import requests
# PyGithub, LGPL, Python library for Github API v3, pip install PyGithub
import github
from github import Github

# settings, , load and save settings, internal
import settings
# access_common, , things shared between different component access modules, internal
import access_common
# auth, , authenticate users, internal
import auth
# globalconf, share global arguments between modules, internal
import yotta.lib.globalconf as globalconf

# Constants
_github_url = 'https://api.github.com'

logger = logging.getLogger('access')

## NOTE
## It may be tempting to re-use resources (like Github instances) between
## functions below, however it must be possible to call these functions in
## parallel, so they must not share resources that are stateful and do not
## maintain their state in a threadsafe way

# Internal functions

def _userAuthedWithGithub():
    return settings.getProperty('github', 'authtoken')

def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # if yotta is being run noninteractively, then we never retry, but we
        # do call auth.authorizeUser, so that a login URL can be displayed:
        interactive = globalconf.get('interactive')
        if not interactive:
            try:
                return fn(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    auth.authorizeUser(provider='github', interactive=False)
                raise
            except github.BadCredentialsException:
                logger.debug("github: bad credentials")
                auth.authorizeUser(provider='github', interactive=False)
                raise
            except github.UnknownObjectException:
                logger.debug("github: unknown object")
                # some endpoints return 404 if the user doesn't have access:
                if not _userAuthedWithGithub():
                    logger.info('failed to fetch Github object, try re-authing...')
                    auth.authorizeUser(provider='github', interactive=False)
                raise
        else:
            try:
                return fn(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    auth.authorizeUser(provider='github')
                    return fn(*args, **kwargs)
                raise
            except github.BadCredentialsException:
                logger.debug("github: bad credentials")
                auth.authorizeUser(provider='github')
                logger.debug('trying with authtoken: %s', settings.getProperty('github', 'authtoken'))
                return fn(*args, **kwargs)
            except github.UnknownObjectException:
                logger.debug("github: unknown object")
                # some endpoints return 404 if the user doesn't have access, maybe
                # it would be better to prompt for another username and password,
                # and store multiple tokens that we can try for each request....
                # but for now we assume that if the user is logged in then a 404
                # really is a 404
                if not _userAuthedWithGithub():
                    logger.info('failed to fetch Github object, re-trying with authentication...')
                    auth.authorizeUser(provider='github')
                    return fn(*args, **kwargs)
                raise
    return wrapped

@_handleAuth
def _getTags(repo):
    ''' return a dictionary of {tag: tarball_url}'''
    logger.debug('get tags for %s', repo)
    g = Github(settings.getProperty('github', 'authtoken'))
    repo = g.get_repo(repo)
    tags = repo.get_tags()
    logger.debug('tags for %s: %s', repo, [t.name for t in tags])
    return {t.name: t.tarball_url for t in tags}

def _tarballUrlForBranch(repo, branchname=None):
    r = repo.url + u'/tarball'
    if branchname:
        r += '/' + branchname
    return r

@_handleAuth
def _getBranchHeads(repo):
    g = Github(settings.getProperty('github', 'authtoken'))
    repo = g.get_repo(repo)
    branches = repo.get_branches()

    return {b.name:_tarballUrlForBranch(repo, b.name) for b in branches}


@_handleAuth
def _getTipArchiveURL(repo):
    ''' return a string containing a tarball url '''
    g = Github(settings.getProperty('github', 'authtoken'))
    repo = g.get_repo(repo)
    return repo.get_archive_link('tarball')


@_handleAuth
def _getTarball(url, into_directory):
    '''unpack the specified tarball url into the specified directory'''
    tok = settings.getProperty('github', 'authtoken')
    headers = {}
    if tok is not None:
        headers['Authorization'] = 'token ' + str(tok)

    logger.debug('GET %s', url)
    response = requests.get(url, allow_redirects=True, stream=True, headers=headers)
    response.raise_for_status()

    logger.debug('getting file: %s', url)
    # TODO: there's an MD5 in the response headers, verify it

    access_common.unpackTarballStream(response, into_directory)

# API
def deauthorize():
    if settings.getProperty('github', 'authtoken'):
        settings.setProperty('github', 'authtoken', '')

class GithubComponentVersion(access_common.RemoteVersion):
    def __init__(self, semver, tag, url, name):
        self.tag = tag
        github_spec = re.search('/(repos|codeload.github.com)/([^/]*/[^/]*)/', url).group(2)
        super(GithubComponentVersion, self).__init__(
            semver, url, name=name, friendly_version=(semver or tag), friendly_source=('GitHub %s' % github_spec)
        )

    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory)

class GithubComponent(access_common.RemoteComponent):
    def __init__(self, repo, tag_or_branch=None, semantic_spec=None, name=None):
        logging.debug('create Github component for repo:%s version spec:%s' % (repo, semantic_spec or tag_or_branch))
        self.repo = repo
        self.spec = semantic_spec
        self.tag_or_branch = tag_or_branch
        self.tags = None
        self.name = name

    @classmethod
    def createFromSource(cls, vs, name=None):
        ''' returns a github component for any github url (including
            git+ssh:// git+http:// etc. or None if this is not a Github URL.
            For all of these we use the github api to grab a tarball, because
            that's faster.

            Normally version will be empty, unless the original url was of the
            form: 'owner/repo @version' or 'url://...#version', which can be used
            to grab a particular tagged version.

            (Note that for github components we ignore the component name - it
             doesn't have to match the github module name)
        '''
        return GithubComponent(vs.location, vs.spec, vs.semantic_spec, name)

    def versionSpec(self):
        return self.spec

    def tagOrBranchSpec(self):
        return self.tag_or_branch

    def _getTags(self):
        if self.tags is None:
            try:
                self.tags = _getTags(self.repo).items()
            except github.UnknownObjectException as e:
                raise access_common.Unavailable(
                    'could not locate github component "%s", either the name is misspelt, you do not have access to it, or it does not exist' % self.repo
                )
        return self.tags

    def availableVersions(self):
        ''' return a list of Version objects, each with a tarball URL set '''
        r = []
        for t in self._getTags():
            logger.debug("available version tag: %s", t)
            # ignore empty tags:
            if not len(t[0].strip()):
                continue
            try:
                r.append(GithubComponentVersion(t[0], t[0], url=t[1], name=self.name))
            except ValueError:
                logger.debug('invalid version tag: %s', t)

        return r

    def availableTags(self):
        ''' return a list of GithubComponentVersion objects for all tags
        '''
        return [GithubComponentVersion('', t[0], t[1], self.name) for t in self._getTags()]

    def availableBranches(self):
        ''' return a list of GithubComponentVersion objects for the tip of each branch
        '''
        return [
            GithubComponentVersion('', b[0], b[1], self.name) for b in _getBranchHeads(self.repo).items()
        ]

    def tipVersion(self):
        return GithubComponentVersion('', '', _getTipArchiveURL(self.repo), self.name)

    @classmethod
    def remoteType(cls):
        return 'github'
