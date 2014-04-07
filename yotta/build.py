# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
from lib import component
# CMakeGen, , generate build files, internal
from lib import cmakegen


def addOptions(parser):
    parser.add_argument('-g', '--generate-only', dest='generate_only',
        action='store_true', default=False,
        help='Only generate CMakeLists, don\'t run CMake or build'
    )


def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    builddir = os.path.join(cwd, 'build')

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    all_components = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)]
    )
    logging.info('all dependencies: (target=%s)' % target)
    for d in all_components.values():
        if d:
            logging.info('    %s@%s: %s' % (d.getName(), d.getVersion(), os.path.relpath(d.path)))
        else:
            logging.error('    %s not available' % os.path.split(d.path)[1])

    generator = cmakegen.CMakeGen(builddir, target)
    errcode = None
    for error in generator.generateRecursive(c, all_components, builddir):
        logging.error(error)
        errcode = 1
    
    if not args.generate_only:
        for error in target.build(builddir):
            logging.error(error)
            errcode = 1

    return errcode

