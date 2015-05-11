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

# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils


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
        return self.__unicode__().encode('utf-8')
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


def unpackTarballStream(stream, into_directory, hash=(None, None)):
    ''' Unpack a stream-like object that contains a tarball into a directory
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
        fd = os.open(download_fname, os.O_CREAT | os.O_EXCL |
                                     os.O_RDWR | getattr(os, "O_BINARY", 0))
        with os.fdopen(fd, 'rb+') as f:
            f.seek(0)
            
            for chunk in stream.iter_content(1024):
                f.write(chunk)
                if hash_name:
                    m.update(chunk)

            if hash_name:
                calculated_hash = m.hexdigest()
                logging.debug(
                    'calculated hash: %s check against: %s' % (calculated_hash, hash_value))
                if hash_value and (hash_value != calculated_hash):
                    raise Exception('Hash verification failed.')
            f.truncate()
            logging.debug(
                'got file, extract into %s (for %s)', temp_directory, into_directory)
            # head back to the start of the file and untar (without closing the
            # file)
            f.seek(0)
            f.flush()
            os.fsync(f)
            with tarfile.open(fileobj=f) as tf:
                to_extract = []
                # modify members to change where they extract to!
                for m in tf.getmembers():
                    split_path = fsutils.fullySplitPath(m.name)
                    if len(split_path) > 1:
                        m.name = os.path.join(*(split_path[1:]))
                        to_extract.append(m)
                tf.extractall(path=temp_directory, members=to_extract)

        # remove the temporary download file, maybe in the future we will cache
        # these somewhere
        fsutils.rmRf(os.path.join(into_directory, 'download.tar.gz'))

        # move the directory we extracted stuff into to where we actually want it
        # to be
        fsutils.rmRf(into_directory)
        shutil.move(temp_directory, into_directory)

    finally:
        fsutils.rmRf(temp_directory)

    logging.debug('extraction complete %s', into_directory)
