# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import os
import logging
import re

# Component, , represents an installed component, internal
from .lib import component
# version, , represent versions and specifications, internal
from .lib import version
# validate, , validate various things, internal
from .lib import validate

Known_Licenses = {
             'isc': 'https://spdx.org/licenses/ISC',
      'apache-2.0': 'https://spdx.org/licenses/Apache-2.0',
             'mit': 'https://spdx.org/licenses/MIT',
    'bsd-3-clause': 'https://spdx.org/licenses/BSD-3-Clause'
}

Git_Repo_RE = re.compile("^(git[+a-zA-Z-]*:.*|.*\.git|.*git@.*github\.com.*)$")
HG_Repo_RE  = re.compile("^(hg[+a-zA-Z-]*:.*|.*\.hg)$")
SVN_Repo_RE = re.compile("^svn[+a-zA-Z-]*:.*$")



def getUserInput(question, default=None, type_class=str):
    # python 2 + 3 compatibility
    try:
        global input
        input = raw_input
    except NameError:
        pass
    while True:
        default_descr = ''
        if default is not None:
            default_descr = ' <%s> ' % str(default)
        value = input(question + default_descr)
        if default is not None and not value:
            if type_class:
                return type_class(default)
            else:
                return default
        try:
            typed_value = type_class(value)
            break
        except:
            print('"%s" isn\'t a valid "%s" value' % (value, type_class.__name__))
    return typed_value

def yesNo(string):
    if string.strip().lower() in ('yes', 'y'):
        return True
    elif string.strip().lower() in ('no', 'n'):
        return False
    else:
        raise ValueError()
yesNo.__name__ = "Yes/No"

def repoObject(string):
    string = string.strip()
    if not string:
        return None
    elif Git_Repo_RE.match(string):
        repo_type = 'git'
        url = Git_Repo_RE.match(string).group(0)
    elif HG_Repo_RE.match(string):
        repo_type = 'hg'
        url = HG_Repo_RE.match(string).group(0)
    elif SVN_Repo_RE.match(string):
        repo_type = 'svn'
        url = SVN_Repo_RE.match(string).group(0)
    else:
        raise ValueError()
    return {'type':repo_type, 'url':url}

def listOfWords(string):
    if isinstance(string, list):
        return string
    else:
        return filter(bool, re.split(",|\\s", string))

def addOptions(parser):
    pass

def execCommand(args, following_args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if c:
        logging.info('The current directory already a contains a module: existing description will be modified')
    elif os.path.isfile(c.getDescriptionFile()):
        logging.error('A module description exists but could not be loaded:')
        logging.error(c.error)
        return 1

    default_name = c.getName()
    if not default_name:
        default_name = validate.componentNameCoerced(os.path.split(cwd)[1])
    
    c.setName(getUserInput("Enter the module name:", default_name))
    c.setVersion(getUserInput("Enter the initial version:", str(c.getVersion() or "0.0.0"), version.Version))

    def current(x):
        return c.description[x] if x in c.description else None

    c.description['description'] = getUserInput("Short description: ", current('description'))
    c.description['keywords']    = getUserInput("Keywords: ", ' '.join(current('keywords') or []), listOfWords)
    c.description['author']      = getUserInput("Author: ", current('author'))

    current_repo_url = current('repository')
    if isinstance(current_repo_url, dict):
        current_repo_url = current_repo_url['url']
    new_repo_url = getUserInput("Repository url: ", current_repo_url, repoObject)
    if new_repo_url:
        c.description['repository'] = new_repo_url
    c.description['homepage']    = getUserInput("Homepage: ", current('homepage'))

    if not current('licenses') or current('license'):
        license = getUserInput('What is the license for this project (Apache-2.0, ISC, MIT etc.)? ', 'Apache-2.0')
        license_url = None
        if license.lower().strip() in Known_Licenses:
            license_url = Known_Licenses[license.lower().strip()]
            c.description['licenses'] = [{'type':license, 'url':license_url}]
        else:
            c.description['license'] = license

    c.description['dependencies']       = current('dependencies') or {}
    c.description['targetDependencies'] = current('targetDependencies') or {}

    isexe = getUserInput("Is this module an executable?", "no", yesNo)
    if isexe:
        c.description['bin'] = './source'


    # Create folders while initing
    folders_to_create = ["./source", "./test", "./" + c.getName()]
    for folder_name in folders_to_create:
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

    c.writeDescription()

