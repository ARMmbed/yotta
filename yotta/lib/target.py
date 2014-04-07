# standard library modules, , ,
import json
import os
import subprocess
import logging
import string

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
        super(Target, self).__init__(
            path,
            installed_linked=installed_linked,
            latest_suitable_version=latest_suitable_version
        )
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

    def build(self, builddir):
        ''' Execute the commands necessary to build this component, and all of
            its dependencies. '''
        # in the future this may be specified in the target description, but
        # for now we only support cmake, so everything is simple:
        #commands = [['cmake','.', '-G', 'Ninja'], ['ninja']]
        commands = [['cmake','.'], ['make']]
        for cmd in commands:
            child = subprocess.Popen(
                cmd, cwd=builddir
            )
            child.wait()
            if child.returncode:
                yield err
    
    def debug(self, builddir, program):
        ''' Launch a debugger for the specified program. '''
        if 'debug' not in self.description:
            yield "Target %s does not specify debug commands" % self
            return
        prog_path = os.path.join(builddir, program)
        if not os.path.isfile(prog_path):
            yield "%s does not exist, perhaps you meant %s" % (
                os.path.relpath(program), os.path.relpath(os.path.join('source', program))
            )
            return
        
        
        with open(os.devnull, "w") as dev_null:
            try:
                if 'debug-server' in self.description:
                    logging.debug('starting debug server...')
                    daemon = subprocess.Popen(
                        self.description['debug-server'], cwd=builddir,
                        stdout = dev_null, stderr = dev_null
                    )
                else:
                    daemon = None
                
                
                cmd = [
                    string.Template(x).safe_substitute(program=prog_path)
                    for x in self.description['debug']
                ]
                logging.debug('starting debugger: %s', cmd)
                child = subprocess.Popen(
                    cmd, cwd=builddir
                )
                child.wait()
                if child.returncode:
                    yield "debug process executed with status %s" % child.returncode
            except:
                # reset the terminal, in case the debugger has screwed it up
                os.system('reset')
                raise
            finally:
                if daemon:
                    logging.debug('shutting down debug server...')
                    daemon.terminate()
