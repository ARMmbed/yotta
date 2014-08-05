# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
from lib import component
# version, , represent versions and specifications, internal
from lib import version

Known_Licenses = {
    'mit': 'https://spdx.org/licenses/MIT',
    'bsd-3-clause': 'https://spdx.org/licenses/BSD-3-Clause'
}


def getUserInput(question, default=None, type_class=str):
    while True:
        default_descr = ''
        if default is not None:
            default_descr = ' <%s>' % str(default)
        value = raw_input(question + default_descr)
        if default is not None and not value:
            return default
        try:
            typed_value = type_class(value)
            break
        except:
            print '"%s" isn\'t a valid "%s" value' % (value, type_class.__name__)
    return typed_value


def addOptions(parser):
    pass


def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if c:
        logging.info(
            'The current directory already a contains a component: existing description will be modified')
    elif os.path.isfile(c.getDescriptionFile()):
        logging.error(
            'A component description exists but could not be loaded:')
        logging.error(c.error)
        return 1

    c.setName(getUserInput("Enter the package name:", c.getName()))
    c.setVersion(
        getUserInput("Enter the initial version:", str(c.getVersion() or "0.0.0"), version.Version))

    def current(x):
        return c.description[x] if x in c.description else None

    c.description['description'] = getUserInput(
        "Short description: ", current('description'))
    c.description['author'] = getUserInput("Author: ", current('author'))
    c.description['homepage'] = getUserInput("Homepage: ", current('homepage'))

    if not current('licenses') or current('license'):
        license = getUserInput(
            'What is the license for this project (MIT, BSD-3-Clause, etc.)? ')
        license_url = 'about:blank'
        if license.lower().strip() in Known_Licenses:
            license_url = Known_Licenses[license.lower().strip()]
        c.description['licenses'] = [{'type': license, 'url': license_url}]

    c.description['dependencies'] = current('dependencies') or {}
    c.description['targetDependencies'] = current('targetDependencies') or {}

    # TODO: more questions ( bugs url,...), check that the name is available in
    # the registry...

    c.writeDescription()
