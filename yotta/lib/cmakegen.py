# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
import re
import itertools
from collections import defaultdict
from collections import OrderedDict

# bsd licensed - pip install jinja2
from jinja2 import Environment, FileSystemLoader

# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils

Template_Dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

logger = logging.getLogger('cmakegen')

Ignore_Subdirs = set(('build','yotta_modules', 'yotta_targets', 'CMake'))

jinja_environment = Environment(loader=FileSystemLoader(Template_Dir), trim_blocks=True, lstrip_blocks=True)

def replaceBackslashes(s):
    return s.replace('\\', '/')
def sanitizePreprocessorSymbol(sym):
    return re.sub('[^a-zA-Z0-9]', '_', str(sym)).upper()
def sanitizeSymbol(sym):
    return re.sub('[^a-zA-Z0-9]', '_', str(sym))

jinja_environment.filters['replaceBackslashes'] = replaceBackslashes
jinja_environment.filters['sanitizePreprocessorSymbol'] = sanitizePreprocessorSymbol
jinja_environment.globals['list'] = list
jinja_environment.globals['pathJoin'] = os.path.join

class SourceFile(object):
    def __init__(self, fullpath, relpath, lang):
        super(SourceFile, self).__init__()
        self.fullpath = fullpath
        self.relpath = relpath
        self.lang = lang
    def __repr__(self):
        return self.fullpath

class CMakeGen(object):
    def __init__(self, directory, target):
        super(CMakeGen, self).__init__()
        self.buildroot = directory
        logger.info("generate for target: %s" % target)
        self.target = target
        self.configured = False
        self.config_include_file = None
        self.config_json_file = None
        self.build_info_include_file = None
        self.build_uuid = None

    def _writeFile(self, path, contents):
        dirname = os.path.dirname(path)
        fsutils.mkDirP(dirname)
        self.writeIfDifferent(path, contents)

    def configure(self, component, all_dependencies):
        ''' Ensure all config-time files have been generated. Return a
            dictionary of generated items.
        '''
        r = {}

        builddir = self.buildroot

        # only dependencies which are actually valid can contribute to the
        # config data (which includes the versions of all dependencies in its
        # build info) if the dependencies aren't available we can't tell what
        # version they are. Anything missing here should always be a test
        # dependency that isn't going to be used, otherwise the yotta build
        # command will fail before we get here
        available_dependencies = OrderedDict((k, v) for k, v in all_dependencies.items() if v)

        self.set_toplevel_definitions = ''
        if self.build_info_include_file is None:
            self.build_info_include_file, build_info_definitions = self.getBuildInfo(component.path, builddir)
            self.set_toplevel_definitions += build_info_definitions

        if self.config_include_file is None:
            self.config_include_file, config_definitions, self.config_json_file = self._getConfigData(available_dependencies, component, builddir, self.build_info_include_file)
            self.set_toplevel_definitions += config_definitions

        self.configured = True
        return {
            'merged_config_include': self.config_include_file,
               'merged_config_json': self.config_json_file,
               'build_info_include': self.build_info_include_file
        }

    def generateRecursive(self, component, all_components, builddir=None, modbuilddir=None, processed_components=None, application=None):
        ''' generate top-level CMakeLists for this component and its
            dependencies: the CMakeLists are all generated in self.buildroot,
            which MUST be out-of-source

            !!! NOTE: experimenting with a slightly different way of doing
            things here, this function is a generator that yields any errors
            produced, so the correct use is:

            for error in gen.generateRecursive(...):
                print(error)
        '''
        assert(self.configured)

        if builddir is None:
            builddir = self.buildroot
        if modbuilddir is None:
            modbuilddir = os.path.join(builddir, 'ym')

        if processed_components is None:
            processed_components = dict()
        if not self.target:
            yield 'Target "%s" is not a valid build target' % self.target

        toplevel = not len(processed_components)

        logger.debug('generate build files: %s (target=%s)' % (component, self.target))
        # because of the way c-family language includes work we need to put the
        # public header directories of all components that this component
        # depends on (directly OR indirectly) into the search path, which means
        # we need to first enumerate all the direct and indirect dependencies
        recursive_deps = component.getDependenciesRecursive(
            available_components = all_components,
                          target = self.target,
                  available_only = True,
                            test = True
        )
        dependencies = component.getDependencies(
                  all_components,
                          target = self.target,
                  available_only = True,
                            test = True
        )

        for name, dep in dependencies.items():
            # if dep is a test dependency, then it might not be required (if
            # we're not building tests). We don't actually know at this point
            if not dep:
                if dep.isTestDependency():
                    logger.debug('Test dependency "%s" of "%s" is not installed.' % (name, component))
                else:
                    yield 'Required dependency "%s" of "%s" is not installed.' % (name, component)
        # ensure this component is assumed to have been installed before we
        # check for its dependencies, in case it has a circular dependency on
        # itself
        processed_components[component.getName()] = component
        new_dependencies = OrderedDict([(name,c) for name,c in dependencies.items() if c and not name in processed_components])
        self.generate(builddir, modbuilddir, component, new_dependencies, dependencies, recursive_deps, application, toplevel)

        logger.debug('recursive deps of %s:' % component)
        for d in recursive_deps.values():
            logger.debug('    %s' % d)

        processed_components.update(new_dependencies)
        for name, c in new_dependencies.items():
            for error in self.generateRecursive(
                c, all_components, os.path.join(modbuilddir, name), modbuilddir, processed_components, application=application
            ):
                yield error

    def checkStandardSourceDir(self, dirname, component):
        # validate, , validate various things, internal
        from yotta.lib import validate
        err = validate.sourceDirValidationError(dirname, component.getName())
        if err:
            logger.warning(err)

    def _validateListedSubdirsExist(self, component):
        ''' Return true if all the subdirectories which this component lists in
            its module.json file exist (although their validity is otherwise
            not checked).

            If they don't, warning messages are printed.
        '''
        lib_subdirs = component.getLibs(explicit_only=True)
        bin_subdirs = component.getBinaries()

        ok = True
        for d in lib_subdirs:
            if not os.path.exists(os.path.join(component.path, d)):
                logger.warning(
                    "lib directory \"%s\" doesn't exist but is listed in the module.json file of %s", d, component
                )
                ok = False

        for d in bin_subdirs:
            if not os.path.exists(os.path.join(component.path, d)):
                logger.warning(
                    "bin directory \"%s\" doesn't exist but is listed in the module.json file of %s", d, component
                )
                ok = False

        return ok

    def _listSubDirectories(self, component, toplevel):
        ''' return: {
                manual: [list of subdirectories with manual CMakeLists],
                  auto: [list of pairs: (subdirectories name to autogenerate, a list of source files in that dir)],
                   bin: {dictionary of subdirectory name to binary name},
                   lib: {dictionary of subdirectory name to binary name},
                  test: [list of directories that build tests],
              resource: [list of directories that contain resources]
            }
        '''
        manual_subdirs = []
        auto_subdirs = []
        header_subdirs = []
        lib_subdirs = component.getLibs()
        bin_subdirs = component.getBinaries()
        test_subdirs = []
        resource_subdirs = []
        # if the application or library is set to get the sources from top level ("."),
        # they'll be acumulated into a single array (top_sources below).
        top_sources = []
        start_on_top = "." in [os.path.normpath(x) for x in list(lib_subdirs.keys()) + list(bin_subdirs.keys())]
        for f in sorted(os.listdir(component.path)):
            if f in Ignore_Subdirs or f.startswith('.') or f.startswith('_'):
                continue
            check_cmakefile_path = os.path.join(f, 'CMakeLists.txt')
            if os.path.isfile(os.path.join(component.path, check_cmakefile_path)) and not \
                    component.ignores(check_cmakefile_path):
                self.checkStandardSourceDir(f, component)
                # if the subdirectory has a CMakeLists.txt in it (and it isn't
                # ignored), then delegate to that:
                manual_subdirs.append(f)
                # tests only supported in the `test` directory for now
                if f in ('test',):
                    test_subdirs.append(f)
            else:
                if os.path.isfile(os.path.join(component.path, f)):
                    # top level source: check if it should be included
                    if not component.ignores(f) and start_on_top:
                        sf = self.createSourceFile(f, os.path.join(component.path, f), ".")
                        if sf is not None:
                            top_sources.append(sf)
                else:
                    # otherwise, if the directory has source files, and is listed
                    # as a source/test directory, generate a CMakeLists in the
                    # corresponding temporary directory, and add that.
                    sources = self.containsSourceFiles(os.path.join(component.path, f), component)
                    if sources:
                        if f in ('test',):
                            auto_subdirs.append((f, sources))
                            test_subdirs.append(f)
                        elif start_on_top:
                            # include the sources in this directory only if it's not
                            # a potential test directory
                            from yotta.lib import validate
                            if not validate.isPotentialTestDir(f):
                                top_sources.extend(sources)
                                if f == component.getName():
                                    header_subdirs.append((f, sources))
                        elif os.path.normpath(f) in [fsutils.fullySplitPath(x)[0] for x in lib_subdirs] or \
                             os.path.normpath(f) in [fsutils.fullySplitPath(x)[0] for x in bin_subdirs]:
                            for full_subpath in list(lib_subdirs.keys()) + list(bin_subdirs.keys()):
                                if fsutils.fullySplitPath(full_subpath)[0] == os.path.normpath(f):
                                    # this might be a sub-sub directory, in which
                                    # case we need to re-calculate the sources just
                                    # for the part we care about:
                                    sources = self.containsSourceFiles(os.path.join(component.path, full_subpath), component)
                                    auto_subdirs.append((full_subpath, sources))
                        elif f == component.getName():
                            header_subdirs.append((f, sources))
                    elif toplevel and \
                         ((f in ('test',)) or \
                          (os.path.normpath(f) in lib_subdirs or start_on_top) or \
                          (os.path.normpath(f) in bin_subdirs or start_on_top) and not \
                          component.ignores(f)):
                        # (if there aren't any source files then do nothing)
                        # !!! FIXME: ensure this warning is covered in tests
                        logger.warning("subdirectory \"%s\" of %s was ignored because it doesn't appear to contain any source files", f, component)

            # 'resource' directory also has special meaning, but there's no
            # pattern for the files which might be in here:
            if f in ('resource',):
                resource_subdirs.append(os.path.join(component.path, f))

            # issue a warning if a differently cased or common misspelling of a
            # standard directory name was encountered:
            check_directory_name_cases = list(lib_subdirs.keys()) + list(bin_subdirs.keys()) + ['test', 'resource']
            if f.lower() in check_directory_name_cases + ['src'] and not \
               f in check_directory_name_cases and not \
               component.ignores(f):
                self.checkStandardSourceDir(f, component)
        if top_sources:
            # all the top level sources are grouped into a single cmake-generated directory
            # which is given the same name as the component
            auto_subdirs.append((component.getName(), top_sources))

        return {
            "manual": manual_subdirs,
              "auto": auto_subdirs,
           "headers": header_subdirs,
               "bin": {component.getName(): component.getName()} if (start_on_top and component.isApplication()) else bin_subdirs,
               "lib": {component.getName(): component.getName()} if (start_on_top and not component.isApplication()) else lib_subdirs,
              "test": test_subdirs,
          "resource": resource_subdirs
        }

    def _definitionsForConfig(self, config, key_path=None):
        if key_path is None:
            key_path = list()
        key_prefix = '_'.join([sanitizePreprocessorSymbol(x) for x in key_path])
        r = []
        if len(key_prefix):
            r.append((key_prefix,None))
        for (k, v) in config.items():
            if isinstance(v, dict):
                r += self._definitionsForConfig(v, key_path + [k])
            else:
                # Don't validate the value here (we wouldn't know where an
                # invalid value came from, so the error message would be
                # unhelpful) - the target schema should validate values, or if
                # that isn't possible then the target should check when loading
                if isinstance(v, bool):
                    # convert bool to 1/0, since we can't know the availability
                    # of a C bool type
                    v = 1 if v else 0
                r.append(('%s_%s' % (key_prefix, sanitizePreprocessorSymbol(k)), v))
        return r

    def _getConfigData(self, all_dependencies, component, builddir, build_info_header_path):
        ''' returns (path_to_config_header, cmake_set_definitions) '''
        # ordered_json, , read/write ordered json, internal
        from yotta.lib import ordered_json
        add_defs_header = ''
        set_definitions = ''
        # !!! backwards-compatible "TARGET_LIKE" definitions for the top-level
        # of the config. NB: THESE WILL GO AWAY
        definitions = []
        definitions.append(('TARGET', sanitizePreprocessorSymbol(self.target.getName())))
        definitions.append(('TARGET_LIKE_%s' % sanitizePreprocessorSymbol(self.target.getName()),None))

        # make the path to the build-info header available both to CMake and
        # in the preprocessor:
        full_build_info_header_path = replaceBackslashes(os.path.abspath(build_info_header_path))
        logger.debug('build info header include path: "%s"', full_build_info_header_path)
        definitions.append(('YOTTA_BUILD_INFO_HEADER', '"'+full_build_info_header_path+'"'))

        for target in self.target.getSimilarTo_Deprecated():
            if '*' not in target:
                definitions.append(('TARGET_LIKE_%s' % sanitizePreprocessorSymbol(target),None))

        merged_config = self.target.getMergedConfig()
        logger.debug('target configuration data: %s', merged_config)
        definitions += self._definitionsForConfig(merged_config, ['YOTTA', 'CFG'])

        add_defs_header += '// yotta config data (including backwards-compatible definitions)\n'

        for k, v in definitions:
            if v is not None:
                add_defs_header += '#define %s %s\n' % (k, v)
                set_definitions += 'set(%s %s)\n' % (k, v)
            else:
                add_defs_header += '#define %s\n' % k
                set_definitions += 'set(%s TRUE)\n' % k

        add_defs_header += '\n// version definitions\n'

        for dep in list(all_dependencies.values()) + [component]:
            add_defs_header += "#define YOTTA_%s_VERSION_STRING \"%s\"\n" % (sanitizePreprocessorSymbol(dep.getName()), str(dep.getVersion()))
            add_defs_header += "#define YOTTA_%s_VERSION_MAJOR %d\n" % (sanitizePreprocessorSymbol(dep.getName()), dep.getVersion().major())
            add_defs_header += "#define YOTTA_%s_VERSION_MINOR %d\n" % (sanitizePreprocessorSymbol(dep.getName()), dep.getVersion().minor())
            add_defs_header += "#define YOTTA_%s_VERSION_PATCH %d\n" % (sanitizePreprocessorSymbol(dep.getName()), dep.getVersion().patch())

        # add the component's definitions
        defines = component.getDefines()
        if defines:
            add_defs_header += "\n// direct definitions (defines.json)\n"
            for name, value in defines.items():
                add_defs_header += "#define %s %s\n" % (name, value)
            add_defs_header += '\n'

        # use -include <definitions header> instead of lots of separate
        # defines... this is compiler specific, but currently testing it
        # out for gcc-compatible compilers only:
        config_include_file = os.path.join(builddir, 'yotta_config.h')
        config_json_file    = os.path.join(builddir, 'yotta_config.json')
        set_definitions += 'set(YOTTA_CONFIG_MERGED_JSON_FILE \"%s\")\n' % replaceBackslashes(os.path.abspath(config_json_file))

        self._writeFile(
            config_include_file,
            '#ifndef __YOTTA_CONFIG_H__\n'+
            '#define __YOTTA_CONFIG_H__\n'+
            add_defs_header+
            '#endif // ndef __YOTTA_CONFIG_H__\n'
        )
        self._writeFile(
            config_json_file,
            ordered_json.dumps(merged_config)
        )
        return (config_include_file, set_definitions, config_json_file)

    def getBuildInfo(self, sourcedir, builddir):
        ''' Write the build info header file, and return (path_to_written_header, set_cmake_definitions) '''
        cmake_defs = ''
        preproc_defs = '// yotta build info, #include YOTTA_BUILD_INFO_HEADER to access\n'
        # standard library modules
        import datetime
        # vcs, , represent version controlled directories, internal
        from yotta.lib import vcs

        now = datetime.datetime.utcnow()
        vcs_instance = vcs.getVCS(sourcedir)
        if self.build_uuid is None:
            import uuid
            self.build_uuid = uuid.uuid4()

        definitions = [
            ('YOTTA_BUILD_YEAR',   now.year,        'UTC year'),
            ('YOTTA_BUILD_MONTH',  now.month,       'UTC month 1-12'),
            ('YOTTA_BUILD_DAY',    now.day,         'UTC day 1-31'),
            ('YOTTA_BUILD_HOUR',   now.hour,        'UTC hour 0-24'),
            ('YOTTA_BUILD_MINUTE', now.minute,      'UTC minute 0-59'),
            ('YOTTA_BUILD_SECOND', now.second,      'UTC second 0-61'),
            ('YOTTA_BUILD_UUID',   self.build_uuid, 'unique random UUID for each build'),
        ]
        if vcs_instance is not None:
            commit_id = None
            repotype = vcs_instance.__class__.__name__
            try:
                commit_id = vcs_instance.getCommitId()
            except vcs.VCSNotInstalled as e:
                logger.warning('%s is not installed, VCS status build info is not available', repotype)
                commit_id = None
            except vcs.VCSError as e:
                logger.debug('%s', e)
                logger.warning(
                    'error detecting build info: "%s", build info is not available to the build. Please check that this is a valid %s repository!',
                    str(e).split('\n')[0],
                    repotype
                )
            if commit_id is not None:
                clean_state = int(vcs_instance.isClean())
                description = vcs_instance.getDescription()
                definitions += [
                    ('YOTTA_BUILD_VCS_ID',    commit_id,   'git or mercurial hash'),
                    ('YOTTA_BUILD_VCS_CLEAN', clean_state, 'evaluates true if the version control system was clean, otherwise false'),
                    ('YOTTA_BUILD_VCS_DESCRIPTION', description, 'git describe or mercurial equivalent')
                ]

        for d in definitions:
            preproc_defs += '#define %s %s // %s\n' % d
            cmake_defs   += 'set(%s "%s") # %s\n' % d

        buildinfo_include_file = os.path.join(builddir, 'yotta_build_info.h')
        self._writeFile(
            buildinfo_include_file,
            '#ifndef __YOTTA_BUILD_INFO_H__\n'+
            '#define __YOTTA_BUILD_INFO_H__\n'+
            preproc_defs+
            '#endif // ndef __YOTTA_BUILD_INFO_H__\n'
        )
        return (buildinfo_include_file, cmake_defs)

    def generate(
            self, builddir, modbuilddir, component, active_dependencies, immediate_dependencies, all_dependencies, application, toplevel
        ):
        ''' active_dependencies is the dictionary of components that need to be
            built for this component, but will not already have been built for
            another component.
        '''

        include_root_dirs = ''
        if application is not None and component is not application:
            include_root_dirs += 'include_directories("%s")\n' % replaceBackslashes(application.path)

        include_sys_dirs = ''
        include_other_dirs = ''
        for name, c in itertools.chain(((component.getName(), component),), all_dependencies.items()):
            if c is not component and c.isTestDependency():
                continue
            include_root_dirs += 'include_directories("%s")\n' % replaceBackslashes(c.path)
            dep_sys_include_dirs = c.getExtraSysIncludes()
            for d in dep_sys_include_dirs:
                include_sys_dirs += 'include_directories(SYSTEM "%s")\n' % replaceBackslashes(os.path.join(c.path, d))
            dep_extra_include_dirs = c.getExtraIncludes()
            for d in dep_extra_include_dirs:
                include_other_dirs += 'include_directories("%s")\n' % replaceBackslashes(os.path.join(c.path, d))

        add_depend_subdirs = ''
        for name, c in active_dependencies.items():
            depend_subdir = replaceBackslashes(os.path.join(modbuilddir, name))
            relpath = replaceBackslashes(os.path.relpath(depend_subdir, self.buildroot))
            add_depend_subdirs += \
                'add_subdirectory(\n' \
                '   "%s"\n' \
                '   "${CMAKE_BINARY_DIR}/%s"\n' \
                ')\n' \
                % (depend_subdir, relpath)

        delegate_to_existing = None
        delegate_build_dir = None

        module_is_empty = False
        if os.path.isfile(os.path.join(component.path, 'CMakeLists.txt')) and not component.ignores('CMakeLists.txt'):
            # adding custom CMake is a promise to generate a library: so the
            # module is never empty in this case.
            delegate_to_existing = component.path
            add_own_subdirs = []
            logger.debug("delegate to build dir: %s", builddir)
            delegate_build_dir = os.path.join(builddir, 'existing')
        else:
            # !!! TODO: if they don't exist, that should possibly be a fatal
            # error, not just a warning
            self._validateListedSubdirsExist(component)

            subdirs = self._listSubDirectories(component, toplevel)
            manual_subdirs      = subdirs['manual']
            autogen_subdirs     = subdirs['auto']
            binary_subdirs      = subdirs['bin']
            lib_subdirs         = subdirs['lib']
            test_subdirs        = subdirs['test']
            resource_subdirs    = subdirs['resource']
            header_subdirs      = subdirs['headers']
            logger.debug("%s lib subdirs: %s, bin subdirs: %s", component, lib_subdirs, binary_subdirs)

            add_own_subdirs = []
            for f in manual_subdirs:
                if os.path.isfile(os.path.join(component.path, f, 'CMakeLists.txt')):
                    # if this module is a test dependency, then don't recurse
                    # to building its own tests.
                    if f in test_subdirs and component.isTestDependency():
                        continue
                    add_own_subdirs.append(
                        (os.path.join(component.path, f), f)
                    )
            # names of all directories at this level with stuff in: used to figure
            # out what to link automatically
            all_subdirs = manual_subdirs + [x[0] for x in autogen_subdirs]

            # first check if this module is empty:
            if component.isTestDependency():
                if len(autogen_subdirs) + len(add_own_subdirs) == 0:
                    module_is_empty = True
            else:
                if len(autogen_subdirs) + len(add_own_subdirs) <= len(test_subdirs):
                    module_is_empty = True

            # autogenerate CMakeLists for subdirectories as appropriate:
            for f, source_files in autogen_subdirs:
                if f in test_subdirs:
                    # if this module is a test dependency, then don't recurse
                    # to building its own tests.
                    if component.isTestDependency():
                        continue
                    self.generateTestDirList(
                        builddir, f, source_files, component, immediate_dependencies, toplevel=toplevel, module_is_empty=module_is_empty
                    )
                else:
                    if f in binary_subdirs:
                        is_executable = True
                        object_name = binary_subdirs[f]
                    else:
                        # not a test subdir or binary subdir: it must be a lib
                        # subdir
                        assert(f in lib_subdirs)
                        object_name = lib_subdirs[f]

                    for header_dir, header_files in header_subdirs:
                        source_files.extend(header_files)

                    self.generateSubDirList(
                                      builddir = builddir,
                                       dirname = f,
                                  source_files = source_files,
                                     component = component,
                                   all_subdirs = all_subdirs,
                        immediate_dependencies = immediate_dependencies,
                                   object_name = object_name,
                              resource_subdirs = resource_subdirs,
                                 is_executable = (f in binary_subdirs)
                    )
                add_own_subdirs.append(
                    (os.path.join(builddir, f), f)
                )

            # from now on, completely forget that this component had any tests
            # if it is itself a test dependency:
            if component.isTestDependency():
                test_subdirs = []

            # if we're not building anything other than tests, and this is a
            # library module (not a binary) then we need to generate a dummy
            # library so that this component can still be linked against
            if module_is_empty:
                if len(binary_subdirs):
                    logger.warning('nothing to build!')
                else:
                    add_own_subdirs.append(self.createDummyLib(
                        component, builddir, [x[0] for x in immediate_dependencies.items() if not x[1].isTestDependency()]
                    ))

        toolchain_file_path = os.path.join(builddir, 'toolchain.cmake')
        if toplevel:
            # generate the top-level toolchain file:
            template = jinja_environment.get_template('toolchain.cmake')
            file_contents = template.render({  #pylint: disable=no-member
                                   # toolchain files are provided in hierarchy
                                   # order, but the template needs them in reverse
                                   # order (base-first):
                "toolchain_files": self.target.getToolchainFiles()
            })
            self._writeFile(toolchain_file_path, file_contents)

        # generate the top-level CMakeLists.txt
        template = jinja_environment.get_template('base_CMakeLists.txt')

        relpath = os.path.relpath(builddir, self.buildroot)

        file_contents = template.render({ #pylint: disable=no-member
                            "toplevel": toplevel,
                         "target_name": self.target.getName(),
                     "set_definitions": self.set_toplevel_definitions,
                      "toolchain_file": toolchain_file_path,
                           "component": component,
                             "relpath": relpath,
                   "include_root_dirs": include_root_dirs,
                    "include_sys_dirs": include_sys_dirs,
                  "include_other_dirs": include_other_dirs,
                  "add_depend_subdirs": add_depend_subdirs,
                     "add_own_subdirs": add_own_subdirs,
                 "config_include_file": self.config_include_file,
                         "delegate_to": delegate_to_existing,
                  "delegate_build_dir": delegate_build_dir,
                 "active_dependencies": active_dependencies,
                     "module_is_empty": module_is_empty,
                      "cmake_includes": self.target.getAdditionalIncludes()
        })
        self._writeFile(os.path.join(builddir, 'CMakeLists.txt'), file_contents)

    def createDummyLib(self, component, builddir, link_dependencies):
        safe_name        = sanitizeSymbol(component.getName())
        dummy_dirname    = 'yotta_dummy_lib_%s' % safe_name
        dummy_cfile_name = 'dummy.c'
        logger.debug("create dummy lib: %s, %s, %s" % (safe_name, dummy_dirname, dummy_cfile_name))

        cmake_files = []
        source_dir = os.path.join(component.path, 'source')
        if os.path.exists(source_dir):
            for root, dires, files in os.walk(os.path.join(component.path, 'source')):
                for f in files:
                    name, ext = os.path.splitext(f)
                    if ext.lower() == '.cmake' and not component.ignores(os.path.relpath(os.path.join(root, f), component.path)):
                        cmake_files.append(os.path.join(root, f))

        dummy_template = jinja_environment.get_template('dummy_CMakeLists.txt')

        dummy_cmakelists = dummy_template.render({ #pylint: disable=no-member
                   "cfile_name": dummy_cfile_name,
                      "libname": component.getName(),
            "link_dependencies": link_dependencies,
                  "cmake_files": cmake_files
        })
        self._writeFile(os.path.join(builddir, dummy_dirname, "CMakeLists.txt"), dummy_cmakelists)
        dummy_cfile = "void __yotta_dummy_lib_symbol_%s(){}\n" % safe_name
        self._writeFile(os.path.join(builddir, dummy_dirname, dummy_cfile_name), dummy_cfile)
        return (os.path.join(builddir, dummy_dirname), dummy_dirname)

    def writeIfDifferent(self, fname, contents):
        try:
            with open(fname, "r+") as f:
                current_contents = f.read()
                if current_contents != contents:
                    f.seek(0)
                    f.write(contents)
                    f.truncate()
        except IOError:
            with open(fname, "w") as f:
                f.write(contents)

    def generateTestDirList(self, builddir, dirname, source_files, component, immediate_dependencies, toplevel=False, module_is_empty=False):
        logger.debug('generate CMakeLists.txt for directory: %s' % os.path.join(component.path, dirname))

        link_dependencies = [x for x in immediate_dependencies]
        fname = os.path.join(builddir, dirname, 'CMakeLists.txt')

        # group the list of source files by subdirectory: generate one test for
        # each subdirectory, and one test for each file at the top level
        subdirs = defaultdict(list)
        toplevel_srcs = []
        for f in source_files:
            if f.lang in ('c', 'cpp', 'objc', 's'):
                subrelpath = os.path.relpath(f.relpath, dirname)
                subdir = fsutils.fullySplitPath(subrelpath)[0]
                if subdir and subdir != subrelpath:
                    subdirs[subdir].append(f)
                else:
                    toplevel_srcs.append(f)

        tests = []
        for f in toplevel_srcs:
            object_name = '%s-test-%s' % (
                component.getName(), os.path.basename(os.path.splitext(str(f))[0]).lower()
            )
            tests.append([[str(f)], object_name, [f.lang]])
        for subdirname, sources in sorted(subdirs.items(), key=lambda x: x[0]):
            object_name = '%s-test-%s' % (
                component.getName(), fsutils.fullySplitPath(subdirname)[0].lower()
            )
            tests.append([[str(f) for f in sources], object_name, [f.lang for f in sources]])

        # link tests against the main executable
        if not module_is_empty:
            link_dependencies.append(component.getName())

        # Find cmake files
        cmake_files = []
        for root, dires, files in os.walk(os.path.join(component.path, dirname)):
            for f in files:
                name, ext = os.path.splitext(f)
                if ext.lower() == '.cmake' and not component.ignores(os.path.relpath(os.path.join(root, f), component.path)):
                    cmake_files.append(os.path.join(root, f))

        test_template = jinja_environment.get_template('test_CMakeLists.txt')

        file_contents = test_template.render({ #pylint: disable=no-member
             'source_directory':os.path.join(component.path, dirname),
                        'tests':tests,
            'link_dependencies':link_dependencies,
                  'cmake_files': cmake_files,
             'exclude_from_all': (not toplevel),
            'test_dependencies': [x[1] for x in immediate_dependencies.items() if x[1].isTestDependency()]
        })

        self._writeFile(fname, file_contents)

    def generateSubDirList(self, builddir, dirname, source_files, component, all_subdirs, immediate_dependencies, object_name, resource_subdirs, is_executable):
        logger.debug('generate CMakeLists.txt for directory: %s' % os.path.join(component.path, dirname))

        link_dependencies = [x[0] for x in immediate_dependencies.items() if not x[1].isTestDependency()]
        fname = os.path.join(builddir, dirname, 'CMakeLists.txt')

        assert(object_name)
        object_name = object_name

        # if we're building the main library, or an executable for this
        # component, then we should link against all the other directories
        # containing cmakelists:
        link_dependencies += [x for x in all_subdirs if x not in ('source', 'test', dirname)]

        # Find resource files
        resource_files = []
        for f in resource_subdirs:
            for root, dires, files in os.walk(f):
                if root.endswith(".xcassets") or root.endswith(".bundle"):
                    resource_files.append(root)
                    del dires[:]
                else:
                    for f in files:
                        resource_files.append(os.path.join(root, f))

        # Find cmake files
        cmake_files = []
        for root, dires, files in os.walk(os.path.join(component.path, dirname)):
            for f in files:
                name, ext = os.path.splitext(f)
                if ext.lower() == '.cmake' and not component.ignores(os.path.relpath(os.path.join(root, f), component.path)):
                    cmake_files.append(os.path.join(root, f))

        subdir_template = jinja_environment.get_template('subdir_CMakeLists.txt')

        file_contents = subdir_template.render({ #pylint: disable=no-member
                'source_directory': os.path.join(component.path, dirname),
             "config_include_file": self.config_include_file,
                      'executable': is_executable,
                      'file_names': [str(f) for f in source_files],
                     'object_name': object_name,
               'link_dependencies': link_dependencies,
                       'languages': set(f.lang for f in source_files),
                    'source_files': set((f.fullpath, f.lang) for f in source_files),
                  'resource_files': resource_files,
                     'cmake_files': cmake_files
        })

        self._writeFile(fname, file_contents)

    def createSourceFile(self, f, fullpath, relpath):
        c_exts          = set(('.c',))
        cpp_exts        = set(('.cpp','.cc','.cxx'))
        asm_exts        = set(('.s',))
        objc_exts       = set(('.m', '.mm'))
        header_exts     = set(('.h',))
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext in c_exts:
            return SourceFile(fullpath, relpath, 'c')
        elif ext in cpp_exts:
            return SourceFile(fullpath, relpath, 'cpp')
        elif ext in asm_exts:
            return SourceFile(fullpath, relpath, 's')
        elif ext in objc_exts:
            return SourceFile(fullpath, relpath, 'objc')
        elif ext in header_exts:
            return SourceFile(fullpath, relpath, 'header')
        else:
            return None

    def containsSourceFiles(self, directory, component):
        sources = []
        for root, dires, files in os.walk(directory):
            for f in sorted(files):
                fullpath = os.path.join(root, f)
                relpath  = os.path.relpath(fullpath, component.path)
                if component.ignores(relpath):
                    continue
                sf = self.createSourceFile(f, fullpath, relpath)
                if sf is not None:
                    sources.append(sf)
        return sources

