# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import tarfile
import logging
import os
import hashlib
import tempfile
import shutil
import sys
import functools
import random
import errno

# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils
# folders, , where yotta stores things, internal
import folders

logger = logging.getLogger('access')
cache_logger = logging.getLogger('cache')

# arbitrary default setting for download caching. Later maybe this can be a
# setting:
Max_Cached_Modules = 100

class AccessException(Exception):
    pass


class Unavailable(AccessException):
    pass


class TargetUnavailable(Unavailable):
    pass


class SpecificationNotMet(AccessException):
    pass


class RemoteVersion(version.Version):
    def __init__(self, version_string, url=None, name='unknown', friendly_source='unknown', friendly_version=None):
        self.name = name
        self.version_string = version_string
        self.friendly_version = friendly_version or version_string
        self.friendly_source = friendly_source
        super(RemoteVersion, self).__init__(version_string, url)

    def unpackInto(self, directory):
        raise NotImplementedError

    def __repr__(self):
        return u'%s@%s from %s' % (self.name, self.friendly_version, self.friendly_source)
    def __str__(self):
        return self.__unicode__()
    def __unicode__(self):
        return self.__repr__()

class RemoteComponent(object):

    @classmethod
    def createFromSource(cls, url, name=None):
        raise NotImplementedError

    def versionSpec(self):
        raise NotImplementedError

    def availableVersions(self):
        raise NotImplementedError

    def tipVersion(self):
        raise NotImplementedError

    @classmethod
    def remoteType(cls):
        raise NotImplementedError


def _openExclusively(name):
    # in python >=3.3, there's the handy 'x' flag, otherwise we have to use
    # fdopen:
    # (tarfile has problems with fdopened files on python 3.3, so this works
    # around that bug too)
    if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
        return open(name, 'bx+')
    else:
        fd = os.open(name, os.O_CREAT | os.O_EXCL |
                           os.O_RDWR | getattr(os, "O_BINARY", 0))
        return os.fdopen(fd, 'rb+')


def pruneCache():
    ''' Prune the cache '''
    cache_dir = folders.cacheDirectory()
    def fullpath(f):
        return os.path.join(cache_dir, f)
    # ensure cache exists
    fsutils.mkDirP(cache_dir)
    for f in sorted(
            [f for f in os.listdir(cache_dir) if os.path.isfile(fullpath(f))],
            key = lambda f: os.stat(fullpath(f)).st_mtime
        )[Max_Cached_Modules:]:
        cache_logger.debug('cleaning up cache file %s', f)
        fsutils.rmF(fullpath(f))
    cache_logger.debug('cache pruned to %s items', Max_Cached_Modules)

def sometimesPruneCache(p):
    ''' return decorator to prune cache after calling fn with a probability of p'''
    def decorator(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            r = fn(*args, **kwargs)
            if random.random() < p:
                pruneCache()
            return r
        return wrapped
    return decorator

def unpackFrom(tar_file_path, to_directory):
    # first unpack into a sibling directory of the specified directory, and
    # then move it into place.

    # we expect our tarballs to contain a single top-level directory. We strip
    # off this name as we extract to minimise the path length

    into_parent_dir = os.path.dirname(to_directory)
    fsutils.mkDirP(into_parent_dir)
    temp_directory = tempfile.mkdtemp(dir=into_parent_dir)

    with tarfile.open(tar_file_path) as tf:
        strip_dirname = ''
        # get the extraction directory name from the first part of the
        # extraction paths: it should be the same for all members of
        # the archive
        for m in tf.getmembers():
            split_path = fsutils.fullySplitPath(m.name)
            if os.path.isabs(m.name) or '..' in split_path:
                raise ValueError('archive uses invalid paths')
            if not strip_dirname:
                if len(split_path) != 1 or not len(split_path[0]):
                    raise ValueError('archive does not appear to contain a single module')
                strip_dirname = split_path[0]
                continue
            else:
                if split_path[0] != strip_dirname:
                    raise ValueError('archive does not appear to contain a single module')
            m.name = os.path.join(*split_path[1:])
            tf.extract(m, path=temp_directory)
    shutil.move(temp_directory, to_directory)
    logger.debug('extraction complete %s', to_directory)

def unpackFromCache(cache_key, to_directory):
    ''' If the specified cache key exists, unpack the tarball into the
        specified directory, otherwise raise KeyError.
    '''
    if cache_key is None:
        raise KeyError('"None" is never in cache')
    cache_dir = folders.cacheDirectory()
    fsutils.mkDirP(cache_dir)
    path = os.path.join(cache_dir, cache_key)
    try:
        unpackFrom(path, to_directory)
        cache_logger.debug('unpacked %s from cache into %s', cache_key, to_directory)
        return
    except IOError as e:
        if e.errno == errno.ENOENT:
            cache_logger.debug('%s not in cache', cache_key)
            raise KeyError('not in cache')

def downloadToCache(stream, hashinfo={}, cache_key=None):
    ''' Download the specified stream to a temporary cache directory, and
        return (path to the downloaded, cache key).
        If cache_key is None, then a cache key will be generated and returned,
        but you will probably want to remove the cache file yourself (this is
        safe).
    '''
    hash_name  = None
    hash_value = None
    m = None

    if len(hashinfo):
        # check for hashes in preferred order. Currently this is just sha256
        # (which the registry uses). Initial investigations suggest that github
        # doesn't return a header with the hash of the file being downloaded.
        for h in ('sha256',):
            if h in hashinfo:
                hash_name  = h
                hash_value = hashinfo[h]
                m = getattr(hashlib, h)()
                break
        if not hash_name:
            logger.warning('could not find supported hash type in %s', hashinfo)

    if cache_key is None:
        cache_key = '%032x' % random.getrandbits(256)

    cache_dir = folders.cacheDirectory()
    fsutils.mkDirP(cache_dir)
    download_fname = os.path.join(cache_dir, cache_key)

    with _openExclusively(download_fname) as f:
        f.seek(0)
        for chunk in stream.iter_content(1024):
            f.write(chunk)
            if hash_name:
                m.update(chunk)

        if hash_name:
            calculated_hash = m.hexdigest()
            logger.debug(
                'calculated %s hash: %s check against: %s' % (
                    hash_name, calculated_hash, hash_value
                )
            )
            if hash_value and (hash_value != calculated_hash):
                raise Exception('Hash verification failed.')
        logger.debug('wrote tarfile of size: %s to %s', f.tell(), download_fname)
        f.truncate()

    return (download_fname, cache_key)

@sometimesPruneCache(0.05)
def unpackTarballStream(stream, into_directory, hash={}, cache_key=None):
    ''' Unpack a responses stream that contains a tarball into a directory. If
        a hash is provided, then it will be used as a cache key (for future
        requests you can try to retrieve the key value from the cache first,
        before making the request)
    '''

    download_fname, cache_key = downloadToCache(stream, hash, cache_key)
    unpackFromCache(cache_key, into_directory)

    # if we didn't provide a cache key, there's no point in storing the cache
    if cache_key is None:
        fsutils.rmF(download_fname)


