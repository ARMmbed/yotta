# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

def addOptions(parser):
    parser.add_argument('module_or_path', default=None, nargs='?',
        help='Link a globally installed (or globally linked) module into '+
             'the current module\'s dependencies. If ommited, globally '+
             'link the current module.'
    )

def tryLink(src, dst):
    # standard library modules, , ,
    import logging

    # fsutils, , misc filesystem utils, internal
    from yotta.lib import fsutils
    try:
        fsutils.symlink(src, dst)
    except Exception as e:
        if src == fsutils.realpath(src):
            logging.error('failed to create link (create the first half of the link first)')
        else:
            logging.error('failed to create link: %s', e)
        return 1
    return 0

def execCommand(args, following_args):
    # standard library modules, , ,
    import logging
    import os

    # colorama, BSD 3-Clause license, color terminal output, pip install colorama
    import colorama

    # validate, , validate things, internal
    from yotta.lib import validate
    # folders, , get places to install things, internal
    from yotta.lib import folders
    # fsutils, , misc filesystem utils, internal
    from yotta.lib import fsutils

    c = validate.currentDirectoryModule()
    if not c:
        return 1
    link_module_name = None
    if args.module_or_path:
        link_module_name = args.module_or_path
        err = validate.componentNameValidationError(args.module_or_path)
        if err:
            # check if the module name is really a path to a module
            if os.path.isdir(args.module_or_path):
                # make sure the first half of the link exists,
                src = os.path.abspath(args.module_or_path)
                # if it isn't a valid module, that's an error:
                dep = validate.directoryModule(src)
                if not dep:
                    logging.error("%s is not a valid module: %s", args.module_or_path, dep.getError())
                    return 1
                link_module_name = dep.getName()
                dst = os.path.join(folders.globalInstallDirectory(), link_module_name)
                errcode = tryLink(src, dst)
                if errcode:
                    return errcode
            else:
                logging.error("%s is neither a valid module name, nor a path to an existing module.", args.module_or_path)
                logging.error(err)
                return 1
        fsutils.mkDirP(os.path.join(os.getcwd(), 'yotta_modules'))
        src = os.path.join(folders.globalInstallDirectory(), link_module_name)
        dst = os.path.join(os.getcwd(), 'yotta_modules', link_module_name)
        # if the component is already installed, rm it
        fsutils.rmRf(dst)
    else:
        fsutils.mkDirP(folders.globalInstallDirectory())

        src = os.getcwd()
        dst = os.path.join(folders.globalInstallDirectory(), c.getName())

    if link_module_name:
        realsrc = fsutils.realpath(src)
        if src == realsrc:
            logging.warning(
              ('%s -> %s -> ' % (dst, src)) + colorama.Fore.RED + 'BROKEN' + colorama.Fore.RESET #pylint: disable=no-member
            )
        else:
            logging.info('%s -> %s -> %s' % (dst, src, realsrc))
        # check if the thing we linked is actually a dependency, if it isn't
        # warn about that. To do this we may have to get the current target
        # description. This might fail, in which case we warn that we couldn't
        # complete the check:
        target = c.getTarget(args.target, args.config)
        if target:
            if not c.hasDependencyRecursively(link_module_name, target=target, test_dependencies=True):
                logging.warning(
                    '"%s" is not installed as a dependency, so will not '+
                    ' be built. Perhaps you meant to "yotta install %s" '+
                    'first?',
                    link_module_name,
                    link_module_name
                )
        else:
            logging.warning(
                'Could not check if linked module "%s" is installed as a '+
                'dependency, because target "%s" is not available. Run '
                '"yotta ls" to check.',
                link_module_name,
                args.target
            )
    else:
        logging.info('%s -> %s' % (dst, src))
    return tryLink(src, dst)

