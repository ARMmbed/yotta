# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
import re

# validate, , validate things, internal
from .lib import validate
# Target, , represents an installed target, internal
from .lib import target
# fsutils, , misc filesystem utils, internal
from .lib import fsutils
# build, , build subcommand, internal
from . import build


def addOptions(parser):
    parser.add_argument(
        "--list", '-l', dest='list_only', default=False, action='store_true',
        help='List the tests that would be run, but don\'t run them. Implies --no-build'
    )
    parser.add_argument(
        "--no-build", '-n', dest='build', default=True, action='store_false',
        help='Don\'t build first.'
    )
    parser.add_argument(
        "tests", metavar='TEST_TO_RUN', nargs='*', type=str, default=[],
        help='List tests to run (omit to run the default set, or use "all" to run all).'
    )

    # relevant build options:
    parser.add_argument('-r', '--release-build', dest='release_build', action='store_true', default=True)
    parser.add_argument('-d', '--debug-build', dest='release_build', action='store_false', default=True)
    target.DerivedTarget.addBuildOptions(parser)


def findCTests(builddir, recurse_yotta_modules=False):
    ''' returns a list of (directory_path, [list of tuples of (test name, test command)]) '''
    # we don't run ctest -N to get the list of tests because unfortunately it
    # only lists the names, not the test commands. The best way to get at these
    # seems to be to parse the CTestTestfile.cmake files, which kinda sucks,
    # but works... Patches welcome.
    tests = []
    add_test_re = re.compile('add_test\\(([^" ]*)\s*"(.*)"\\)', flags=re.IGNORECASE)
    for root, dirs, files in os.walk(builddir, topdown=True):
        if not recurse_yotta_modules:
            dirs = [d for d in dirs if d != 'ym']
        if 'CTestTestfile.cmake' in files:
            with open(os.path.join(root, 'CTestTestfile.cmake'), 'r') as ctestf:
                dir_tests = []
                for line in ctestf:
                    if line.lower().startswith('add_test'):
                        match = add_test_re.search(line)
                        if match:
                            dir_tests.append((match.group(1), match.group(2)))
                        else:
                            logging.error(
                                "unknown CTest Syntax '%s', please report this error at http://github.com/ARMmbed/yotta/issues" %
                                line.rstrip('\n')
                            )
                if len(dir_tests):
                    tests.append((root, dir_tests))
    return tests

def moduleFromDirname(build_subdir, all_modules, toplevel_module):
    modtop = True
    submod = False
    module = toplevel_module
    # <topdir> /ym/<submod>/ym/<submod2>/somedir/somedir --> submod2
    for part in fsutils.fullySplitPath(build_subdir):
        if submod:
            if part in all_modules:
                module = all_modules[part]
            modtop = True
            submod = False
        else:
            if part == 'ym' and modtop:
                submod = True
            else:
                submod = False
                modtop = False
    return module

def execCommand(args, following_args):
    # remove the pseudo-name 'all': it wouldn't be recognised by build/cmake
    all_tests = 'all' in args.tests
    if all_tests:
        args.tests.remove('all')

    returncode = 0
    if args.build and not args.list_only:
        # we need to build before testing, make sure that any tests needed are
        # built:
        if all_tests:
            vars(args)['build_targets'] = args.tests + ['all_tests']
        else:
            vars(args)['build_targets'] = args.tests
        build_status = build.installAndBuild(args, following_args)
        # a generate or build step failure is fatal, but an install-step
        # failure should not prevent attempting tests:
        if build_status.get('generate_status', 0) != 0 or \
           build_status.get('build_status', 0) != 0 or \
           build_status.get('missing_status', 0) != 0:
            return 1
        else:
            returncode = build_status['status']

    cwd = os.getcwd()

    c = validate.currentDirectoryModule()
    if not c:
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    all_modules = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )


    builddir = os.path.join(cwd, 'build', target.getName())

    # get the list of tests we need to run, if --all is specified we also run
    # the tests for all of our submodules, otherwise we just run the tests for
    # this module.
    # If we have specific test specified, we also need to search for all the
    # tests, in case the specific test does not belong to this module
    tests = findCTests(builddir, recurse_yotta_modules=(all_tests or len(args.tests)))

    passed = 0
    failed = 0
    for dirname, test_definitions in tests:
        module = moduleFromDirname(os.path.relpath(dirname, builddir), all_modules, c)
        logging.debug('inferred module %s from path %s', module.getName(), os.path.relpath(dirname, builddir))
        if (not len(args.tests)) and (module is not c) and not all_tests:
            continue
        info_filter = True
        filter_command = module.getTestFilterCommand()
        for test_name, test_command in test_definitions:
            if len(args.tests) and not test_name in args.tests:
                logging.debug('skipping not-listed test %s: %s', test_name, test_command)
                continue
            if info_filter and filter_command:
                info_filter = False
                logging.info('using filter "%s" for tests in %s', ' '.join(filter_command), dirname)
            logging.info('test %s: %s', module.getName(), test_name)
            if args.list_only:
                continue
            test_returncode = target.test(
                            cwd = dirname,
                   test_command = test_command,
                 filter_command = filter_command,
                   forward_args = following_args
            )
            if test_returncode:
                logging.error('test %s failed (command: %s)', test_name, test_command)
                failed += 1
                if not returncode:
                    returncode = 1
            else:
                logging.info('test %s passed', test_name)
                passed += 1
    if not args.list_only:
        logging.info("tests complete: %d passed, %d failed", passed, failed)

    return returncode

