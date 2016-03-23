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
import functools
import random
import errno

# version, , represent versions and specifications, internal
from yotta.lib import version
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# folders, , where yotta stores things, internal
from yotta.lib import folders
# Ordered JSON, , read & write json, internal
from yotta.lib import ordered_json
# settings, , load and save settings, internal
from yotta.lib import settings

logger = logging.getLogger('access')
cache_logger = logging.getLogger('cache')

class AccessException(Exception):
    pass


class Unavailable(AccessException):
    pass


class TargetUnavailable(Unavailable):
    pass


class SpecificationNotMet(AccessException):
    pass

class NotInCache(KeyError):
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
        import sys
        # in python 3 __str__ must return a string (i.e. unicode), in
        # python 2, it must not return unicode, so:
        if sys.version_info[0] >= 3:
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf8')
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

_max_cached_modules = None
def getMaxCachedModules():
    global _max_cached_modules
    if _max_cached_modules is None:
        _max_cached_modules = settings.get('maxCachedModules')
        if _max_cached_modules is None:
            # arbitrary default value
            _max_cached_modules = 400
    return _max_cached_modules

def _encodeCacheKey(cache_key):
    import sys
    # if we're under python 2, and cache_key is unicode (it will be, but check
    # to be defensive), encode it as ascii. This prevents coersion errors if
    # the username has unicode charaters in it.
    if sys.version_info[0] < 3 and isinstance(cache_key, unicode):
        return cache_key.encode('ascii')
    return cache_key

def pruneCache():
    ''' Prune the cache '''
    cache_dir = folders.cacheDirectory()
    def fullpath(f):
        return os.path.join(cache_dir, f)
    def getMTimeSafe(f):
        # it's possible that another process removed the file before we stat
        # it, handle this gracefully
        try:
            return os.stat(f).st_mtime
        except FileNotFoundError:
            import time
            return time.clock()
    # ensure cache exists
    fsutils.mkDirP(cache_dir)
    max_cached_modules = getMaxCachedModules()
    for f in sorted(
            [f for f in os.listdir(cache_dir) if
                os.path.isfile(fullpath(f)) and not f.endswith('.json') and not f.endswith('.locked')
            ],
            key = lambda f: getMTimeSafe(fullpath(f)),
            reverse = True
        )[max_cached_modules:]:
        cache_logger.debug('cleaning up cache file %s', f)
        removeFromCache(f)
    cache_logger.debug('cache pruned to %s items', max_cached_modules)

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
    try:
        with tarfile.open(tar_file_path) as tf:
            strip_dirname = ''
            # get the extraction directory name from the first part of the
            # extraction paths: it should be the same for all members of
            # the archive
            for m in tf.getmembers():
                split_path = fsutils.fullySplitPath(m.name)
                logger.debug('process member: %s %s', m.name, split_path)
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
        # make sure the destination directory doesn't exist:
        fsutils.rmRf(to_directory)
        shutil.move(temp_directory, to_directory)
        temp_directory = None
        logger.debug('extraction complete %s', to_directory)
    except IOError as e:
        if e.errno != errno.ENOENT:
            logger.error('failed to extract tarfile %s', e)
            fsutils.rmF(tar_file_path)
        raise
    finally:
        if temp_directory is not None:
            # if anything has failed, cleanup
            fsutils.rmRf(temp_directory)

def removeFromCache(cache_key):
    f = os.path.join(folders.cacheDirectory(), cache_key)
    try:
        fsutils.rmF(f)
        # remove any metadata too, if it exists
        fsutils.rmF(f + '.json')
    except OSError as e:
        # if we failed to remove either file, then it might be because another
        # instance of yotta is using it, so just skip it this time.
        pass

def unpackFromCache(cache_key, to_directory):
    ''' If the specified cache key exists, unpack the tarball into the
        specified directory, otherwise raise NotInCache (a KeyError subclass).
    '''
    if cache_key is None:
        raise NotInCache('"None" is never in cache')

    cache_key = _encodeCacheKey(cache_key)

    cache_dir = folders.cacheDirectory()
    fsutils.mkDirP(cache_dir)
    path = os.path.join(cache_dir, cache_key)
    logger.debug('attempt to unpack from cache %s -> %s', path, to_directory)
    try:
        unpackFrom(path, to_directory)
        try:
            shutil.copy(path + '.json', os.path.join(to_directory, '.yotta_origin.json'))
        except IOError as e:
            if e.errno == errno.ENOENT:
                pass
            else:
                raise
        cache_logger.debug('unpacked %s from cache into %s', cache_key, to_directory)
        return
    except IOError as e:
        if e.errno == errno.ENOENT:
            cache_logger.debug('%s not in cache', cache_key)
            raise NotInCache('not in cache')
    except OSError as e:
        if e.errno == errno.ENOTEMPTY:
            logger.error('directory %s was not empty: probably simultaneous invocation of yotta! It is likely that downloaded sources are corrupted.')
        else:
            raise

def _downloadToCache(stream, hashinfo={}, origin_info=dict()):
    ''' Download the specified stream to a temporary cache directory, and
        returns a cache key that can be used to access/remove the file.
        You should use either removeFromCache(cache_key) or _moveCachedFile to
        move the downloaded file to a known key after downloading.
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

    cache_dir = folders.cacheDirectory()
    fsutils.mkDirP(cache_dir)
    file_size = 0

    (download_file, download_fname) = tempfile.mkstemp(dir=cache_dir, suffix='.locked')

    with os.fdopen(download_file, 'wb') as f:
        f.seek(0)
        for chunk in stream.iter_content(4096):
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
        file_size = f.tell()
        logger.debug('wrote tarfile of size: %s to %s', file_size, download_fname)
        f.truncate()

    extended_origin_info = {
        'hash': hashinfo,
        'size': file_size
    }
    extended_origin_info.update(origin_info)
    ordered_json.dump(download_fname + '.json', extended_origin_info)
    return os.path.basename(download_fname)

def _moveCachedFile(from_key, to_key):
    ''' Move a file atomically within the cache: used to make cached files
        available at known keys, so they can be used by other processes.
    '''
    cache_dir = folders.cacheDirectory()
    from_path = os.path.join(cache_dir, from_key)
    to_path   = os.path.join(cache_dir, to_key)
    try:
        os.rename(from_path, to_path)
        # if moving the actual file was successful, then try to move the
        # metadata:
        os.rename(from_path+'.json', to_path+'.json')
    except Exception as e:
        # if the source doesn't exist, or the destination doesn't exist, remove
        # the file instead.
        # windows error 183 == file already exists
        # (be careful not to use WindowsError on non-windows platforms as it
        # isn't defined)
        if (isinstance(e, OSError) and e.errno == errno.ENOENT) or \
           (isinstance(e, getattr(__builtins__, "WindowsError", type(None))) and e.errno == 183):
            fsutils.rmF(from_path)
        else:
            raise

@sometimesPruneCache(0.05)
def unpackTarballStream(stream, into_directory, hash={}, cache_key=None, origin_info=dict()):
    ''' Unpack a responses stream that contains a tarball into a directory. If
        a hash is provided, then it will be used as a cache key (for future
        requests you can try to retrieve the key value from the cache first,
        before making the request)
    '''
    cache_key = _encodeCacheKey(cache_key)

    # if the cache is disabled, then use a random cache key even if one was
    # provided, so that the module is not persisted in the cache and its
    # temporary download location is a random key:
    if getMaxCachedModules() == 0:
        cache_key = None

    new_cache_key = _downloadToCache(stream, hash, origin_info)
    unpackFromCache(new_cache_key, into_directory)

    if cache_key is None:
        # if we didn't provide a cache key, there's no point in storing the cache
        removeFromCache(new_cache_key)
    else:
        # otherwise make this file available at the known cache key
        _moveCachedFile(new_cache_key, cache_key)


