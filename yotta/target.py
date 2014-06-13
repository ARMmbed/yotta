# standard library modules, , ,
import re

# settings, , load and save settings, internal
from lib import settings


# OK this is a pretty terrible validation regex... should find a proper module
# to do this
Target_RE = re.compile('^('+
    '[a-z0-9-]+,?('+
        '[a-zA-Z0-9-]+/[a-zA-Z0-9-]+' +'|'+ '([a-zA-Z0-9_-]*@)?[a-zA-Z0-9_+-]+://.*' + '|' + '[a-z0-9.-]*'+
    ')?'+
')$')


def addOptions(parser):
    parser.add_argument('target', default=None, nargs='?',
        help='set the build target to this (targetname[,versionspec_or_url])'
    )

    # FIXME: need help that lists possible targets, and we need a walkthrough
    # guide to forking a new target for an existing board
    #
    # (the description of a target should have a list of things that it's
    #  similar to, e.g. objectador is similar to EFM32gg990f, #  EFM32gg,
    #  Cortex-M3, ARMv8, ARM)

    # FIXME: per-program target setting (per-program settings files?)
    #parser.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
    #    help='Install globally instead of in the current working directory.'
    #)


def execCommand(args):
    if args.target is None:
        saved = settings.getProperty('build', 'target')
        if saved is not None:
            print '%s version: %s' % tuple(saved.split(',', 1))
        else:
            print None
    else:
        if not Target_RE.match(args.target):
            logging.error('''Invalid target: "%s"''' % args.target)#, targets must be one of:
            #
            #    a valid name (lowercase letters, numbers, and hyphen)
            #    a github ref (owner/project)
            #    a valid url
            #
            #Note that to use a local directory as a target you can use
            #
            #    # in the directory containing the target package:
            #    yotta link target
            #
            #    # then in the directory of the application to use the target:
            #    yotta link target {targetname}
            #    yotta target {targetname}
            #
            #''')
        else:
            if args.target.find(',') == -1:
                target = args.target + ',*'
            else:
                target = args.target
            settings.setProperty('build', 'target', target)
