# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
import shutil


# validate, , validate things, internal
from yotta.lib import validate
# access_common, , things shared between different component access modules, internal
from yotta.lib import access_common
# CMakeGen, , generate build files, internal
from yotta.lib import cmakegen
# Target, , represents an installed target, internal
from yotta.lib import target
# settings, , load and save settings, internal
from yotta.lib import settings
# paths
from yotta.lib import paths
from yotta.lib import fsutils
# install, , install subcommand, internal
from yotta import install
# --config option, , , internal
from yotta import options

def addOptions(parser, add_build_targets=True):
    options.config.addTo(parser)
    parser.add_argument('-g', '--generate-only', dest='generate_only',
        action='store_true', default=False,
        help='Only generate CMakeLists, don\'t run CMake or build'
    )
    parser.add_argument('-x', '--export', dest='export',
        default=False, const=True, nargs='?',
        help=(
            'Export mode. If flag is set, generates builds without reference to Yotta.'
            '[optional] Specify an output path to receive the clean build'
        )
    )
    parser.add_argument('-r', '--release-build', dest='release_build', action='store_true', default=True)
    parser.add_argument('-d', '--debug-build', dest='release_build', action='store_false', default=True)
    # the target class adds its own build-system specific options. In the
    # future we probably want to load these from a target instance, rather than
    # from the class
    target.DerivedTarget.addBuildOptions(parser)

    if add_build_targets:
        parser.add_argument(
            "build_targets", metavar='MODULE_TO_BUILD', nargs='*', type=str, default=[],
            help='List modules or programs to build (omit to build the default '+
                 'set, or use "all_tests" to build all tests, including those '+
                 'of dependencies).'
        )

def execCommand(args, following_args):
    status = installAndBuild(args, following_args)
    return status['status']

def runScriptWithModules(module, sub_modules, script, script_environment):
    module.runScript(script, script_environment)
    [mod.runScript(script, script_environment) for mod in sub_modules if mod]

def installAndBuild(args, following_args):
    ''' Perform the build command, but provide detailed error information.
        Returns {status:0, build_status:0, generate_status:0, install_status:0} on success.
        If status: is nonzero there was some sort of error. Other properties
        are optional, and may not be set if that step was not attempted.
    '''
    build_status = 0
    generate_status = 0
    error = None
    args_dict = vars(args)
    export_mode_or_path = args_dict.get('export')

    if export_mode_or_path:
        logging.info('this build will be configured for exporting')
        new_modules = settings.getProperty('build', 'vendor_modules_directory') or 'vendor_modules'
        new_targets = settings.getProperty('build', 'vendor_targets_directory') or 'vendor_targets'
        new_build_modules = settings.getProperty('build', 'built_modules_directory') or 'modules'
        # to save downloading the cached files, copy the old cache
        try:
            if not os.path.exists(new_modules):
                shutil.copytree(paths.Modules_Folder, new_modules)
                shutil.copytree(paths.Targets_Folder, new_targets)
        except Exception as e:
            logging.error(e)
            logging.error('failed to use existing cache; rebuilding')

        paths.Modules_Folder = new_modules
        paths.Targets_Folder = new_targets
        paths.BUILT_MODULES_DIR = new_build_modules

    args_dict.setdefault('build_targets', [])

    if 'test' in args.build_targets:
        logging.error('Cannot build "test". Use "yotta test" to run tests.')
        return {'status':1}

    c = validate.currentDirectoryModule()
    if not c:
        return {'status':1}

    try:
        target, errors = c.satisfyTarget(args.target, additional_config=args.config)
    except access_common.AccessException as e:
        logging.error(e)
        return {'status':1}
    if errors:
        for error in errors:
            logging.error(error)
        return {'status':1}

    # run the install command before building, we need to add some options the
    # install command expects to be present to do this:
    args_dict['component'] = None
    args_dict['act_globally'] = False
    if not hasattr(args, 'install_test_deps'):
        if 'all_tests' in args.build_targets:
            args_dict['install_test_deps'] = 'all'
        elif not len(args.build_targets):
            args_dict['install_test_deps'] = 'own'
        else:
            # If the named build targets include tests from other modules, we
            # need to install the deps for those modules. To do this we need to
            # be able to tell which module a library belongs to, which is not
            # straightforward (especially if there is custom cmake involved).
            # That's why this is 'all', and not 'none'.
            args_dict['install_test_deps'] = 'all'

    # install may exit non-zero for non-fatal errors (such as incompatible
    # version specs), which it will display
    install_status = install.execCommand(args, [])

    builddir = os.path.join(os.getcwd(), paths.DEFAULT_BUILD_DIR, target.getName())

    all_deps = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )

    # if a dependency is missing the build will almost certainly fail, so don't try
    missing = 0
    for d in all_deps.values():
        if not d and not (d.isTestDependency() and args.install_test_deps != 'all'):
            logging.error('%s not available' % os.path.split(d.path)[1])
            missing += 1
    if missing:
        logging.error('Missing dependencies prevent build. Use `yotta ls` to list them.')
        return {'status': 1, 'install_status':install_status, 'missing_status':missing}

    generator = cmakegen.CMakeGen(builddir, target)
    # only pass available dependencies to
    config = generator.configure(c, all_deps)
    logging.debug("config done, merged config: %s", config['merged_config_json'])

    script_environment = {
        'YOTTA_MERGED_CONFIG_FILE': str(config['merged_config_json'])
    }
    # run pre-generate scripts for all components:
    runScriptWithModules(c, all_deps.values(), 'preGenerate', script_environment)

    app = c if len(c.getBinaries()) else None
    for error in generator.generateRecursive(c, all_deps, builddir, application=app):
        logging.error(error)
        generate_status = 1

    logging.debug("generate done.")
    # run pre-build scripts for all components:
    runScriptWithModules(c, all_deps.values(), 'preBuild', script_environment)

    if export_mode_or_path and export_mode_or_path is not True:
        # these export exclusions apply at any level of the directory structure
        excludes = {
            '.module.json',
            '.yotta.json',
            '.yotta_origin.json',
            'module.json',
            'target.json',
            'yotta_modules',
            'yotta_targets'
        }
        export_to = os.path.abspath(export_mode_or_path)
        logging.info('exporting unbuilt project source and dependencies to %s', export_to)
        check = os.path.join(export_to, 'source')  # this might be insufficient, or indeed misleading.
        if os.path.exists(export_to) and os.listdir(export_to) and not os.path.exists(check):
            # as the export can be any path we do a sanity check before calling 'rmRf'
            raise Exception(
                'Aborting export: directory is not empty and does not look like a previous export'
                ' (expecting: %s)'
                % (check)
            )
        fsutils.rmRf(export_to)
        shutil.copytree(src='.', dst=export_to, ignore=lambda a, b: excludes)

    if args_dict.get('generate_only'):
        logging.info('skipping build step')
    else:
        # build in the current directory
        error = target.build(
                builddir, c, args, release_build=args.release_build,
                build_args=following_args, targets=args.build_targets
        )

        if error:
            logging.error(error)
            build_status = 1
        else:
            # post-build scripts only get run if we were successful:
            runScriptWithModules(c, all_deps.values(), 'postBuild', script_environment)

        if install_status:
            logging.warning(
                "There were also errors installing and resolving dependencies, "+
                "which may have caused the build failure: see above, or run "+
                "`yotta install` for details."
            )

    return {
                'status': build_status or generate_status or install_status,
        'missing_status': missing,
          'build_status': build_status,
       'generate_status': generate_status,
        'install_status': install_status
    }

