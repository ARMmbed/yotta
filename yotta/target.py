# standard library modules, , ,
import re

# settings, , load and save settings, internal
from lib import settings


# OK this is a pretty terrible validation regex... should find a proper module
# to do this
Target_RE = re.compile('^([a-z0-9-]*|[a-zA-Z0-9-]+/[a-zA-Z0-9-]+|([a-zA-Z0-9_-]*@)?[a-zA-Z0-9_+-]+://.*)$')


def addOptions(parser):
    parser.add_argument('target', default=None, nargs='?',
        help='set the build target to this'
    )

    # FIXME: need help that lists possible targets, and we need a walkthrough
    # guide to forking a new target for an existing board, and we need to pick
    # dependencies based on closest-supported target so that when someone forks
    # a target they don't have to fork every single target dependent component
    #
    # (the description of a target should have a hierarchy of things that it's
    #  similar to, e.g. objectador is similar to EFM32-STK3700 is similar to
    #  EFM32gg990f is similar to Cortex-M3)

    # FIXME: per-program target setting (per-program settings files?)
    #parser.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
    #    help='Install globally instead of in the current working directory.'
    #)


def execCommand(args):
    if args.target is None:
        print settings.getProperty('build', 'target')
    else:
        if not Target_RE.match(args.target):
            logging.error('''Invalid target: "%s"''')#, targets must be one of:
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
            settings.setProperty('build', 'target', args.target)
