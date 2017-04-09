# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import re
import os
import logging



Source_Dir_Regex = re.compile('^[a-z0-9_-]*$')
Source_Dir_Invalid_Regex = re.compile('[^a-z0-9_-]*')
Component_Name_Replace_With_Dash = re.compile('[^a-z0-9]+')
Looks_Like_An_Email = re.compile('^[^@]+@[^@]+\.[^@]+$')

Component_Name_Regex = r'^[a-z]+[a-z0-9-]*$'
Target_Name_Regex = r'^[a-z]+[a-z0-9+-]*$'

# return True if the given directory name is a potential directory name
# for tests, False otherwise
def isPotentialTestDir(dirname):
    return dirname.lower() in ('test', 'tests')

# return an error string describing the validation failure, or None if there is
# no error
def sourceDirValidationError(dirname, component_name):
    ''' validate source directory names in components '''
    if dirname == component_name:
        return 'Module %s public include directory %s should not contain source files' % (component_name, dirname)
    elif dirname.lower() in ('source', 'src') and dirname != 'source':
        return 'Module %s has non-standard source directory name: "%s" should be "source"' % (component_name, dirname)
    elif isPotentialTestDir(dirname) and dirname != 'test':
        return 'Module %s has non-standard test directory name: "%s" should be "test"' % (component_name, dirname)
    elif not Source_Dir_Regex.match(dirname):
        corrected = Source_Dir_Invalid_Regex.sub('', dirname.lower())
        if not corrected:
            corrected = 'source'
        return 'Module %s has non-standard source directory name: "%s" should be "%s"' % (component_name, dirname, corrected)
    else:
        return None

def componentNameValidationError(component_name):
    if not re.match(Component_Name_Regex, component_name):
        return 'Module name "%s" is invalid - must contain only lowercase a-z, 0-9 and hyphen, with no spaces.' % component_name
    return None

def targetNameValidationError(target_name):
    if not re.match(Target_Name_Regex, target_name):
        return 'Target name "%s" is invalid - must contain only lowercase a-z, 0-9, + and hyphen, with no spaces.' % target_name
    return None

def componentNameCoerced(component_name):
    return Component_Name_Replace_With_Dash.sub('-', component_name.lower())

def looksLikeAnEmail(email):
    if Looks_Like_An_Email.match(email):
        return True
    else:
        return False

def directoryModule(path):
    # Component, , represents an installed component, internal
    from yotta.lib import component
    # Pack, , base class for targets and components, internal
    from yotta.lib import pack
    try:
        c = component.Component(path)
    except pack.InvalidDescription as e:
        logging.error(e)
        return None
    return c

def directoryTarget(path):
    # Target, , represents an installed target, internal
    from yotta.lib import target
    # Pack, , base class for targets and components, internal
    from yotta.lib import pack
    try:
        t = target.Target(path)
    except pack.InvalidDescription as e:
        logging.error(e)
        return None
    return t

def currentDirectoryModule():
    c = directoryModule(os.getcwd())
    if not c:
        logging.error(str(c.error))
        logging.error('The current directory does not contain a valid module.')
        return None
    return c

def currentDirectoryTarget():
    t = directoryTarget(os.getcwd())
    if not t:
        logging.error(str(t.error))
        logging.error('The current directory does not contain a valid target.')
        return None
    return t

def currentDirectoryModuleOrTarget():
    # Component, , represents an installed component, internal
    from yotta.lib import component
    # Target, , represents an installed target, internal
    from yotta.lib import target
    # Pack, , base class for targets and components, internal
    from yotta.lib import pack
    wd = os.getcwd()
    errors = []
    p = None
    try:
        p = component.Component(wd)
    except pack.InvalidDescription as e:
        errors.append(e)
    if not p:
        try:
            p = target.Target(wd)
        except pack.InvalidDescription as e:
            errors.append(e)
    if not p:
        for e in errors:
            logging.debug(e)
        logging.error('The current directory does not contain a valid module or target.')
        return None
    return p
