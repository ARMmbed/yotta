# standard library modules, , ,
import argparse
import logging
import os

# version, , represent versions and specifications, internal
from lib import version
# Component, , represents an installed component, internal
from lib import component
# Target, , represents an installed target, internal
from lib import target
# Registry Access, , access packages in the registry, internal
from lib import registry_access
# Validate, , validate various things, internal
from lib import validate

def checkEmail(email):
    if validate.looksLikeAnEmail(email):
        return email
    else:
        raise argparse.ArgumentTypeError(
            "\"%s\" doesn't look like a valid email address" % email
        )

def addOptions(parser):
    subparser = parser.add_subparsers(metavar='{list, add, remove}', dest='subsubcommand')

    parse_list = subparser.add_parser("list", description="list the module or target's owners")
    parse_list.add_argument('module', nargs='?',
        help="module to list owners for (defaults to the current directory's module)"
    )

    parse_add  = subparser.add_parser("add", description="add an owner to the module or target")
    parse_add.add_argument('email', type=checkEmail,
        help="email address to add as an owner"
    )
    parse_add.add_argument('module', nargs='?',
        help="module add owner for (defaults to the current directory's module)"
    )

    parse_rm   = subparser.add_parser("remove", description="remove an owner from the module or target")
    parse_rm.add_argument('email', type=checkEmail,
        help="email address to remove from owners"
    )
    parse_rm.add_argument('module', nargs='?',
        help="module to remove owner from (defaults to the current directory's module)"
    )

    subparser.choices.update({
        '':subparser.choices['list'],
      'ls':subparser.choices['list'],
      'rm':subparser.choices['remove'],
    })


def execCommand(args):
    print args
    sc = args.subsubcommand

    # if the current directory contains a component or a target, get it
    cwd = os.getcwd()
    c = component.Component(cwd)
    t = target.Target(cwd)
    p = c
    if t and not c:
        p = t

    if not p and not args.module:
        logging.error('a module must be specified (the current directory does not contain a valid module)')
        return 1

    if sc in ('list', 'ls', ''):
        listOwners(args, p)
    elif sc in ('remove', 'rm'):
        removeOwner(args, p)
    elif sc in ('add',):
        addOwner(args, p)


def listOwners(args, p):
    if p:
        registry_access.listOwners(p.getRegistryNamespace(), p.getName)
    else:
        # !!! FIXME: capture does-not-exist messages into single line errors
        registry_access.listOwners(component.Registry_Namespace, args.module)
        registry_access.listOwners(target.Registry_Namespace, args.module)

def removeOwner(args, p):
    if p:
        registry_access.removeOwner(p.getRegistryNamespace(), p.getName, args.email)
    else:
        # !!! FIXME: test which of target/component exist first
        registry_access.removeOwner(component.Registry_Namespace, args.module, args.email)

def addOwner(args, p):
    if p:
        registry_access.addOwner(p.getRegistryNamespace(), p.getName, args.email)
    else:
        # !!! FIXME: test which of target/component exist first
        registry_access.addOwner(component.Registry_Namespace, args.module, args.email)
