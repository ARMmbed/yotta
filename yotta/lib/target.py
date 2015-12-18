# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import signal
import subprocess
import logging
import string
import traceback
import errno
import itertools
import shlex
from collections import OrderedDict

# Ordered JSON, , read & write json, internal
import ordered_json
# access, , get components, internal
import access
import access_common
# Pack, , common parts of Components/Targets, internal
import pack
# fsutils, , misc filesystem utils, internal
import fsutils

Target_Description_File = 'target.json'
App_Config_File = 'config.json'
Registry_Namespace = 'targets'
Schema_File = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema', 'target.json')

logger = logging.getLogger('target')

def _ignoreSignal(signum, frame):
    logger.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _newPGroup():
    os.setpgrp()

def _mergeDictionaries(*args):
    ''' merge dictionaries of dictionaries recursively, with elements from
        dictionaries earlier in the argument sequence taking precedence
    '''
    # to support merging of OrderedDicts, copy the result type from the first
    # argument:
    result = type(args[0])()
    for k, v in itertools.chain(*[x.items() for x in args]):
        if not k in result:
            result[k] = v
        elif isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _mergeDictionaries(result[k], v)
    return result

def _mirrorStructure(dictionary, value):
    ''' create a new nested dictionary object with the same structure as
        'dictionary', but with all scalar values replaced with 'value'
    '''
    result = type(dictionary)()
    for k in dictionary.keys():
        if isinstance(dictionary[k], dict):
            result[k] = _mirrorStructure(dictionary[k], value)
        else:
            result[k] = value
    return result

# API

def loadAdditionalConfig(config_path):
    ''' returns (error, config)
    '''
    error = None
    config = {}
    if not config_path:
        return (error, config)
    if os.path.isfile(config_path):
        try:
            config = ordered_json.load(config_path)
        except Exception as e:
            error = "Invalid syntax in file %s: %s" % (config_path, e)
    else:
        # try to interpret the argument as literal JSON
        try:
            config = ordered_json.loads(config_path)
        except Exception as e:
            # if this fails too, guess whether it was intended to be JSON or
            # not, and display an appropriate error message
            if '{' in config_path or '}' in config_path:
                error = "Invalid syntax in literal JSON: %s" % e
            else:
                error = "File \"%s\" does not exist" % config_path
    logger.debug('read additional config: %s', config)
    return (error, config)

def getDerivedTarget(
        target_name_and_version,
                   targets_path,
                application_dir = None,
                install_missing = True,
               update_installed = False,
              additional_config = None
    ):
    ''' Get the specified target description, optionally ensuring that it (and
        all dependencies) are installed in targets_path.

        Returns (DerivedTarget, errors), or (None, errors) if the leaf target
        could not be found/installed.
    '''
    logger.debug('satisfy target: %s' % target_name_and_version);
    if ',' in target_name_and_version:
        name, ver = target_name_and_version.split(',')
        dspec = pack.DependencySpec(name, ver)
    else:
        dspec = pack.DependencySpec(target_name_and_version, "*")

    leaf_target      = None
    previous_name    = dspec.name
    search_dirs      = [targets_path]
    target_hierarchy = []
    errors           = []
    while True:
        t = None
        try:
            if install_missing:
                t = access.satisfyVersion(
                                 name = dspec.name,
                     version_required = dspec.version_req,
                            available = target_hierarchy,
                         search_paths = search_dirs,
                    working_directory = targets_path,
                     update_installed = ('Update' if update_installed else None),
                                 type = 'target'
                )
            else:
                t = access.satisfyVersionFromSearchPaths(
                                 name = dspec.name,
                     version_required = dspec.version_req,
                         search_paths = search_dirs,
                                 type = 'target'
                )
        except access_common.Unavailable as e:
            errors.append(e)
        if not t:
            if install_missing:
                logger.error(
                    'could not install target %s for %s' %
                    (dspec, previous_name)
                )
            break
        else:
            target_hierarchy.append(t)
            previous_name = dspec.name
            assert(isinstance(t, Target))
            dspec = t.baseTargetSpec() #pylint: disable=no-member
            if not leaf_target:
                leaf_target = t
            if dspec is None:
                break
    if leaf_target is None:
        return (None, errors)
    # if we have a valid target, try to load the app-specific config data (if
    # any):
    app_config = {}
    if application_dir is not None:
        app_config_fname = os.path.join(application_dir, App_Config_File)
        if os.path.exists(app_config_fname):
            try:
                app_config = ordered_json.load(app_config_fname)
            except Exception as e:
                errors.append(Exception("Invalid application config.json: %s" % (e)))
    return (DerivedTarget(leaf_target, target_hierarchy[1:], app_config, additional_config), errors)

class Target(pack.Pack):
    def __init__(self, path, installed_linked=False, latest_suitable_version=None):
        ''' Initialise a Target based on a directory. If the directory does not
            contain a valid target.json file the initialised object will test
            false, and will contain an error property containing the failure.
        '''
        # re-initialise with the information from the most-derived target
        super(Target, self).__init__(
                                      path,
               description_filename = Target_Description_File,
                   installed_linked = installed_linked,
                    schema_filename = Schema_File,
            latest_suitable_version = latest_suitable_version
        )

    def baseTargetSpec(self):
        ''' returns pack.DependencySpec for the base target of this target (or
            None if this target does not inherit from another target.
        '''
        inherits = self.description.get('inherits', {})
        if len(inherits) == 1:
            return pack.DependencySpec(list(inherits.items())[0][0], list(inherits.items())[0][1])
        elif len(inherits) > 1:
            logger.error('target %s specifies multiple base targets, but only one is allowed', self.getName())
        return None

    def getRegistryNamespace(self):
        return Registry_Namespace

    def getConfig(self):
        return self.description.get('config', OrderedDict())

class DerivedTarget(Target):
    def __init__(self, leaf_target, base_targets, app_config, additional_config):
        ''' Initialise a DerivedTarget (representing an inheritance hierarchy of
            Targets.), given the most-derived Target description, and a set of
            available Targets to compose the rest of the lineage from.

            DerivedTarget provides build & debug commands, and access to the
            derived target config info (merged with the application config
            info from config.json, if any).

            It's possible to update the application config for an existing
            DerivedTarget instance.

            DerivedTarget can also be used as a stand-in for the most-derived
            (leaf) target in the inheritance hierarchy.
        '''

        # initialise the base class as a copy of leaf_target
        super(DerivedTarget, self).__init__(
                               path = leaf_target.path,
                   installed_linked = leaf_target.installed_linked,
            latest_suitable_version = leaf_target.latest_suitable_version
        )

        self.hierarchy = [leaf_target] + base_targets[:]
        self.config = None
        self.config_blame = None
        self.app_config = app_config
        self.additional_config = additional_config or {}


    # override truthiness to test validity of the entire hierarchy:
    def __nonzero__(self):
        for t in self.hierarchy:
            if not t: return False
        return bool(len(self.hierarchy))
    def __bool__(self):
        return self.__nonzero__()

    def getScript(self, scriptname):
        ''' return the specified script if one exists (possibly inherited from
            a base target)
        '''
        for t in self.hierarchy:
            if 'scripts' in t.description and scriptname in t.description['scripts']:
                return t.description['scripts'][scriptname]
        return None

    def _loadConfig(self):
        ''' load the configuration information from the target hierarchy '''
        config_dicts = [self.additional_config, self.app_config] + [t.getConfig() for t in self.hierarchy]
        # create an identical set of dictionaries, but with the names of the
        # sources in place of the values. When these are merged they will show
        # where each merged property came from:
        config_blame = [
            _mirrorStructure(self.additional_config, 'command-line config'),
            _mirrorStructure(self.app_config, 'application\'s config.json'),
        ] + [
            _mirrorStructure(t.getConfig(), t.getName()) for t in self.hierarchy
        ]

        self.config = _mergeDictionaries(*config_dicts)
        self.config_blame = _mergeDictionaries(*config_blame)
        # note that backwards compatibility with the "similarTo" data that used
        # to be used for target-dependencies is ensured at the point of use. We
        # don't merge similarTo into the config because it might break things
        # in the config (clobber objects with scalar values, for example)

    def _ensureConfig(self):
        if self.config is None:
            self._loadConfig()

    def getConfigValue(self, conf_key):
        self._ensureConfig()
        # jsonpointer, pip install jsonpointer, BSD 3 Clause
        import jsonpointer
        try:
            return jsonpointer.resolve_pointer(self.config, conf_key)
        except jsonpointer.JsonPointerException as e:
            # fall back to legacy dot-separated pointers
            key_path = conf_key.split('.');
            c = self.config
            for part in key_path:
                if part in c:
                    c = c[part]
                else:
                    return None
            return c

    def getSimilarTo_Deprecated(self):
        r = []
        for t in self.hierarchy:
            r.append(t.getName())
            r += t.description.get('similarTo', [])
        return r

    def getMergedConfig(self):
        self._ensureConfig()
        return self.config

    def getConfigBlame(self):
        self._ensureConfig()
        return self.config_blame

    def getToolchainFiles(self):
        ''' return a list of toolchain file paths in override order (starting
            at the bottom/leaf of the hierarchy and ending at the base).
            The list is returned in the order they should be included
            (most-derived last).
        '''
        return reversed([
            os.path.join(x.path, x.description['toolchain']) for x in self.hierarchy if 'toolchain' in x.description
        ])

    def getAdditionalIncludes(self):
        ''' Return the list of cmake files which are to be included by yotta in
            every module built. The list is returned in the order they should
            be included (most-derived last).
        '''
        return reversed([
            os.path.join(t.path, include_file)
                for t in self.hierarchy
                for include_file in t.description.get('cmakeIncludes', [])
        ])

    @classmethod
    def addBuildOptions(cls, parser):
        parser.add_argument('-G', '--cmake-generator', dest='cmake_generator',
           default='Ninja',
           help='CMake generator to use (defaults to Ninja). You can use this '+
           'to generate IDE project files instead, see cmake --help for '+
           'possible generator names. Note that only Ninja or Unix Makefile '+
           'based generators will work correctly with yotta.',
           metavar='CMAKE_GENERATOR',
           type=str
        )

    @classmethod
    def _findNinja(cls):
        # sometimes ninja is called ninja-build
        for name in ('ninja', 'ninja-build'):
            if fsutils.which(name) is not None:
                return name
        # default to ninja:
        return 'ninja'

    @classmethod
    def overrideBuildCommand(cls, generator_name, targets=None):
        if targets is None:
            targets = []
        # when we build using cmake --build, the nice colourised output is lost
        # - so override with the actual build command for command-line
        # generators where people will care:
        try:
            r = {
                'Unix Makefiles': ['make'],
                'Ninja': [cls._findNinja()]
            }[generator_name]
            # all of the above build programs take the build targets (e.g.
            # "all") as the last arguments
            if targets is not None:
                r += targets
            return r
        except KeyError:
            return None

    def hintForCMakeGenerator(self, generator_name, component):
        if generator_name in ('Ninja', 'Unix Makefiles'):
            return None
        try:
            name = self.getName()
            component_name = component.getName()
            return {
                'Xcode':
                    'a project file has been generated at ./build/%s/%s.xcodeproj' % (name, component_name),
                'Sublime Text 2 - Ninja':
                    'a project file has been generated at ./build/%s/%s.sublime-project' % (name, component_name),
                'Sublime Text 2 - Unix Makefiles':
                    'a project file has been generated at ./build/%s/%s.sublime-project' % (name, component_name),
                'Eclipse CDT4 - Ninja':
                    'a project file has been generated at ./build/%s/.project' % name,
                'Eclipse CDT4 - Unix Makefiles':
                    'a project file has been generated at ./build/%s/.project' % name
            }[generator_name]
        except KeyError:
            return 'project files for %s have been generated in ./build/%s' % (component_name, name)

    def exec_helper(self, cmd, builddir):
        ''' Execute the given command, returning an error message if an error occured
            or None if the command was succesful.'''
        try:
            child = subprocess.Popen(cmd, cwd=builddir)
            child.wait()
        except OSError as e:
            if e.errno == errno.ENOENT:
                if cmd[0] == 'cmake':
                    return 'CMake is not installed, please follow the installation instructions at http://yottadocs.mbed.com/#installing'
                else:
                    return '%s is not installed' % (cmd[0])
            else:
                return 'command %s failed' % (cmd)
        if child.returncode:
            return 'command %s failed' % (cmd)

    @fsutils.dropRootPrivs
    def build(self, builddir, component, args, release_build=False, build_args=None, targets=None):
        ''' Execute the commands necessary to build this component, and all of
            its dependencies. '''
        if build_args is None:
            build_args = []
        if targets is None:
            targets = []
        # in the future this may be specified in the target description, but
        # for now we only support cmake, so everything is simple:
        build_type = ('Debug', 'RelWithDebInfo')[release_build]
        if build_type:
            cmd = ['cmake', '-D', 'CMAKE_BUILD_TYPE=%s' % build_type, '-G', args.cmake_generator, '.']
        else:
            cmd = ['cmake', '-G', args.cmake_generator, '.']
        res = self.exec_helper(cmd, builddir)
        if res is not None:
            return res

        # work-around various yotta-specific issues with the generated
        # Ninja/project files:
        import cmake_fixups
        cmake_fixups.applyFixupsForFenerator(args.cmake_generator, builddir, component)

        build_command = self.overrideBuildCommand(args.cmake_generator, targets=targets)
        if build_command:
            cmd = build_command + build_args
        else:
            cmd = ['cmake', '--build', builddir]
            if len(targets):
                # !!! FIXME: support multiple targets with the default CMake
                # build command
                cmd += ['--target', targets[0]]
            cmd += build_args
        res = self.exec_helper(cmd, builddir)
        if res is not None:
            return res
        hint = self.hintForCMakeGenerator(args.cmake_generator, component)
        if hint:
            logger.info(hint)

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
            logging.info('found %s at %s', program, exact_matches[0])
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
        ''' Launch a debugger for the specified program. Uses the `debug`
            script if specified by the target, falls back to the `debug` and
            `debugServer` commands if not. `program` is inserted into the
            $program variable in commands.
        '''
        try:
            signal.signal(signal.SIGINT, _ignoreSignal);
            if self.getScript('debug') is not None:
                return self._debugWithScript(builddir, program)
            elif 'debug' in self.description:
                logger.warning(
                    'target %s provides deprecated debug property. It should '+
                    'provide script.debug instead.', self.getName()

                )
                return self._debugDeprecated(builddir, program)
            else:
                return "Target %s does not specify debug commands" % self
        finally:
            # clear the sigint handler
            signal.signal(signal.SIGINT, signal.SIG_DFL);

    @fsutils.dropRootPrivs
    def _debugWithScript(self, builddir, program):
        child = None
        try:
            prog_path = prog_path = self.findProgram(builddir, program)
            if prog_path is None:
                return

            cmd = [
                os.path.expandvars(string.Template(x).safe_substitute(program=prog_path))
                for x in self.getScript('debug')
            ]
            logger.debug('starting debugger: %s', cmd)
            child = subprocess.Popen(
                cmd, cwd = builddir
            )
            child.wait()
            if child.returncode:
                return "debug process exited with status %s" % child.returncode
            child = None
        except:
            # reset the terminal, in case the debugger has screwed it up
            os.system('reset')
            raise
        finally:
            if child is not None:
                try:
                    child.terminate()
                except OSError as e:
                    pass

    @fsutils.dropRootPrivs
    def _debugDeprecated(self, builddir, program):
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
                    logger.debug('starting debug server...')
                    daemon = subprocess.Popen(
                                   self.description[debug_server_prop],
                             cwd = builddir,
                          stdout = dev_null,
                          stderr = dev_null,
                      preexec_fn = _newPGroup
                    )
                else:
                    daemon = None

                cmd = [
                    os.path.expandvars(string.Template(x).safe_substitute(program=prog_path))
                    for x in self.description['debug']
                ]
                logger.debug('starting debugger: %s', cmd)
                child = subprocess.Popen(
                    cmd, cwd = builddir
                )
                child.wait()
                if child.returncode:
                    return "debug process executed with status %s" % child.returncode
                child = None
            except:
                # reset the terminal, in case the debugger has screwed it up
                os.system('reset')
                raise
            finally:
                if child is not None:
                    try:
                        child.terminate()
                    except OSError as e:
                        pass
                if daemon is not None:
                    logger.debug('shutting down debug server...')
                    try:
                        daemon.terminate()
                    except OSError as e:
                        pass

    @fsutils.dropRootPrivs
    def test(self, cwd, test_command, filter_command, forward_args):
        # we assume that test commands are relative to the current directory.
        test_command = './' + test_command
        test_script = self.getScript('test')
        if test_script is None:
            cmd = shlex.split(test_command)
        else:
            cmd = [
                os.path.expandvars(string.Template(x).safe_substitute(program=os.path.abspath(os.path.join(cwd, test_command))))
                for x in test_script
            ] + forward_args

        test_child = None
        test_filter = None
        try:
            logger.debug('running test: %s', cmd)
            if filter_command:
                logger.debug('using output filter command: %s', filter_command)
                test_child = subprocess.Popen(
                    cmd, cwd = cwd, stdout = subprocess.PIPE
                )
                try:
                    test_filter = subprocess.Popen(
                        filter_command, cwd = cwd, stdin = test_child.stdout
                    )
                except OSError as e:
                    logger.error('error starting test output filter "%s": %s', filter_command, e)
                    test_child.terminate()
                    return 1
                test_filter.communicate()
                test_child.terminate()
                test_child.stdout.close()
                returncode = test_filter.returncode
                test_child = None
                test_filter = None
                if returncode:
                    logger.debug("test filter exited with status %s (=fail)", returncode)
                    return 1
            else:
                try:
                    test_child = subprocess.Popen(
                        cmd, cwd = cwd
                    )
                except OSError as e:
                    if e.errno == errno.ENOENT:
                        logger.error('Error: no such file or directory: "%s"', cmd[0])
                        return 1
                    raise
                test_child.wait()
                returncode = test_child.returncode
                test_child = None
                if returncode:
                    logger.debug("test process exited with status %s (=fail)", returncode)
                    return 1
        finally:
            if test_child is not None:
                test_child.terminate()
            if test_filter is not None:
                test_filter.terminate()
        logger.debug("test %s passed", test_command)
        return 0
