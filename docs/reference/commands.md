---
layout: default
title: yotta Command Reference
section: reference/commands
---

# Command Reference
## <a href="#yotta" name="yotta">#</a> yotta
Synonyms: `yt`

The `yotta` command is always run with a subcommand in order to do something, `yotta` with no subcommand will only display help and version information with the `--help` and `--version` options.
`yt` can be used as a shortcut for `yotta` in all commands.

Options:
 
 * `yotta --version`: Display the version of yotta.
 * `yotta --help`: Display help for yotta, including a list of subcommands.
 * `yotta <subcommand> --help`: display help for a specific subcommand.

Additional Options that can be used with all subcommands:

 * `yotta --plain <subcommand>`: Don't use coloured output.
 * `yotta --noninteractive <subcommand>`: Don't wait for user input.
 * `yotta --target <targetname>`: Override the currently set target for this
   command (useful when isolating several instances of yotta)
 * `yotta --config <configfile or JSON>`: Override the target and
   application-defined [configuration](/reference/config.html). This is useful
   in CI infrastructure to easily change the configuration for a particular
   build.

## <a href="#yotta-init" name="yotta-init">#</a> yotta init
#### Synopsis

```
yotta init
```

#### Description
Create a new `module.json` module-description file based on a set of questions. If a `module.json` file already exists, the values in it will be used as defaults, and it will not delete anything from the file.

## <a href="#yotta-build" name="yotta-build">#</a> yotta build
#### Synopsis

```
yotta build [--generate-only] [--debug-build] [--cmake-generator <cmake-generator-name>] [name ... ]
yotta build [ ... ] -- [ build-tool arguments ]
```

#### Description
Build the current module and its dependencies. Missing dependencies will be automatically installed first.

If no `name` arguments are specified then the current module's tests will be
built, but not the tests for any other module. Use the `yotta build all_tests`
to build the tests for all dependency modules.

`yotta` uses [CMake](http://www.cmake.org) to control the build, the basic process is:

 1. `yotta` installs the target description for the build target
 2. `yotta` installs all module dependencies (which may depend on which target is being built for)
 3. `yotta` generates CMakeLists.txt describing the libraries and executables to build
 4. `yotta` instructs CMake to generate the make files / ninja files / IDE project file (depending on `--cmake-generator`)
 5. `yotta` instructs CMake to execute the build. The compiler used depends on the CMake Toolchain file provided by the active `yotta target`.

For more information on the yotta build process, see the [build system
reference](/reference/buildsystem.html).

Options:

  * **`--generate-only`, `-g`**: only generate the CMakeLists, don't build

  * **`--debug-build`, `-d`**: build a debug (less-optimised) build.

    The effects depend on the target (this selects CMake build type `Debug`),
    but generally this means no optimisation, and `NDEBUG` is not defined.

  * **`--release-build`, `-r`**: build a release (optimised) build.   **deprecated**

    The effects depend on the target (this selects CMake build type
    `RelWithDebInfo`).
    This option is deprecated because it is now the default, unless
    `--debug-build` is specified.

  * **`--cmake-generator`, `-G`**: specify the CMake Generator. CMake can generate project files for various editors and IDEs.

  * **`name ...`**: one or more modules may be specified, in which case only these
   modules and their dependencies will be built. Use `all_tests` to cause all
   tests to be built.

  * **`-- ...`**: any options specified after `--` are passed unmodified on to the tool being used for building (e.g. Ninja, or make)

#### Generating IDE Project Files
The `-G`/`--cmake-generator` option can be used to generate project files for
various IDE and text editors. This option is passed through to CMake, but note
that only IDE project files which use Ninja or Makefile build systems will
correctly support cross-compilation for yotta targets.

To see the [CMake generators](https://cmake.org/cmake/help/v3.0/manual/cmake-generators.7.html)
available on your platform see `cmake --help`.


#### Examples

Build this module and its tests:

```sh
yotta build
```

Build the tests for all dependencies:

```sh
yotta build -d all_tests
```

Generating IDE project files:

```sh
yotta build -d -G "Sublime Text 2 - Ninja"
yotta build -d -G "Eclipse CDT4 - Ninja"
```

Passing options through to the build system:

```sh
yotta build -G "Unix Makefiles" -- -j 4
yotta build -- -v
```

## <a href="#yotta-search" name="yotta-search">#</a> yotta search
#### Synopsis
```
yotta search <string> [--keyword=<keyword>] [--limit=<N>]
yotta search module <string> [--keyword=<keyword>] [--limit=<N>]
yotta search target <string> [--keyword=<keyword>] [--limit=<N>]
```

#### Description

Search for open-source yotta modules and build targets that have been published
to the yotta registry.

The results will be listed in combined order of search relevance and
popularity.

Options:

 * `--keyword`, `-k`: specify keywords to constrain the search (use multiple
   times for multiple keywords, modules returned will have all of the specified
   keywords)
 * `--limit`, `-l`: limit the number of results returned

#### Examples

```
yotta search logging
yotta search module logging
yotta search target -k mbed-official -k mbed-target:k64f
```

## <a href="#yotta-test" name="yotta-test">#</a> yotta test
#### Synopsis

```
yotta test [--list] [--no-build] [ build-arguments ] [tests-to-run ...]
```

#### Description

Run tests. If no arguments are specified, then the tests for the current module
will be run, use `yotta test all` to run the tests for all modules.

The [target description](/tutorial/targets.html) provides support for the test
command if it is a cross-compiling target (no support is necessary to run tests
natively). The `scripts.test` value in the target description is executed with
`$program` expanded to the path to the binary, it should be a wrapper script
that loads the binary at the specified path onto the target device, runs it,
and prints output on standard output.

Options:

 * `--list`, `-l`: List the tests that would be run, rather than running them.
   Implies `--no-build`.
 * `--no-build`, `-n`: Don't build anything, try to run already-built tests.
   Things will fail if all the specified tests are not built!
 * This command also accepts the options to [`yotta build`](#yotta-build),
   which are used if building.

#### Examples

```
yotta test
yotta test --list all
yotta test -n my-test
yotta test --config="path/to/test-config.json"
```
   

## <a href="#yotta-debug" name="yotta-debug">#</a> yotta debug
#### Synopsis

```
yotta debug <program>
```

#### Description

If the target description supports it, launch a debugger attached to the specified executable.

#### Examples

```
yotta debug test/simplelog-test
yotta debug source/helloyotta
```

## <a href="#yotta-target" name="yotta-target">#</a> yotta target
#### Synopsis

```
yotta target
yotta target <targetname>[@url-or-version-spec] [-g] [-n]
```

#### Description
Display or set the current target. `yotta` will look for and install a target
description from the `yotta` registry when building or installing dependencies.
If you run `yotta target` in an existing module then yotta will attempt to
download the target description immediately, unless `-n` is specified.

Targets define the options and commands that `yotta` uses to compile modules and executables. 

A target must define a CMake Toolchain file describing all of the rules that `yotta` uses to build software, it may also define commands to launch a debugger (used by `yotta debug`).

If `-g` is specified when setting the target, then it will be saved globally
(in the user settings file). Otherwise the specified target will be saved for
the current module only, in a `.yotta.json` file.

If the target is set both locally and globally, then the locally set target
takes precedence.

#### Examples

```
yotta target x86-osx-native
yotta target frdm-k64f-gcc@^2.0.0
```

## <a href="#yotta-install" name="yotta-install">#</a> yotta install
Synonyms: `yotta in`
#### Synopsis

```
# in a module directory:
yotta install
yotta install <module>[@<version>]
# anywhere:
yotta install <module>[@<version>] [--global]
```

#### Description
Install a module, including modules that it depends on.

Typical usage is:

```
yotta install <module>
```

Which installs `<module>` and its dependencies, and saves it in the current module's description file.

A `<module>` is one of:

  * a name, in which case the module is installed from the public registry (<https://yottabuild.org>)
  * a github spec (username/reponame), in which case the module is installed directly from github. This can include private github URLs.

#### `yotta install` (no arguments, in a module folder)
In a module directory, `yotta install` will check for and install any missing dependencies of the current module. Options:

 * `--install-linked`: also traverse into any linked modules, and install their dependencies. By default linked modules are not modified. Note that without this option all the required dependencies to build may not be installed.

#### `yotta install <module>` (in a module folder)
In a module directory, `yotta install <module>` will install the specified module, and any missing dependencies for it.

The installed version of the module will be saved as a dependency into the
current module's module.json file. This uses the `^` semantic-version specifier
to specify that only minor version updates are allowed to be installed,
**unless** the module has a 0.x.x version number, in which case the `~`
semantic-version specifier is used restrict updates to patch versions only.

#### `yotta install <module>` (anywhere)
Download the specified dependency, and install it in a subdirectory of the current directory. Options:

 * `--global`: install the specified module into the global modules directory instead.

#### Examples

```
yotta install simpleog
yotta install ARM-RD/simplelog
```

## <a href="#yotta-update" name="yotta-update">#</a> yotta update
Synonyms: `yotta up`
#### Synopsis

```
yotta update
yotta update <module>
```

#### Description
Update all of the current modules dependencies to the latest matching versions. Or, if a module is specified, update only that module and its dependencies.

Options:

 * `--update-linked`: update the dependencies of linked modules too.

## <a href="#yotta-version" name="yotta-version">#</a> yotta version
Synonyms: `yotta v`
#### Synopsis

```
yotta version [patch | minor | major | <version>]
```

#### Description
Bump the current module's version, set a new version, or display the current version. `patch`, `minor` and `major` declare which part of the major.minor.patch version number to bump.

If the current module is version-controlled by mercurial or git, then the new version is tagged. If the module is version controlled but the working directory is not clean, then an error message is printed.

## <a href="#yotta-login" name="yotta-login">#</a> yotta login
#### Synopsis

```
yotta login
```

#### Description
Authenticate with the `yotta` registry. `yotta` will open a browser to an OAuth login page on the `yotta` registry, where you can then log in with either GitHub or mbed. This process generates a secret access token that is saved in your `yotta` configuration file, and which `yotta` can use to pull from private repositories that you have access to on GitHub or mbed.

You must log in before you can publish modules. Access control for publishing is based on email addresses verified by GitHub/mbed, you can see the email address of the owners with permission to publish a given module using the `yotta owners` command.

No information other than your email address, and a public key generated by your `yotta` client, is stored by the `yotta` registry. Even someone with access to the `yotta` registry's database would not be able to publish modules in your name without stealing information that never leaves your computer!


## <a href="#yotta-logout" name="yotta-logout">#</a> yotta logout
#### Synopsis

```
yotta logout
```

#### Description
Remove all saved authentication information from the current computer. Does not revoke access tokens, as GitHub returns the same access token for each computer that you log into `yotta` on. If you wish to revoke access tokens you can do so on your GitHub account page.

## <a href="#yotta-whoami" name="yotta-whoami">#</a> yotta whoami
#### Synopsis

```
yotta whoami
yotta who
```

#### Description
Display the primary email address(es) that you are currently authenticated to.
If you are not logged in then this will return a non-zero status code,
otherwise the status code is 0.

#### Examples
```sh
> yotta whoami
friend@example.com

> yotta logout
> yotta whoami
not logged in
```


## <a href="#yotta-publish" name="yotta-publish">#</a> yotta publish
#### Synopsis

```
yotta publish
```

#### Description
Publish the current module or target to the public [`yotta` registry](https://yottabuild.org), where other people will be able to search for and install it.

Any files matching lines in the `.yotta_ignore` file (if present) are ignored,
and will not be included in the published tarball.


## <a href="#yotta-link" name="yotta-link">#</a> yotta link
Synonyms: `yotta ln`
#### Synopsis

```
yotta link (in a module directory)
yotta link <modulename>
yotta link /path/to/a/module
```

#### Description
Module linking allows you to use local versions of modules when building other modules – it's useful when fixing a bug in a dependency that is most easily reproduced when that dependency is used by another module.

To link a module there are two steps. First, in the directory of the dependency:

```
yotta link
```

This will create a symlink from the global modules directory to the current module.

Then, in the module that you would like to use the linked version of the dependency, run:

```
yotta link <depended-on-module-name>
```

When you run `yotta build` it will then pick up the linked module.

This works for direct and indirect dependencies: you can link to a module that your module does not use directly, but a dependency of your module does.

The variant of the command which takes a path to an existing module (e.g. `yotta link ../path/to/a/module`) performs both steps in sequence, for convenience.

**WARNING:** yotta uses directory junctions to provide links on windows. **Some
command line tools are not aware of directory junctions and will recurse
through them** (such as the version of `rm` that ships with msys). Be careful
if you recursively delete your yotta_modules folder. yotta itself will never
modify or remove files through a link, and windows explorer will also treat
them correctly.

#### Directories
When you run `yotta link`, links are created in a system-wide directory under
`YOTTA_PREFIX`, and the links in that directory are then picked up by
subsequent `yotta link <modulename>` commands.

On linux this defaults to `/usr/local`, and on windows to the python
installation directory (normally `c:\Python27`). To change this directory (e.g.
to make yotta link things into your home directory), set the `YOTTA_PREFIX`
environment variable.


## <a href="#yotta-link-target" name="yotta-link-target">#</a> yotta link-target
#### Synopsis

```
yotta link-target (in a target directory)
yotta link-target <targetename>
yotta link-target /path/to/a/target
```

#### Description
Like module linking, target linking allows you to use local versions of targets when building modules – it's useful when developing and testing target descriptions.

To link a target you need to perform two steps. First, in the directory of the target:

```
yotta link-target
```

This will create a symlink from the global targets directory to the current target.

Then, in the module that you would like to use the linked version of the target, run:

```
yotta link-target <targetename>
```

When you run `yotta build` (provided you've set `yotta target` to `<targetname>`), the linked target description will be used.

The variant of the command which takes a path to an existing module (e.g. `yotta link ../path/to/a/module`) performs both steps in sequence, for convenience.

See also [yotta link](#yotta-link).


## <a href="#yotta-list" name="yotta-list">#</a> yotta list
Synonyms: `yotta ls`
#### Synopsis

```
yotta list [--all]
yotta list [--json]
```

#### Description
List the installed dependencies of the current module, including information on
the installed versions. Unless `--all` is specified, dependencies are only
listed under the modules that first use them, with `--all` dependencies that
are used my multiple modules are listed multiple times (but all modules will
use the same installed instance of the dependency).

The `--json` option will cause the list to be output in JSON format, for
example:

```JSON
{
  "modules": [
    {
      "name": "toplevel-module-name",
      "version": "1.0.0",
      "path": "/some/path/on/disk/toplevel-module-name",
      "specifications": [
        {
          "version": "~0.11.0",
          "name": "some-dependency-name"
        }
      ]
    },
    {
      "name": "some-dependency-name",
      "version": "0.11.7",
      "path": "/some/path/on/disk/yotta_modules/some-dependency-name",
      "linkedTo": "/some/path/on/disk/some-dependency-name",
      "specifications": [
        {
          "version": "ARMmbed/some-test-dependency#^1.2.3",
          "name": "some-test-dependency",
          "testOnly": true
        }
      ]
    },
    {
      "name": "some-test-dependency",
      "version": "1.5.6",
      "path": "/some/path/on/disk/yotta_modules/some-test-dependency",
      "errors": [
        "a description of some error with this module"
      ]
    }
}
```


## <a href="#yotta-uninstall" name="yotta-uninstall">#</a> yotta uninstall
Synonyms: `yotta unlink`, `yotta rm`, `yotta un`
#### Synopsis

```
yotta uninstall <module>
```

#### Description
Remove the specified dependency of the current module (or destroy the symlink if it was linked).

## <a href="#yotta-owners" name="yotta-owners">#</a> yotta owners
Synonyms: `yotta owner`
#### Synopsis

```
yotta owners list [<modulename>]
yotta owner add <email> [<modulename>]
yotta owner remove <email> [<modulename>]
```

#### Description
List, add, or remove owners from the specified module or target. Owners are people with permission to publish new versions of a module, and to add/remove other owners.

If the current directory is a module or target, then the module name is optional, and defaults to the current module.


## <a href="#yotta-licenses" name="yotta-licenses">#</a> yotta licenses
#### Synopsis

```
yotta licenses [--all]
```

#### Description
List the licenses of all of the modules that the current module depends on. If
`--all` is specified, then each unique license is listed for each module it
occurs in, instead of just once.

**NOTE:** while yotta can list the licenses that modules have declared in their
`module.json` files, it can make no warranties about whether modules contain
code under other licenses that have not been declared.

## <a href="#yotta-config" name="yotta-config">#</a> yotta config
#### Synopsis

```
yotta config
```

#### Description
Display the merged [config data](/reference/config.html) for the current target
(and application, if the current module defines an executable application).

The config data is produced by merging the json config data defined by the
application, the current target, and any targets the current target inherits
from recursively. Values defined by the application will override those defined
at the same path by targets, and values defined in targets will override values
defined by targets they inherit from.

The config data displayed is identical to the data that will be available to
modules when they are built.

See the [config system reference](/reference/config.html) for more details.

## <a href="#yotta-outdated" name="yotta-outdated">#</a> yotta outdated

#### Synopsis

```
yotta outdated
```

#### Description
List modules for which newer versions are available from the yotta registry.

## <a href="#yotta-shrinkwrap" name="yotta-shrinkwrap">#</a> yotta shrinkwrap

#### Synopsis

```
yotta shrinkwrap
```

#### Description
Create a `yotta-shrinkwrap.json` file in the current module, which specifies
the exact versions of dependencies and target descriptions currently being
used.

When a module with a `yotta-shrinkwrap.json` file is installed, the versions
specified in the shrinkwrap will be downloaded from the public yotta registry,
instead of the latest versions that satisfy the specifications from module.json
files. **When a shrinkwrap file is present, dependencies will always be
downloaded from the registry, not from git/other URLs.**

In practise this allows an application or module to specify a known-good set of
dependencies that it should be used with.

Note that generally publishing modules with a `yotta-shrinkwrap.json` file to
the yotta registry should be avoided. The exact versions specified in the
shrink-wrap could easily cause version conflicts with other modules which
depend on the same modules.

The format of the `yotta-shrinkwrap.json` file is:

```
{
  "modules": [
    {
      "version": "1.0.0",
      "name": "first-module-name"
    },
    {
      "version": "0.11.7",
      "name": "a-dependency-name"
    },
    ...
  ],
  "targets": [
   {
     "version": "1.2.3",
     "name": "some-target-name"
   },
   ...
  ]
}
```
