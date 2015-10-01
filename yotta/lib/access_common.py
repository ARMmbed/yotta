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

# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils

logger = logging.getLogger('access')

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



def unpackTarballStream(stream, into_directory, hash=(None, None)):
    ''' Unpack a responses stream that contains a tarball into a directory
    '''
    hash_name = hash[0]
    hash_value = hash[1]

    if hash_name:
        m = getattr(hashlib, hash_name)()

    into_parent_dir = os.path.dirname(into_directory)
    fsutils.mkDirP(into_parent_dir)
    temp_directory = tempfile.mkdtemp(dir=into_parent_dir)
    download_fname = os.path.join(temp_directory, 'download.tar.gz')
    # remove any partially downloaded file: TODO: checksumming & caching of
    # downloaded components in some central place
    fsutils.rmF(download_fname)
    # create the archive exclusively, we don't want someone else maliciously
    # overwriting our tar archive with something that unpacks to an absolute
    # path when we might be running sudo'd
    try:
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
            logger.debug(
                'got file, extract into %s (for %s)', temp_directory, into_directory
            )
            # head back to the start of the file and untar (without closing the
            # file)
            f.seek(0)
            f.flush()
            os.fsync(f)
            with tarfile.open(fileobj=f) as tf:
                extracted_dirname = ''
                # get the extraction directory name from the first part of the
                # extraction paths: it should be the same for all members of
                # the archive
                for m in tf.getmembers():
                    split_path = fsutils.fullySplitPath(m.name)
                    if len(split_path) > 1:
                        if extracted_dirname:
                            if split_path[0] != extracted_dirname:
                                raise ValueError('archive does not appear to contain a single module')
                        else:
                            extracted_dirname = split_path[0]
                tf.extractall(path=temp_directory)

        # move the directory we extracted stuff into to where we actually want it
        # to be
        fsutils.rmRf(into_directory)
        shutil.move(os.path.join(temp_directory, extracted_dirname), into_directory)

    finally:
        fsutils.rmF(download_fname)
        fsutils.rmRf(temp_directory)

    logger.debug('extraction complete %s', into_directory)
