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
  "license": "Apache-2.0",
  "dependencies": {
    "simplelog": "~0.0.0"
  },
  "targetDependencies": {},
  "bin": "./source"
}
```

## Properties

### <a href="name" name="name">#</a> `name` *required*
**type: String**

The unique name of your module. It's got to be globally unique, so be
adventurous!

Names can use only lowercase letters, numbers, and hyphens, but must start with
a letter. (This reduces problems with case insensitive filesystems, and
confusingly similar names.)


### <a href="version" name="version">#</a> `version` *required*
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


### <a href="licenses" name="licenses">#</a> `licenses` *deprecated*
See also: [`license`](#license). The `licenses` property was formerly a method
of specifying that multiple licenses applied to a module. It's now preferred to
use a single `license` field containing a SPDX license expression.

`licenses` example:

```json
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
```

### <a href="license" name="license">#</a> `license` *required*
**type: String** `"<SPDX license identifier>"`**

The license property in module.json should include all of the licenses that
affect code in your module. For example:

```json
  "license": "Apache-2.0"
```

The license identifiers are from the [SPDX list](http://spdx.org/licenses/).
[SPDX license expressions](/reference/licenses.html) can be used for compound
licenses.

According to [SPDX v2.0](https://spdx.org/sites/spdx/files/SPDX-2.0.pdf), custom licenses in a file should be entered as:

```json
  "license": "LicenseRef-LICENSE.pdf"
```

If you're starting a completely new module, and have freedom to choose the
license yourself, `yotta`'s preferred license is
[Apache-2.0](http://spdx.org/licenses/Apache-2.0), a permissive OSI-approved
open source license which provides clarity over the scope of patent grants.
`yotta` itself is also licensed under Apache-2.0.

When you run `yotta init` to initialise a new module, yotta will suggest some
licenses, and automatically fill in the license field for those options.

**Remember: some people will find it much harder to use your module if you
don't use a standard permissive license.**

### <a href="#dependencies" name="dependencies">#</a>`dependencies`
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

### <a href="targetDependencies" name="targetDependencies">#</a> `targetDependencies`
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

To test nested values from config data, use [JSON pointer syntax](https://tools.ietf.org/html/rfc6901),
`"/mbed/meshing/supported"` in the following example tests that the "supported"
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
        "/mbed/meshing/supported": {
            "mbed-meshing": "^1.2.3"
        }
	}
```

### <a href="#testDependencies" name="testDependencies">#</a> `testDependencies`
**type: Object `{"<modulename>": "<version specification or source>"}`**

The `testDependencies` section can be used to list modules that are only
depended on by tests. They will not normally be installed if your module is
installed as a dependency of another.

See [`dependencies`](#dependencies) for a description of how to specify
different sorts of dependencies.


### <a href="#description" name="description">#</a> `description`
**type: String**

Brief of what your module does. This helps other people to find your module.
Include a `readme.md` file with a longer description, API documentation and
example code.

### <a href="#keywords" name="keywords">#</a>`keywords`
**type: Array of String**

Keywords describe what your module does, and help other people to find it.

### <a href="#homepage" name="homepage">#</a>`homepage`
**type: String (url)**

The URL of your module's homepage (if any).

### <a href="#repository" name="repository">#</a>`repository`
**type: Object `{"url":"<url>", "type": "<git, hg, or svn>"}`**

The `repository` section helps other people to contribute to your module by
making it easy for them to clone their own copy and suggest improvements.

The URL of your module's source code repository and the type of the repository
should be included.

**Note:** this repository field is intended as a place where people can find
and contribute back to your module. It is never used by yotta to download code.
See the [dependencies](#dependencies) section for information on how to depend
on modules from source control repositories, instead of from the public modules
registry.


### <a href="#private" name="private">#</a> `private`
**type: Boolean**

If present, and set to `true`, then `yotta publish` will not allow you to
publish this module to the public registry. This is useful to prevent
accidental publication of private modules and applications.

### <a href="#bugs" name="bugs">#</a> `bugs`
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


### <a href="#bin" name="bin">#</a> `bin`
**type: String (path relative to module root)**

If present, the `bin` property specifies a subdirectory that should be built
into an executable. Published modules should not normally use this property.

For example, to build an executable (instead of the default static library) out
of the contents of the source directory, set:

```json
  "bin": "./source"
```

### <a href="#lib" name="lib">#</a> `lib`
**type: String (path relative to module root)**

If present, the `lib` property specifies a subdirectory that should be built
into a library. If it isn't specified, then the default behaviour is for the
"source" directory to be built into a library.

For example, to build a library out of the contents of `./some/subdirectory`
instead of the default `source` directory, use:

```json
  "lib": "./some/subdirectory"
```

### <a href="#extraIncludes" name="extraIncludes">#</a> `extraIncludes`
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

### <a href="#scripts" name="scripts">#</a> `scripts`
**type: hash of script-name to command**

Each command is either an array of the separate command arguments, or a single
string which yotta will split into parts based on normal shell command
splitting rules.

Any script which is a `.py` file will be invoked using the python interpreter
which is running yotta.

The supported scripts are:

 * **`preVersion`**: Runs before the [`yotta
   version`](/reference/commands.html#yotta-version)
   command increments the version number. The old and new version numbers are
   available as environment variables `YOTTA_OLD_VERSION` and
   `YOTTA_NEW_VERSION`.  Can return non-zero to prevent continuing.
 * **`postVersion`**: Runs after the version has been bumped by `yotta
   version`, but before any changes have been committed or tagged in VCS
   (returning non-zero will prevent
   anything from being committed).
 * **`prePublish`**: Runs before the module is
   [published](/reference/commands.html#yotta-publish). Can return non-zero to
   prevent publishing.
 * **`postPublish`**: Runs after the module has been published. Tweet here.
 * **`postInstall`**: Runs once after a module is downloaded into
   `yotta_modules`, or downloaded as a top-level module.
 * **`preGenerate`**: Runs before generating CMake for any build including this
   module.
 * **`preBuild`**: Runs immediately before each build including this module.
 * **`postBuild`**: Runs after everything has been built. This script will be
   run whether or not this module was actually re-built (so don't do slow
   things here!): consider using a .cmake file to define post-build rules
   instead.
 * **`preTest`**: Runs before tests from this module are loaded by the target's
   scripts.test script.
 * **`preDebug`**: Runs before this module (if it is an application), or one of
   its tests is loaded by the target's scripts.debug script.
 * **`preStart`**: Runs before this module (if it is an application) is loaded
   by the target's scripts.start script.
 * **`testReporter`**: this command is run for the tests of each module, and is
   piped the output of the tests. It may display information about the
   success/failure of a test, and should exit with a status 0 if the test
   passed, or a status 1 if the test failed.
 
The `preGenerate`, `preBuild` and `postBuild` scripts have the merged [config
information](/reference/config.html) available to them in a file indicated by the
`YOTTA_MERGED_CONFIG_FILE` environment variable.

#### Examples

A module that uses the [greentea](https://github.com/ARMmbed/greentea) test
framework, would use the `greentea` helper program to parse and verify the test
output might use this testReporter script:

```json
   "scripts": {
      "testReporter": ["greentea", "--digest", "stdin", "-v", "-V"]
   }
```


### <a href="#yotta" name="yotta">#</a>  `yotta`
**type: version specification**

A version specification for the version of yotta that this module requires. For
example:

```json
   "yotta": ">=0.13.0"
```

```json
   "yotta": ">=0.10.0, !0.12.0"
```

If your module requires functionality that was introduced in a specific yotta
version, then you can use this property so that older versions of yotta report
a clear error message to the user that they need to upgrade before using your
module.
