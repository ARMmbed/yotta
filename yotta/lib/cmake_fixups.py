# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# workarounds for various issues in CMake

# standard library modules, , ,
import os
import logging


logger = logging.getLogger('yotta.lib.cmake_fixups')

def fixupEclipseProject(builddir, component):
    # explicitly add link to the source directory to generated eclipse
    # projects, so the source files are accessible through the GUI
    import fileinput
    import sys
    logger.debug('fixing up Eclipse project file')
    proj_file = os.path.join(builddir, '.project')
    done = False
    for line in fileinput.input(proj_file, inplace=1):
        sys.stdout.write(line)
        if line.strip() == '<linkedResources>' and not done:
            done = True
            # insert:
            #<link>
            #	<name>ComponentName-source</name>
            #	<type>2</type>
            #	<location>/absolute/path/to/source/location>
            #</link>
            # Note that the path must use forward slashes as separators on
            # windows.
            sys.stdout.write(
                '''\t\t<link>
\t\t\t<name>%s-source</name>
\t\t\t<type>2</type>
\t\t\t<location>%s</location>
\t\t</link>\n''' % (component.getName(), os.path.abspath(os.path.join(component.path, 'source')).replace('\\', '/'))
            )

def fixupNinjaBackslashes(builddir):
    logger.debug("Converting back-slashes in build.ninja to forward-slashes")
    build_file = os.path.join(builddir, "build.ninja")
    # We want to convert back-slashes to forward-slashes, except in macro
    # definitions, such as -DYOTTA_COMPONENT_VERSION = \"0.0.1\". So we use a
    # little trick: first we change all \" strings to an unprintable ASCII char
    # that can't appear in build.ninja (in this case \1), then we convert all
    # the back-slashed to forward-slashes, then we convert '\1' back to \".
    try:
        f = open(build_file, "r+t")
        data = f.read()
        data = data.replace('\\"', '\1')
        data = data.replace('\\', '/')
        data = data.replace('\1', '\\"')
        f.seek(0)
        f.write(data)
        f.close()
    except Exception as e:
        logger.error('Unable to fixup ninja file "%s", the build may fail.',
                build_file)


def applyFixupsForFenerator(cmake_generator, builddir, component):
    # cmake error: the generated Ninja build file will not work on windows when
    # arguments are read from a file (@file) instead of the command line, since
    # '\' in @file is interpreted as an escape sequence.
    #!!! FIXME: remove this once http://www.cmake.org/Bug/view.php?id=15278 is fixed!
    if ('Ninja' in cmake_generator) and os.name == 'nt':
        fixupNinjaBackslashes(builddir)

    # both fixups may apply, so don't use elif
    if "Eclipse" in cmake_generator:
        fixupEclipseProject(builddir, component)
