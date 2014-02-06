# standard library modules, , ,
import json

# How to use a Component:
#
# Initialise it with the directory into which the package has been downloaded.
#
# Check that 'if package:' is true, which indicates that the download is indeed
# a valid package.
#
# Check that package.getVersion() returns the version you think you've
# downloaded, if it doesn't be sure to make a fuss.
#
# Use package.getDependencies() to get the names of the dependencies of the
# package
#
#
# ... eventually it will also be possible to use packages to tag & commit new
# versions, etc.
#

# The package file format is currently assumed to be identical to NPM's
# package.json


class Component:
    def __init__(self, directory):
        pass

    def getDependencies(self):
        ''' Returns [(package name, version requirement)]
            e.g. ('ARM-RD/yottos', '*')
        '''
    
    def getVersion(self):
        ''' Return the version string as specified by the package file.
            Note that this might be a URI.
        '''


    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return self.package_info

