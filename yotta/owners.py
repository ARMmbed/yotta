# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import argparse
import logging
import os

# Component, , represents an installed component, internal
from .lib import component
# Target, , represents an installed target, internal
from .lib import target
# Registry Access, , access packages in the registry, internal
from .lib import registry_access
# Validate, , validate various things, internal
from .lib import validate

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


def execCommand(args, following_args):
    sc = args.subsubcommand

    # if the current directory contains a component or a target, get it
    cwd = os.getcwd()
    c = component.Component(cwd)
    t = target.Target(cwd)

    if args.module:
        p = None
    else:
        p = c
        if t and not c:
            p = t

    if not p and not args.module:
        logging.error('a module must be specified (the current directory does not contain a valid module)')
        return 1

    if sc in ('list', 'ls', ''):
        return listOwners(args, p)
    elif sc in ('remove', 'rm'):
        return removeOwner(args, p)
    elif sc in ('add',):
        return addOwner(args, p)


def listOwners(args, p):
    if p:
        owners = registry_access.listOwners(p.getRegistryNamespace(), p.getName(), registry=args.registry)
        if owners is not None:
            print('%s "%s" owners:' % (p.getRegistryNamespace(), p.getName()), ', '.join(owners))
        else:
            return 1
    else:
        module_owners = registry_access.listOwners(component.Registry_Namespace, args.module, registry=args.registry)
        target_owners = registry_access.listOwners(target.Registry_Namespace, args.module, registry=args.registry)
        if module_owners:
            print('module "%s" owners:' % args.module, ', '.join(module_owners))
        if target_owners:
            print('target "%s" owners:' % args.module, ', '.join(target_owners))
        if not module_owners and not target_owners:
            logging.error('no such module or target')
            return 1
    return 0

def removeOwner(args, p):
    if p:
        success = registry_access.removeOwner(p.getRegistryNamespace(), p.getName(), args.email, registry=args.registry)
    else:
        # !!! FIXME: test which of target/component exist first
        success = registry_access.removeOwner(component.Registry_Namespace, args.module, args.email, registry=args.registry)
    return 0 if success else 1

def addOwner(args, p):
    if p:
        success = registry_access.addOwner(p.getRegistryNamespace(), p.getName(), args.email, registry=args.registry)
    else:
        # !!! FIXME: test which of target/component exist first
        success = registry_access.addOwner(component.Registry_Namespace, args.module, args.email, registry=args.registry)
    return 0 if success else 1
