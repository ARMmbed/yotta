
# Component, , represents an installed component, internal
import Component

# Version strings we want to support:
#
# (>,>=,<,<=,)version                        # central repo
# 1.2.x                                      # central repo
# http://...                                 # tarball or zipfile
# owner/repo @((>,>=,<,<=,,)version)         # Github
# git://github.com/use/project(#hash-or-tag) # Github
# git+(ssh://..., http://...)(#hash-or-tag)  # git
# hg+(ssh://..., http://...)(#hash-or-tag)   # hg
# * (any version)                            # central repo
#

def satisfyVersion(name, version, available):
    ''' returns a Component for the specified version (either to an already
        installed copy (from the available list), or to a newly downloaded
        one), or None if the version could not be satisfied.
    '''
    
    # if name in available:
    #   ... etc
    # else if version us a url:
    #   ...
    #       might also have version associated with it? (e.g. if it's a github
    #       git URL we can fetch a tarball of a tagged version from the github
    #       api, which is more efficient than cloning the entire repo), if its
    #       a ssh git/hg/whatever repo we have no choice other than cloning?
    # else
    #   ... fetch from central repo 'name' project
