# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import os

# fsutils, , misc filesystem utils, internal
from .lib import fsutils
# validate, , validate things, internal
from .lib import validate


def addOptions(parser):
    parser.add_argument('module', default=None, nargs='?', metavar='<module>',
        help='Name of the module to remove. If omitted the current module '+
             'or target will be removed from the global linking directory.'
    )

def execCommand(args, following_args):
    module_or_target = 'module'
    if 'target' in args.subcommand_name:
        module_or_target = 'target'
    if args.module is not None:
        return removeDependency(args, module_or_target)
    else:
        return removeGlobally(module_or_target)

def rmLinkOrDirectory(path, nonexistent_warning):
    if not os.path.exists(path):
        logging.warning(nonexistent_warning)
        return 1
    if fsutils.isLink(path):
        fsutils.rmF(path)
    else:
        fsutils.rmRf(path)
    return 0

def removeGlobally(module_or_target):
    # folders, , get places to install things, internal
    from .lib import folders
    if module_or_target == 'module':
        global_dir = folders.globalInstallDirectory()
        p = validate.currentDirectoryModule()
    else:
        global_dir = folders.globalTargetInstallDirectory()
        p = validate.currentDirectoryTarget()
    if p is None:
        return 1
    path = os.path.join(global_dir, p.getName())
    return rmLinkOrDirectory(path, ('%s is not linked globally' % p.getName()))

def removeDependency(args, module_or_target):
    c = validate.currentDirectoryModule()
    if not c:
        return 1
    if module_or_target == 'module':
        subdir = c.modulesPath()
        err = validate.componentNameValidationError(args.module)
    else:
        subdir = c.targetsPath()
        err = validate.targetNameValidationError(args.module)
    if err:
        logging.error(err)
        return 1
    path = os.path.join(subdir, args.module)
    return rmLinkOrDirectory(path, '%s %s not found' % (('dependency', 'target')[module_or_target=='target'], args.module))


