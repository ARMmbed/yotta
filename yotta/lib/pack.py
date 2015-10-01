# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import os
from collections import OrderedDict
import tarfile
import re
import logging
import errno
import copy
import hashlib

# PyPi/standard library > 3.4
# it has to be PurePath
from pathlib import PurePath

# JSON Schema, pip install jsonschema, Verify JSON Schemas, MIT
import jsonschema

# version, , represent versions and specifications, internal
import version
# Ordered JSON, , read & write json, internal
import ordered_json
# vcs, , represent version controlled directories, internal
import vcs
# fsutils, , misc filesystem utils, internal
import fsutils
# Registry Access, , access packages in the registry, internal
import registry_access

# These patterns are used in addition to any glob expressions defined by the
# .yotta_ignore file
Default_Publish_Ignore = [
    '/upload.tar.[gb]z',
    '/.git',
    '/.hg',
    '/.svn',
    '/yotta_modules',
    '/yotta_targets',
    '/build',
    '.DS_Store',
    '.sw[ponml]',
    '*~',
    '._.*',
    '.yotta.json'
]

Readme_Regex = re.compile('^readme(?:\.md)', re.IGNORECASE)

Ignore_List_Fname = '.yotta_ignore'

logger = logging.getLogger('components')

class InvalidDescription(Exception):
    pass

# OptionalFileWrapper provides a scope object that can wrap a none-existent file
class OptionalFileWrapper(object):
    def __init__(self, fname=None, mode=None):
        self.fname = fname
        self.mode = mode
        super(OptionalFileWrapper, self).__init__()
    def __enter__(self):
        if self.fname:
            self.file = open(self.fname, self.mode)
        else:
            self.file = open(os.devnull)
        return self
    def __exit__(self, type, value, traceback):
        self.file.close()
    def contents(self):
        if self.fname:
            return self.file.read()
        else:
            return ''
    def extension(self):
        if self.fname:
            return os.path.splitext(self.fname)[1]
        else:
            return ''

    def __nonzero__(self):
        return bool(self.fname)
    # python 3 truthiness
    def __bool__(self):
        return bool(self.fname)


class DependencySpec(object):
    def __init__(self, name, version_req, is_test_dependency=False):
        self.name = name
        self.version_req = version_req
        self.is_test_dependency = is_test_dependency

    def __unicode__(self):
        return u'%s at %s' % (self.name, self.version_req)
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    def __repr__(self):
        return self.__unicode__()

# Pack represents the common parts of Target and Component objects (versions,
# VCS, etc.)

class Pack(object):
    schema_errors_displayed = set()

    def __init__(
            self,
            path,
            description_filename,
            installed_linked,
            schema_filename = None,
            latest_suitable_version = None
        ):
        self.path = path
        self.installed_linked = installed_linked
        self.vcs = None
        self.error = None
        self.latest_suitable_version = latest_suitable_version
        self.version = None
        self.description_filename = description_filename
        self.ignore_list_fname = Ignore_List_Fname
        self.ignore_patterns = copy.copy(Default_Publish_Ignore)
        description_file = os.path.join(path, description_filename)
        if os.path.isfile(description_file):
            try:
                self.description = ordered_json.load(description_file)
                if self.description:
                    if not 'name' in self.description:
                        raise Exception('missing "name"')
                    if 'version' in self.description:
                        self.version = version.Version(self.description['version'])
                    else:
                        raise Exception('missing "version"')
            except Exception as e:
                self.description = OrderedDict()
                self.error = "Description invalid %s: %s" % (description_file, e);
                logger.debug(self.error)
                raise InvalidDescription(self.error)
        else:
            self.error = "No %s file." % description_filename
            self.description = OrderedDict()
        try:
            with open(os.path.join(path, self.ignore_list_fname), 'r') as ignorefile:
                self.ignore_patterns += self._parseIgnoreFile(ignorefile)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
        if self.description and schema_filename and not self.path in self.schema_errors_displayed:
            self.schema_errors_displayed.add(self.path)
            have_errors = False
            with open(schema_filename, 'r') as schema_file:
                schema = json.load(schema_file)
                validator = jsonschema.Draft4Validator(schema)
                for error in validator.iter_errors(self.description):
                    if not have_errors:
                        logger.warning(u'%s has invalid %s:' % (
                            os.path.split(self.path.rstrip('/'))[1],
                            description_filename
                        ))
                        have_errors = True
                    logger.warning(u"  %s value %s" % (u'.'.join([str(x) for x in error.path]), error.message))
            # for now schema validation errors aren't fatal... will be soon
            # though!
            #if have_errors:
            #    raise InvalidDescription('Invalid %s' % description_filename)
        self.vcs = vcs.getVCS(path)

    def getRegistryNamespace(self):
        raise NotImplementedError("must be implemented by subclass")

    def exists(self):
        return os.path.exists(self.description_filename)

    def getError(self):
        ''' If this isn't a valid component/target, return some sort of
            explanation about why that is. '''
        return self.error

    def setError(self, error):
        ''' Set an error: note that setting an error does not make the module
            invalid if it would otherwise be valid.
        '''
        self.error = error

    def getDescriptionFile(self):
        return os.path.join(self.path, self.description_filename)

    def installedLinked(self):
        return self.installed_linked

    def setLatestAvailable(self, version):
        self.latest_suitable_version = version

    def outdated(self):
        ''' Return a truthy object if a newer suitable version is available,
            otherwise return None.
            (in fact the object returned is a ComponentVersion that can be used
             to get the newer version)
        '''
        if self.latest_suitable_version and self.latest_suitable_version > self.version:
            return self.latest_suitable_version
        else:
            return None

    def vcsIsClean(self):
        ''' Return true if the directory is not version controlled, or if it is
            version controlled with a supported system and is in a clean state
        '''
        if not self.vcs:
            return True
        return self.vcs.isClean()

    def commitVCS(self, tag=None):
        ''' Commit the current working directory state (or do nothing if the
            working directory is not version controlled)
        '''
        if not self.vcs:
            return
        self.vcs.commit(message='version %s' % tag, tag=tag)

    def getVersion(self):
        ''' Return the version as specified by the package file.
            This will always be a real version: 1.2.3, not a hash or a URL.

            Note that a component installed through a URL still provides a real
            version - so if the first component to depend on some component C
            depends on it via a URI, and a second component depends on a
            specific version 1.2.3, dependency resolution will only succeed if
            the version of C obtained from the URL happens to be 1.2.3
        '''
        return self.version

    def getName(self):
        if self.description:
            return self.description['name']
        else:
            return None

    def _parseIgnoreFile(self, f):
        r = []
        for l in f:
            l = l.rstrip('\n\r')
            if not l.startswith('#') and len(l):
                r.append(l)
        return r

    def ignores(self, path):
        ''' Test if this module ignores the file at "path", which must be a
            path relative to the root of the module.

            If a file is within a directory that is ignored, the file is also
            ignored.
        '''
        test_path = PurePath('/', path)

        # also check any parent directories of this path against the ignore
        # patterns:
        test_paths = tuple([test_path] + list(test_path.parents))

        for exp in self.ignore_patterns:
            for tp in test_paths:
                if tp.match(exp):
                    logger.debug('"%s" ignored ("%s" matched "%s")', path, tp, exp)
                    return True
        return False

    def setVersion(self, version):
        self.version = version
        self.description['version'] = str(self.version)

    def setName(self, name):
        self.description['name'] = name

    def writeDescription(self):
        ''' Write the current (possibly modified) component description to a
            package description file in the component directory.
        '''
        ordered_json.dump(os.path.join(self.path, self.description_filename), self.description)
        if self.vcs:
            self.vcs.markForCommit(self.description_filename)

    def generateTarball(self, file_object):
        ''' Write a tarball of the current component/target to the file object
            "file_object", which must already be open for writing at position 0
        '''
        archive_name = '%s-%s' % (self.getName(), self.getVersion())
        def filterArchive(tarinfo):
            if tarinfo.name.find(archive_name) == 0 :
                unprefixed_name = tarinfo.name[len(archive_name)+1:]
                tarinfo.mode &= 0o775
            else:
                unprefixed_name = tarinfo.name
            if self.ignores(unprefixed_name):
                return None
            else:
                return tarinfo
        with tarfile.open(fileobj=file_object, mode='w:gz') as tf:
            logger.info('generate archive extracting to "%s"' % archive_name)
            tf.add(self.path, arcname=archive_name, filter=filterArchive)

    def findAndOpenReadme(self):
        files = os.listdir(self.path)
        readme_files = [x for x in files if Readme_Regex.match(x)]
        reamde_file_if_found = None
        for f in readme_files:
            if f.endswith('.md'):
                return OptionalFileWrapper(f, 'r')
        if len(readme_files):
            # if we have multiple files and none of them end with .md, then we're
            # in some hellish world where files have the same name with different
            # casing. Just choose the first in the directory listing:
            return OptionalFileWrapper(readme_files[0], 'r')
        else:
            # no readme files: return an empty file wrapper
            return OptionalFileWrapper()

    def publish(self, registry=None):
        ''' Publish to the appropriate registry, return a description of any
            errors that occured, or None if successful.
            No VCS tagging is performed.
        '''
        if (registry is None) or (registry == registry_access.Registry_Base_URL):
            if 'private' in self.description and self.description['private']:
                return "this %s is private and cannot be published" % (self.description_filename.split('.')[0])
        upload_archive = os.path.join(self.path, 'upload.tar.gz')
        fsutils.rmF(upload_archive)
        fd = os.open(upload_archive, os.O_CREAT | os.O_EXCL | os.O_RDWR | getattr(os, "O_BINARY", 0))
        with os.fdopen(fd, 'rb+') as tar_file:
            tar_file.truncate()
            self.generateTarball(tar_file)
            logger.debug('generated tar file of length %s', tar_file.tell())
            tar_file.seek(0)
            # calculate the hash of the file before we upload it:
            shasum = hashlib.sha256()
            while True:
                chunk = tar_file.read(1000)
                if not chunk:
                    break
                shasum.update(chunk)
            logger.debug('generated tar file has hash %s', shasum.hexdigest())
            tar_file.seek(0)
            with self.findAndOpenReadme() as readme_file_wrapper:
                if not readme_file_wrapper:
                    logger.warning("no readme.md file detected")
                with open(self.getDescriptionFile(), 'r') as description_file:
                    return registry_access.publish(
                        self.getRegistryNamespace(),
                        self.getName(),
                        self.getVersion(),
                        description_file,
                        tar_file,
                        readme_file_wrapper.file,
                        readme_file_wrapper.extension().lower(),
                        registry=registry
                    )

    def unpublish(self, registry=None):
        ''' Try to un-publish the current version. Return a description of any
            errors that occured, or None if successful.
        '''
        return registry_access.unpublish(
            self.getRegistryNamespace(),
            self.getName(),
            self.getVersion(),
            registry=registry
        )


    @classmethod
    def ensureOrderedDict(cls, sequence=None):
        # !!! NB: MUST return the same object if the object is already an
        # ordered dictionary. we rely on spooky-action-at-a-distance to keep
        # the "available components" dictionary synchronised between all users
        if isinstance(sequence, OrderedDict):
            return sequence
        elif sequence:
            return OrderedDict(sequence)
        else:
            return OrderedDict()

    def __repr__(self):
        if not self:
            return "INVALID COMPONENT @ %s: %s" % (self.path, self.description)
        return "%s %s at %s" % (self.description['name'], self.description['version'], self.path)

    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return bool(self.description)
    # python 3 truthiness
    def __bool__(self):
        return bool(self.description)
