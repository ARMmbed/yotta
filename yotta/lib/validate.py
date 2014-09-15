# standard library modules, , ,
import re

Source_Dir_Regex = re.compile('^[a-z0-9_-]*$')
Source_Dir_Invalid_Regex = re.compile('[^a-z0-9_-]*')
Component_Name_Regex = re.compile('^[a-z0-9-]*$')
Component_Name_Replace_With_Dash = re.compile('[^a-z0-9]+')

# return an error string describing the validation failure, or None if there is
# no error
def sourceDirValidationError(dirname, component_name):
    ''' validate source directory names in components '''
    if dirname == component_name:
        return 'Component %s public include directory %s should not contain source files' % (component_name, dirname)
    elif dirname.lower() in ('source', 'src') and dirname != 'source':
        return 'Component %s has non-standard source directory name: "%s" should be "source"' % (component_name, dirname)
    elif dirname.lower() in ('test', 'tests') and dirname != 'test':
        return 'Component %s has non-standard test directory name: "%s" should be "test"' % (component_name, dirname)
    elif not Source_Dir_Regex.match(dirname):
        corrected = Source_Dir_Invalid_Regex.sub('', dirname.lower())
        if not corrected:
            corrected = 'source'
        return 'Component %s has non-standard source directory name: "%s" should be "%s"' % (component_name, dirname, corrected)
    else:
        return None

def componentNameValidationError(component_name):
    if not Component_Name_Regex.match(component_name):
        return 'Component name "%s" is invalid - must contain only lowercase a-z, 0-9 and hyphen, with no spaces.'
    return None

def componentNameCoerced(component_name):
    return Component_Name_Replace_With_Dash.sub('-', component_name.lower())
