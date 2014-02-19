# standard library modules, , ,
import os

# Component, , represents an installed component, internal
from lib import component
# CMakeGen, , generate build files, internal
from lib import cmakegen


def addOptions(parser):
    pass


def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    builddir = os.path.join(cwd, 'build')

    # FIXME: will pass target, or target-dependent defs from target, to generator
    generator = cmakegen.CMakeGen(builddir)
    generator.generateRecursive(c, builddir)
