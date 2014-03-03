# standard library modules, , ,
import json
import os
from collections import OrderedDict
import tarfile
import re
import logging

# version, , represent versions and specifications, internal
import version
# Ordered JSON, , read & write json, internal
import ordered_json
# vcs, , represent version controlled directories, internal
import vcs

# TODO: .xxx_ignore file support for overriding the defaults, use glob syntax
# instead of regexes...
Default_Publish_Ignore = [
    '^\.git$',
    '^\.hg$',
    '^\.svn$',
    '^yotta_modules$',
    '^yotta_targets$',
    '^\.DS_Store$',
    '^\.sw[ponml]$',
    '^\._.*$',
    '[/\\\\]\.DS_Store$',
    '[/\\\\]\.sw[ponml]$',
    '[/\\\\]\._.*$',
]

# Pack represents the common parts of Target and Component objects (versions,
# VCS, etc.)

class Pack(object):
    description_filename = None

    def __init__(self, path, installed_linked):
        self.path = path
        self.installed_linked = installed_linked
        self.vcs = None
        self.error = None
        try:
            self.description = ordered_json.readJSON(os.path.join(path, self.description_filename))
            self.version = version.Version(self.description['version'])
        except Exception, e:
            self.description = OrderedDict()
            self.error = e

    def initVCS(self):
        self.vcs = vcs.getVCS(path)
    
    def getError(self):
        ''' If this isn't a valid component/target, return some sort of
            explanation about why that is. '''
        return self.error

    def getDescriptionFile(self):
        return os.path.join(self.path, self.description_filename)

    def installedLinked(self):
        return self.installed_linked

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
    
    def setVersion(self, version):
        self.version = version
        self.description['version'] = str(self.version)

    def setName(self, name):
        self.description['name'] = name

    def writeDescription(self):
        ''' Write the current (possibly modified) component description to a
            package description file in the component directory.
        '''
        ordered_json.writeJSON(path.join(self.path, Component_Description_File), self.description)
        if self.vcs:
            self.vcs.markForCommit(Component_Description_File)
    
    def generateTarball(self, file_object):
        ''' Write a tarball of the current component/target to the file object
            "file_object", which must already be open for writing at position 0
        '''
        filter_pattern = re.compile('|'.join(Default_Publish_Ignore))
        def filterArchive(tarinfo):
            if filter_pattern.search(tarinfo.name):
                return None
            else:
                return tarinfo
        with tarfile.open(fileobj=file_object, mode='w:gz') as tf:
            archive_name = '%s-%s' % (self.getName(), self.getVersion())
            logging.info('generate archive extracting to "%s"' % archive_name)
            tf.add(self.path, arcname=archive_name, filter=filterArchive)

    def __repr__(self):
        return "%s %s at %s" % (self.description['name'], self.description['version'], self.path)

    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return bool(self.description)
