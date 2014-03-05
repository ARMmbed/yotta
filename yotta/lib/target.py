# standard library modules, , ,
import json
import os

# version, , represent versions and specifications, internal
import version
# Pack, , common parts of Components/Targets, internal
import pack

Target_Description_File = 'target.json'
Registry_Namespace = 'target'

# API
class Target(pack.Pack):
    description_filename = Target_Description_File

    def __init__(self, path, installed_linked=False, latest_suitable_version=None):
        ''' Initialise a Target based on a directory. If the directory does not
            contain a valid target.json file the initialised object will test
            false, and will contain an error property containing the failure.
        '''
        super(Target, self).__init__(path, installed_linked=installed_linked)
        self.latest_suitable_version = latest_suitable_version
        # !!! TODO: validate self.description, possibly add a
        # description_schema class variable used when loading...
    
    def dependencyResolutionOrder(self):
        ''' Return a sequence of names that should be used when resolving
            dependencies: if specific dependencies exist for 
        '''
        return [self.description['name']] + self.description['similarTo']

    def getToolchainFile(self):
        return os.path.join(self.path, self.description['toolchain'])

    #def getLinkScriptFile(self):
    #    return os.path.join(self.path, self.description['linkscript'])
    
    def getRegistryNamespace(self):
        return Registry_Namespace

