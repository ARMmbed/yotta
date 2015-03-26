# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import os
import signal
import subprocess
import logging
import string
import traceback
import errno

# version, , represent versions and specifications, internal
import version
# Pack, , common parts of Components/Targets, internal
import pack

Target_Description_File = 'target.json'
Registry_Namespace = 'targets'

def _ignoreSignal(signum, frame):
    logging.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _newPGroup():
    os.setpgrp()

# API
class Target(pack.Pack):
    def __init__(self, path, installed_linked=False, latest_suitable_version=None):
        ''' Initialise a Target based on a directory. If the directory does not
            contain a valid target.json file the initialised object will test
            false, and will contain an error property containing the failure.
        '''
        # !!! TODO: implement a target.json schema, and pass schema_filename
        # here:
        super(Target, self).__init__(
                                      path,
               description_filename = Target_Description_File,
                   installed_linked = installed_linked,
            latest_suitable_version = latest_suitable_version
        )
    
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
        parser.add_argument('-G', '--cmake-generator', dest='cmake_generator',
           default=('Unix Makefiles', 'Ninja')[os.name == 'nt'],
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

    def exec_helper(self, cmd, builddir):
        ''' Execute the given command, returning an error message if an error occured
            or None if the command was succesful.'''
        try:
            child = subprocess.Popen(cmd, cwd=builddir)
            child.wait()
        except OSError as e:
            if e.errno == errno.ENOENT:
                if cmd[0] == 'cmake':
                    return 'CMake is not installed, please follow the installation instructions at http://docs.yottabuild.org/#installing'
                else:
                    return '%s is not installed' % (cmd[0])
            else:
                return 'command %s failed' % (cmd)
        if child.returncode:
            return 'command %s failed' % (cmd)

    def build(self, builddir, component, args, release_build=False, build_args=None):
        ''' Execute the commands necessary to build this component, and all of
            its dependencies. '''
        if build_args is None:
            build_args = []
        # in the future this may be specified in the target description, but
        # for now we only support cmake, so everything is simple:
        build_type = ('Debug', 'RelWithDebInfo')[release_build]
        if build_type:
            cmd = ['cmake', '-D', 'CMAKE_BUILD_TYPE=%s' % build_type, '-G', args.cmake_generator, '.']
        else:
            cmd = ['cmake', '-G', args.cmake_generator, '.']
        res = self.exec_helper(cmd, builddir)
        if res is not None:
            yield res
        # cmake error: the generated Ninja build file will not work on windows when arguments are read from
        # a file (@file) instead of the command line, since '\' in @file is interpreted as an escape sequence.
        # !!! FIXME: remove this once http://www.cmake.org/Bug/view.php?id=15278 is fixed!
        if args.cmake_generator == "Ninja" and os.name == 'nt':
            logging.debug("Converting back-slashes in build.ninja to forward-slashes")
            build_file = os.path.join(builddir, "build.ninja")
            # We want to convert back-slashes to forward-slashes, except in macro definitions, such as
            # -DYOTTA_COMPONENT_VERSION = \"0.0.1\". So we use a little trick: first we change all \"
            # strings to an unprintable ASCII char that can't appear in build.ninja (in this case \1),
            # then we convert all the back-slashed to forward-slashes, then we convert '\1' back to \".
            try:
                f = open(build_file, "r+t")
                data = f.read()
                data = data.replace('\\"', '\1')
                data = data.replace('\\', '/')
                data = data.replace('\1', '\\"')
                f.seek(0)
                f.write(data)
                f.close()
            except:
                yield 'Unable to update "%s", aborting' % build_file
        build_command = self.overrideBuildCommand(args.cmake_generator)
        if build_command:
            cmd = build_command + build_args
        else:
            cmd = ['cmake', '--build', builddir] + build_args
        res = self.exec_helper(cmd, builddir)
        if res is not None:
            yield res
        hint = self.hintForCMakeGenerator(args.cmake_generator, component)
        if hint:
            logging.info(hint)

    def findProgram(self, builddir, program):
        ''' Return the builddir-relative path of program, if only a partial
            path is specified. Returns None and logs an error message if the
            program is ambiguous or not found
	'''
        # if this is an exact match, do no further checking:
        if os.path.isfile(os.path.join(builddir, program)):
            logging.info('found %s' % program)
            return program
        exact_matches = []
        insensitive_matches = []
        approx_matches = []
        for path, dirs, files in os.walk(builddir):
            if program in files:
                exact_matches.append(os.path.relpath(os.path.join(path, program), builddir))
                continue
            files_lower = [f.lower() for f in files]
            if program.lower() in files_lower:
                insensitive_matches.append(
                    os.path.relpath(
                        os.path.join(path, files[files_lower.index(program.lower())]),
                        builddir
                    )
                )
                continue
            # !!! TODO: in the future add approximate string matching (typos,
            # etc.), for now we just test stripping any paths off program, and
            # looking for substring matches:
            pg_basen_lower_noext = os.path.splitext(os.path.basename(program).lower())[0]
            for f in files_lower:
                if pg_basen_lower_noext in f:
                    approx_matches.append(
                        os.path.relpath(
                            os.path.join(path, files[files_lower.index(f)]),
                            builddir
                        )
                    )

        if len(exact_matches) == 1:
            logging.info('found %s at %s')
            return exact_matches[0]
        elif len(exact_matches) > 1:
            logging.error(
                '%s matches multiple executables, please use a full path (one of %s)' % (
                    program,
                    ', or '.join(['"'+os.path.join(m, program)+'"' for m in exact_matches])
                )
            )
            return None
        # if we have matches with and without a file extension, prefer the
        # no-file extension version, and discard the others (so we avoid
        # picking up post-processed files):
        reduced_approx_matches = []
        for m in approx_matches:
            root = os.path.splitext(m)[0]
            if (m == root) or (root not in approx_matches):
                reduced_approx_matches.append(m)
        approx_matches = reduced_approx_matches

        for matches in (insensitive_matches, approx_matches):
            if len(matches) == 1:
                logging.info('found %s at %s' % (
                    program, matches[0]
                ))
                return matches[0]
            elif len(matches) > 1:
                logging.error(
                    '%s is similar to several executables found. Please use an exact name:\n%s' % (
                        program,
                        '\n'.join(matches)
                    )
                )
                return None
        logging.error('could not find program "%s" to debug' %  program)
        return None
    
    def debug(self, builddir, program):
        ''' Launch a debugger for the specified program. '''
        if 'debug' not in self.description:
            yield "Target %s does not specify debug commands" % self
            return
        prog_path = self.findProgram(builddir, program)
        if prog_path is None:
            return
        
        with open(os.devnull, "w") as dev_null:
            daemon = None
            child = None
            try:
                # debug-server is the old name, debugServer is the new name
                debug_server_prop = 'debugServer'
                if not debug_server_prop in self.description:
                    debug_server_prop = 'debug-server'

                if debug_server_prop in self.description:
                    logging.debug('starting debug server...')
                    daemon = subprocess.Popen(
                                   self.description[debug_server_prop],
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

