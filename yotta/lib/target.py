# standard library modules, , ,
import json
import os
import signal
import subprocess
import logging
import string
import traceback

# version, , represent versions and specifications, internal
import version
# Pack, , common parts of Components/Targets, internal
import pack

Target_Description_File = 'target.json'
Registry_Namespace = 'target'

def _ignoreSignal(signum, frame):
    logging.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _newPGroup():
    os.setpgrp()

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
    
    @classmethod
    def addBuildOptions(cls, parser):
        parser.add_argument('-G', '--cmake-generator', dest='cmake_generator', default='Unix Makefiles',
           choices=(
               'Unix Makefiles',
               'Ninja',
               'Xcode',
               'Sublime Text 2 - Ninja',
               'Sublime Text 2 - Unix Makefiles'
           )
        )

    @classmethod
    def overrideBuildCommand(cls, generator_name):
        # when we build using cmake --build, the nice colourised output is lost
        # - so override with the actual build command for command-line
        # generators where people will care:
        try:
            return {
                'Unix Makefiles': ['make'],
                'Ninja': ['ninja']
            }[generator_name]
        except KeyError:
            return None

    def hintForCMakeGenerator(self, generator_name, component):
        try:
            name = self.getName()
            component_name = component.getName()
            return {
                'Xcode':
                    'to open the built project, run:\nopen ./build/%s/%s.xcodeproj' % (name, component_name),
                'Sublime Text 2 - Ninja':
                    'to open the built project, run:\nopen ./build/%s/%s.??' % (name, component_name),
                'Sublime Text 2 - Unix Makefiles':
                    'to open the built project, run:\nopen ./build/%s/%s.??' % (name, component_name)
            }[generator_name]
        except KeyError:
            return None

    def build(self, builddir, component, args, debug_build=False, release_build=False):
        ''' Execute the commands necessary to build this component, and all of
            its dependencies. '''
        # in the future this may be specified in the target description, but
        # for now we only support cmake, so everything is simple:
        commands = []
        build_type = ((None, 'Debug'), ('Release', 'RelWithDebInfo'))[release_build][debug_build]
        if build_type:
            commands.append(['cmake', '-D', 'CMAKE_BUILD_TYPE=%s' % build_type, '-G', args.cmake_generator, '.'])
        else:
            commands.append(['cmake', '-G', args.cmake_generator, '.'])
        build_command = self.overrideBuildCommand(args.cmake_generator)
        if build_command:
            commands.append(build_command)
        else:
            commands.append(['cmake', '--build', builddir])
        for cmd in commands:
            child = subprocess.Popen(
                cmd, cwd=builddir
            )
            child.wait()
            if child.returncode:
                yield 'command %s failed' % (cmd)
        hint = self.hintForCMakeGenerator(args.cmake_generator, component)
        if hint:
            print hint
    
    def debug(self, builddir, program):
        ''' Launch a debugger for the specified program. '''
        if 'debug' not in self.description:
            yield "Target %s does not specify debug commands" % self
            return
        prog_path = os.path.join(builddir, program)
        if not os.path.isfile(prog_path):
            suggestion = None
            if (prog_path.endswith('.c') or prog_path.endswith('.m')) and os.path.isfile(prog_path[:-2]):
                suggestion = program[:-2]
            elif (prog_path.endswith('.cpp') or prog_path.endswith('.cxx')) and os.path.isfile(prog_path[:-4]):
                suggestion = program[:-4]
            elif os.path.isfile(os.path.join(builddir, 'source', program)):
                suggestion = os.path.join('source', program)
            if suggestion is not None:
                yield "%s does not exist, perhaps you meant %s" % (program, suggestion)
            else:
                yield "%s does not exist" % program
            return
        
        
        with open(os.devnull, "w") as dev_null:
            daemon = None
            child = None
            try:
                if 'debug-server' in self.description:
                    logging.debug('starting debug server...')
                    daemon = subprocess.Popen(
                                   self.description['debug-server'],
                             cwd = builddir,
                          stdout = dev_null,
                          stderr = dev_null,
                      preexec_fn = _newPGroup
                    )
                else:
                    daemon = None
                
                
                signal.signal(signal.SIGINT, _ignoreSignal);
                cmd = [
                    os.path.expandvars(string.Template(x).safe_substitute(program=prog_path))
                    for x in self.description['debug']
                ]
                logging.debug('starting debugger: %s', cmd)
                child = subprocess.Popen(
                    cmd, cwd = builddir
                )
                child.wait()
                if child.returncode:
                    yield "debug process executed with status %s" % child.returncode
                child = None
            except:
                # reset the terminal, in case the debugger has screwed it up
                os.system('reset')
                raise
            finally:
                if child is not None:
                    child.terminate()
                if daemon is not None:
                    logging.debug('shutting down debug server...')
                    daemon.terminate()
                # clear the sigint handler
                signal.signal(signal.SIGINT, signal.SIG_DFL);

