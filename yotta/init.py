# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
from lib import component
# version, , represent versions and specifications, internal
from lib import version


def getUserInput(question, default = None, type_class=str):
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
        logging.info('The current directory already a contains a component: existing description will be modified')
    elif os.path.isfile(c.getDescriptionFile()):
        logging.error('A component description exists but could not be loaded:')
        logging.error(c.error)
        return 1
    
    c.setName(getUserInput("Enter the package name:", c.getName()))
    c.setVersion(getUserInput("Enter the initial version:", str(c.getVersion() or "0.0.0"), version.Version))

    current_description = c.description['description'] if 'description' in c.description else None
    c.description['description'] = getUserInput("Short description:", current_description)

    # TODO: more questions (homepage, bugs url,...), check that the name is
    # available in the registry, and make sure there are empty dependency
    # sections in the json file

    c.writeDescription()

