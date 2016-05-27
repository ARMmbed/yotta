# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

def addOptions(parser):
    parser.add_argument('target_or_path', default=None, nargs='?',
        help='Link a globally installed (or globally linked) target into '+
             'the current target\'s dependencies. If ommited, globally '+
             'link the current target.'
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

def nameFromTargetSpec(target_name_and_version):
    if ',' in target_name_and_version:
        return target_name_and_version.split(',')[0]
    else:
        return target_name_and_version

def execCommand(args, following_args):
    # standard library modules, , ,
    import logging
    import os

    # colorama, BSD 3-Clause license, color terminal output, pip install colorama
    import colorama

    # fsutils, , misc filesystem utils, internal
    from yotta.lib import fsutils
    # validate, , validate things, internal
    from yotta.lib import validate
    # folders, , get places to install things, internal
    from yotta.lib import folders
    c = None
    t = None
    link_target_name = None
    if args.target_or_path:
        link_target_name = args.target_or_path
        c = validate.currentDirectoryModule()
        if not c:
            return 1
        err = validate.targetNameValidationError(args.target_or_path)
        if err:
            # check if the target name is really a path to an existing target
            if os.path.isdir(args.target_or_path):
                # make sure the first half of the link exists,
                src = os.path.abspath(args.target_or_path)
                # if it isn't a valid target, that's an error:
                tgt = validate.directoryTarget(src)
                if not tgt:
                    logging.error("%s is not a valid target: %s", args.target_or_path, tgt.getError())
                    return 1
                link_target_name = tgt.getName()
                dst = os.path.join(folders.globalInstallDirectory(), link_target_name)
                errcode = tryLink(src, dst)
                if errcode:
                    return errcode
            else:
                logging.error(err)
                return 1
        fsutils.mkDirP(os.path.join(os.getcwd(), 'yotta_targets'))
        src = os.path.join(folders.globalTargetInstallDirectory(), link_target_name)
        dst = os.path.join(os.getcwd(), 'yotta_targets', link_target_name)
        # if the target is already installed, rm it
        fsutils.rmRf(dst)
    else:
        t = validate.currentDirectoryTarget()
        if not t:
            return 1
        fsutils.mkDirP(folders.globalTargetInstallDirectory())
        src = os.getcwd()
        dst = os.path.join(folders.globalTargetInstallDirectory(), t.getName())

    broken_link = False
    if link_target_name:
        realsrc = fsutils.realpath(src)
        if src == realsrc:
            broken_link = True
            logging.warning(
              ('%s -> %s -> ' % (dst, src)) + colorama.Fore.RED + 'BROKEN' + colorama.Fore.RESET #pylint: disable=no-member
            )
        else:
            logging.info('%s -> %s -> %s' % (dst, src, realsrc))
        # check that the linked target is actually set as the target (or is
        # inherited from by something set as the target), if it isn't, warn the
        # user:
        if c and link_target_name != nameFromTargetSpec(args.target):
            target = c.getTarget(args.target, args.config)
            if target:
                if not target.inheritsFrom(link_target_name):
                    logging.warning(
                        'target "%s" is not used by the current target (%s), so '
                        'this link will have no effect. Perhaps you meant to '
                        'use "yotta target <targetname>" to set the build '
                        'target first.',
                        link_target_name,
                        nameFromTargetSpec(args.target)
                    )
            else:
                logging.warning(
                    'Could not check if linked target "%s" is used by the '+
                    'current target "%s": run "yotta target" to check.',
                    link_target_name,
                    nameFromTargetSpec(args.target)
                )

    else:
        logging.info('%s -> %s' % (dst, src))
    try:
        fsutils.symlink(src, dst)
    except Exception as e:
        if broken_link:
            logging.error('failed to create link (create the first half of the link first)')
        else:
            logging.error('failed to create link: %s', e)


