# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging


# validate, , validate things, internal
from .lib import validate
# CMakeGen, , generate build files, internal
from .lib import cmakegen
# Target, , represents an installed target, internal
from .lib import target
# install, , install subcommand, internal
from . import install

def addOptions(parser, add_build_targets=True):
    parser.add_argument('-g', '--generate-only', dest='generate_only',
        action='store_true', default=False,
        help='Only generate CMakeLists, don\'t run CMake or build'
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

def installAndBuild(args, following_args):
    ''' Perform the build command, but provide detailed error information.
        Returns {status:0, build_status:0, generate_status:0, install_status:0} on success.
        If status: is nonzero there was some sort of error. Other properties
        are optional, and may not be set if that step was not attempted.
    '''
    build_status = generate_status = install_status = 0

    if not hasattr(args, 'build_targets'):
        vars(args)['build_targets'] = []

    if 'test' in args.build_targets:
        logging.error('Cannot build "test". Use "yotta test" to run tests.')
        return {'status':1}

    cwd = os.getcwd()
    c = validate.currentDirectoryModule()
    if not c:
        return {'status':1}

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return {'status':1}

    # run the install command before building, we need to add some options the
    # install command expects to be present to do this:
    vars(args)['component'] = None
    vars(args)['act_globally'] = False
    if not hasattr(args, 'install_test_deps'):
        if 'all_tests' in args.build_targets:
            vars(args)['install_test_deps'] = 'all'
        elif not len(args.build_targets):
            vars(args)['install_test_deps'] = 'own'
        else:
            # If the named build targets include tests from other modules, we
            # need to install the deps for those modules. To do this we need to
            # be able to tell which module a library belongs to, which is not
            # straightforward (especially if there is custom cmake involved).
            # That's why this is 'all', and not 'none'.
            vars(args)['install_test_deps'] = 'all'

    # install may exit non-zero for non-fatal errors (such as incompatible
    # version specs), which it will display
    install_status = install.execCommand(args, [])

    builddir = os.path.join(cwd, 'build', target.getName())

    all_components = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )

    # if a dependency is missing the build will almost certainly fail, so don't try
    missing = 0
    for d in all_components.values():
        if not d and not (d.isTestDependency() and args.install_test_deps != 'all'):
            logging.error('%s not available' % os.path.split(d.path)[1])
            missing += 1
    if missing:
        logging.error('Missing dependencies prevent build. Use `yotta ls` to list them.')
        return {'status': 1, 'install_status':install_status, 'missing_status':missing}

    generator = cmakegen.CMakeGen(builddir, target)
    app = c if len(c.getBinaries()) else None
    for error in generator.generateRecursive(c, all_components, builddir, application=app):
        logging.error(error)
        generate_status = 1

    if (not hasattr(args, 'generate_only')) or (not args.generate_only):
        error = target.build(
                builddir, c, args, release_build=args.release_build,
                build_args=following_args, targets=args.build_targets
        )
        if error:
            logging.error(error)
            build_status = 1

    return {
                'status': build_status or generate_status or install_status,
        'missing_status': missing,
          'build_status': build_status,
       'generate_status': generate_status,
        'install_status': install_status
    }

