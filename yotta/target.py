
# settings, , load and save settings, internal
from lib import settings


def addOptions(parser):
    parser.add_argument('target', default=None, nargs='?',
        help='Set the build target'
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
    if args.component is None:
        installDeps(args)
    else:
        installComponent(args)
