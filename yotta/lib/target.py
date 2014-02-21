# standard library modules, , ,
import json
import os

# version, , represent versions and specifications, internal
import version
# Ordered JSON, , read & write json, internal
import ordered_json


Target_Description_File = 'target.json'


# API
class Target:
    def __init__(self, path, installed_linked=False, latest_suitable_version=None):
        ''' Initialise a Target based on a directory. If the directory does not
            contain a valid target.json file the initialised object will test
            false, and will contain an error property containing the failure.
        '''
        self.error = None
        self.path = path
        self.installed_linked = installed_linked
        self.version = None
        self.latest_suitable_version = latest_suitable_version
        try:
            self.target_info = ordered_json.readJSON(os.path.join(path, Target_Description_File))
            self.version     = version.Version(self.target_info['version'])
            # TODO: validate everything else
        except Exception, e:
            self.target_info = None
            self.error = e
    
    def getName(self):
        return self.target_info['name']
    
    def dependencyResolutionOrder(self):
        ''' Return a sequence of names that should be used when resolving
            dependencies: if specific dependencies exist for 
        '''
        return [self.target_info['name']] + self.target_info['similar_to']

    def toolchainFile(self):
        return os.path.join(self.path, self.target_info['toolchain_file'])

    def linkScriptFile(self):
        return os.path.join(self.path, self.target_info['linkscript'])
    
    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return bool(self.target_info)

