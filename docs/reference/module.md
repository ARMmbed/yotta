---
layout: default
title: module.json
section: reference/module
---

# module.json Reference
The `module.json` file is used to describe all yotta modules and executables,
it lists the dependencies, specifies the license under which the module can be
used, and provides other information about the module.

To create a new module, you can either write a module.json file manually, or
use `yotta init` to populate the file by answering a sequence of questions.

### Example File
```json
{
  "name": "helloyotta",
  "version": "0.0.0",
  "description": "Hello yotta example module",
  "keywords": ["example"],
  "author": "James Crosby <james.crosby@arm.com>",
  "homepage": "http://github.com/ARMmbed/yotta",
  "repository": {
    "url": "git@github.com:ARMmbed/helloyotta.git",
    "type": "git"
  },
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
    "simplelog": "~0.0.0"
  },
  "targetDependencies": {},
  "bin": "./source"
}
```

## Properties

### `name` *required*
**type: String**

The unique name of your module. It's got to be globally unique, so be
adventurous!

Names can use only lowercase letters, numbers, and hyphens, but must start with
a letter. (This reduces problems with case insensitive filesystems, and
confusingly similar names.)


### `version` *required*
**type: String (conforming to the [semver](http://semver.org) specification)**

yotta uses Semantic Versions for modules: your module's version lets people who
depend on your module know how it's changed since they last updated.

The basic format is:

```
<major>.<minor>.<patch>
```

Optionally followed by `-build-specifiers`.

Whenever you publish a new version of your module, you must update the version
number.

For `0.x.x` versions, the module's API may change in any way across version
numbers.

Once the public API is relatively stable, the major version should be
incremented to 1.

For `1+.x.x` versions, semantic versioning defines the following rules:

 * The `<major>` version must be incremented whenever any backwards incompatible
   changes are made.

 * Otherwise, the `<minor>` version must be updated if new functionality is added which is
   backwards compatible.

 * Otherwise, the `<patch>` version must be updated if only
   backwards-compatible bugfixes have been made.

For a complete guide to semantic versioning, see [semver.org](http://semver.org).



### `licenses` *required*
**type: Array of objects: `{"url":"<URL to full license>", "type":"<SPDX license identifier>" }`**

The licenses property in module.json should include all of the licenses that
affect code in your module. For example:

```json
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ]
```

If you're starting a completely new module, and have freedom to choose the
license yourself, `yotta`'s preferred license is
[Apache-2.0](http://spdx.org/licenses/Apache-2.0), a permissive OSI-approved
open source license which provides clarity over the scope of patent grants.
`yotta` itself is also licensed under Apache-2.0.

When you run `yotta init` to initialise a new module, yotta will suggest some
licenses, and automatically fill in the license URL for those options.

<a name="dependencies"></a>
### `dependencies`
**type: Object `{"<modulename>": "<version specification or source>"}`**

While not required (since your module may not depend on anything), the
`dependencies` section is one of the most important in your module's
description. It describes which other modules your code needs in order to run
and which versions of them should be used.

`yotta` uses this information to automatically download the modules when you
build.

Example:

```json
    "dependencies": {
		"usefulmodule": "^1.2.3",
		"simplelog": "ARMmbed/simplelog#~0.0.1"
	}
```

#### Depending on Modules in the `yotta` Registry
If only a version specification is provided, yotta will look for the specified module
in the public yotta registry. (To publish a module to the registry use
`yotta publish`).

Version specifications can take any of the following forms:

 * `1.2.3`: an exact version number. Use only this exact version (not
   recommended)
 * `^1.2.3`: any compatible version (exact version for `0.x.x` versions, or any
   version greater than the specified version with the same major version
   number for versions > 1. 
 * `~1.2.3`: any version with the same major and minor versions, and an equal
   or greater patch version. 
 * `>1.2.3`: any version greater than `1.2.3`. `>=`, `<`, and `<=` are also
   possible.
 * `*`: any version (useful for development)
  
The `^` and `~` specifiers are recommended, as these provide some guarantee of
compatibility without rigidly constraining the version (which would cause
problems if two separate modules depend on different versions).

#### Depending on Modules in Github
`yotta` has built-in support for depending on modules from Github, including
private repositories (run `yotta login` to authorise yotta for the private
repositories you have access to).

To specify a dependency on a github module, use one of the following forms:

 * `"usefulmodule": "username/repositoryname"`

    Uses the latest version tagged with a semantic version identifier, or
    the head of the default branch if no tagged versions are available.

 * `"usefulmodule": "username/repositoryname#^1.2.3"`
 
    Uses the highest tagged version matching the version specification.

 * `"usefulmodule": "username/repositoryname#tag-name"`

    Uses the specific tagged version.

 * `"usefulmodule": "username/repositoryname#branch-name"`
    
    Uses the latest committed version on the specified branch.

#### Depending on git Modules
To specify a module available from a non-Github git server as a dependency, use
a git URL:

 * `"usefulmodule": "git+ssh://somwhere.com/anything/anywhere"`
 * `"usefulmodule": "git+ssh://somwhere.com/anything/anywhere#<version specification>"`
 * `"usefulmodule": "git+ssh://somwhere.com/anything/anywhere#<branch name>"`
 * `"usefulmodule": "git+ssh://somwhere.com/anything/anywhere#<tag name>"`
 * `"usefulmodule": "<anything>://somwhere.git"`
 * `"usefulmodule": "<anything>://somwhere.git#<version spec, tag, or branch name>"`

#### Depending on hg Modules
To specify a module available from a mercurial server as a dependency, use
a hg URL:

 * `"usefulmodule": "hg+ssh://somwhere.com/anything/anywhere"`
 * `"usefulmodule": "hg+ssh://somwhere.com/anything/anywhere#<version specification>"`
 * `"usefulmodule": "<anything>://somwhere.hg"`
 * `"usefulmodule": "<anything>://somwhere.hg#<version specification>"`
 * `"usefulmodule": "hg+<anything>://somwhere"`
 * `"usefulmodule": "hg+<anything>://somwhere#<version specification>"`

Where <version specification> is a tag with a semantic version identifier.

**Note that modules depending on github, ssh, or hg repositories cannot be
published: they will be rejected by the yotta registry.**

<a name="targetDependencies"></a>
### `targetDependencies`
**type: Object `{"<target-identifier>": <dependencies object>}`**

The modules in the `dependencies` property are always installed and used, no
matter what the compilation target is. Sometimes it's useful to depend on
different modules when the compilation target is different – e.g. if compiling
for different embedded devices that have different ways of connecting to the
internet.

The `targetDependencies` property makes this possible.

Each value in the `targetDependencies` is a target identifier defining a set of
dependencies with the same format as the [`dependencies`](#dependencies) property.

When calculating the dependencies to install, `yotta` uses all sections
from `targetDependencies` that matches one of the identifiers in the current
target's [`similarTo` list](../tutorial/targets.html#similarto), or which match
properties that are defined to a truthy value in the [configuration
data](/reference/config.html).

To test nested values from config data, use dot-syntax,
`"mbed.meshing.supported"` in the following example tests that the "supported"
value is truthy in config data that looks like this:

```json
  {
    "mbed":{
      "meshing":{
        "supported":true
      }
    }
  }
```

A "truthy" json config value is any object or string, or non-zero numbers, or a
literal `true` boolean value.

**NOTE: in the future support for evaluating simple expressions on config
values may be added, but this is not currently possible. To choose which
one-of-n dependencies to use you must define N config values that are either
true or false, and require that they are set appropriately.**

Example:

```json
    "targetDependencies": {
        "k64f": {
            "mbed-hal-freescale": "^3.0.0",
            "mbed": "^3.0.0"
        },
        "mbed.meshing.supported": {
            "mbed-meshing": "^1.2.3"
        }
	}
```

<a name="testDependencies"></a>
### `testDependencies`
**type: Object `{"<modulename>": "<version specification or source>"}`**

The `testDependencies` section can be used to list modules that are only
depended on by tests. They will not normally be installed if your module is
installed as a dependency of another.

See [`dependencies`](#dependencies) for a description of how to specify
different sorts of dependencies.


### `description`
**type: String**

Brief of what your module does. This helps other people to find your module.
Include a `readme.md` file with a longer description, API documentation and
example code.

### `keywords`
**type: Array of String**

Keywords describe what your module does, and help other people to find it. 

### `homepage`
**type: String (url)**

The URL of your module's homepage (if any).

### `repository`
**type: String (url)**

The URL of your module's source code repository (if any). Including this helps
other people to contribute to your module by making it easy for them to clone
their own copy and suggest improvements.

**type: String (type)**

The type of the repostory specified by the strings "git", "hg" or "svn".

### `private`
**type: Boolean**

If present, and set to `true`, then `yotta publish` will not allow you to
publish this module to the public registry. This is useful to prevent
accidental publication of private modules and applications.

### `bugs`
**type: Object `{"url":"<url>", "email": "<optional email>"}`**

Including a bugs section helps people who use your module to report problems,
and suggest fixes.

Example:

```json
  "bugs": {
    "url": "http://github.com/ARMmbed/helloyotta/issues",
    "email": "helloyotta-bugs@example.com"
  }
```


### `bin`
**type: String (path relative to module root)**

If present, the `bin` property specifies a subdirectory that should be built
into an executable. Published modules should not normally use this property.

For example, to build an executable (instead of the default static library) out
of the contents of the source directory, set:

```json
  "bin": "./source"
```

### `extraIncludes`
**type: Array of String (paths relative to module root)**

**WARNING** do not use this property in released modules. It exists only to
simplify the porting of existing software modules to yotta.

Array of additional paths to be included in the header search path. By default
the module's root directory will be in the header search path when compiling
anything that depends on it (directly or indirectly).

The convention of using the module's name for the directory in the module root
that contains the public header files means that public header files can be
included as:

```c
#include "modulename/headername.h"
```

*without* specifying any additional include paths. This almost completely
eliminates any possibility of header name collision, as published module names
are forced to be unique by the yotta module registry.

<a name="scripts"></a>
### `scripts`
**type: hash of script-name to command**

Each command is an array of the separate command arguments.

The supported scripts are:

 * **testReporter**: this command is run for the tests of each module, and is
   piped the output of the tests. It may display information about the
   success/failure of a test, and should exit with a status 0 if the test
   passed, or a status 1 if the test failed.

For example, the scripts for a module that uses the "mbedgt" test framework,
would use the `mbedgt` helper program to parse and verify the test output:

```json
   "scripts": {
      "testReporter": ["mbedgt", "--digest", "stdin", "-v", "-V"]
   }
```
