# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
from lib import component
# CMakeGen, , generate build files, internal
from lib import cmakegen
# Target, , represents an installed target, internal
from lib import target


def addOptions(parser):
    parser.add_argument('-g', '--generate-only', dest='generate_only',
        action='store_true', default=False,
        help='Only generate CMakeLists, don\'t run CMake or build'
    )
    parser.add_argument('-r', '--release-build', dest='release_build', action='store_true', default=False)
    # the target class adds its own build-system specific options. In the
    # future we probably want to load these from a target instance, rather than
    # from the class
    target.Target.addBuildOptions(parser)

def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    builddir = os.path.join(cwd, 'build', target.getName())

    all_components = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)]
    )
    for d in all_components.values():
        if not d:
            logging.error('    %s not available' % os.path.split(d.path)[1])

    generator = cmakegen.CMakeGen(builddir, target)
    errcode = None
    for error in generator.generateRecursive(c, all_components, builddir):
        logging.error(error)
        errcode = 1
    
    if not args.generate_only:
        for error in target.build(builddir, c, args, release_build=args.release_build):
            logging.error(error)
            errcode = 1
            break

    return errcode

