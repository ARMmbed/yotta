# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# validate, , validate things, internal
from yotta.lib import validate
# options, , shared options, internal
import yotta.options as options

def addOptions(parser):
    options.force.addTo(parser)

# python 2 + 3 compatibility
try:
    global input
    input = raw_input
except NameError:
    pass

def prePublishCheck(p, force=False, interactive=True):
    need_ok = False
    if p.description.get('bin', None) is not None:
        logging.warning(
            'This is an executable application, not a re-usable library module. Other modules will not be able to depend on it!'
        )
        need_ok = True

    official_keywords = [x for x in p.getKeywords() if x.endswith('-official')]
    if len(official_keywords):
        need_ok = True
        for k in official_keywords:
            prefix = k[:-len('-official')]
            logging.warning(
                ('You\'re publishing with the %s tag. Is this really an '+
                'officially supported %s module? If not, please remove the %s '+
                'tag from your %s file. If you are unsure, please ask on the '+
                'issue tracker.') % (
                    k, prefix, k, p.description_filename
                )
            )

    if need_ok and not interactive:
        logging.error('--noninteractive prevents user confirmation. Please re-run with --force')
        return 1

    if need_ok and not force:
        input("If you still want to publish, press [enter] to continue.")

    return 0

def execCommand(args, following_args):
    p = validate.currentDirectoryModuleOrTarget()
    if not p:
        return 1

    if not p.vcsIsClean():
        logging.error('The working directory is not clean. Commit before publishing!')
        return 1

    errcode = prePublishCheck(p, args.force, args.interactive)
    if errcode and not args.force:
        return errcode

    errcode = p.runScript('prePublish')
    if errcode:
        logging.error("prePublish script error code %s prevents publishing", errcode)
        return errcode

    error = p.publish(args.registry)
    if error:
        logging.error(error)
        return 1

    errcode = p.runScript('postPublish')
    if errcode:
        logging.warning("postPublish script exited with code %s", errcode)

    # tag the version published as 'latest'
    # !!! can't do this, as can't move tags in git?
    #p.commitVCS(tag='latest')
    logging.info('published latest version: %s', p.getVersion())
    return errcode
