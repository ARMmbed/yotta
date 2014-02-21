# standard library modules, , ,
import tarfile
import logging
import os

# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils

class AccessException(Exception):
    pass

class ComponentUnavailable(AccessException):
    pass

class TargetUnavailable(AccessException):
    pass

class RemoteVersion(version.Version):
    def unpackInto(self, directory):
        raise NotImplementedError

class RemoteComponent(object):
    @classmethod
    def createFromNameAndSpec(cls, url, name=None):
        raise NotImplementedError

    def versionSpec(self):
        raise NotImplementedError

    def availableVersions(self):
        raise NotImplementedError

    def tipVersion(self):
        raise NotImplementedError

def unpackTarballStream(stream, into_directory):
    ''' Unpack a stream-like object that contains a tarball into a directory
    '''
    chunk = 1024 * 32
    fsutils.mkDirP(into_directory)
    # create the archive exclusively, we don't want someone else maliciously
    # overwriting our tar archive with something that unpacks to an absolute
    # path when we might be running sudo'd
    fd = os.open(os.path.join(into_directory, 'download.tar.gz'), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    with os.fdopen(fd, 'rb+') as f:
        f.seek(0)
        while True:
            data = stream.read(chunk)
            if not data: break
            f.write(data)
        f.truncate()
        logging.debug('got file, extract into %s', into_directory)
        # head back to the start of the file and untar (without closing the
        # file)
        f.seek(0)
        with tarfile.open(fileobj=f) as tf:
            to_extract = []
            # modify members to change where they extract to!
            for m in tf.getmembers():
                split_path = fsutils.fullySplitPath(m.name)
                if len(split_path) > 1:
                    m.name = os.path.join(*(split_path[1:]))
                    to_extract.append(m)
            tf.extractall(path=into_directory, members=to_extract)
    logging.debug('extraction complete %s', into_directory)
