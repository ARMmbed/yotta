---
layout: default
title: Yotta Command Reference
section: reference/commands
---

## Command Reference
<a name="yotta"></a>
### yotta
synonyms: `yt`
The yotta command is always run with a subcommand in order to do something, `yotta` with no subcommand will only display help and version information with the `--help` and `--version` options.
`yt` can be used as a shortcut for `yotta` in all commands.

Options:
 
 * `yotta --version`: Display the version of yotta.
 * `yotta --help`: Display help for yotta, including a list of subcommands.
 * `yotta <subcommand> --help`: display help for a specific subcommand.

<a name="yotta-init"></a>
### yotta init
#### Synopsis

```
yotta init

```
#### Description
Create a new `module.json` module-description file based on a set of questions. If a `module.json` file already exists, the values in it will be used as defaults, and it will not delete anything from the file.

<a name="yotta-build"></a>
### yotta build
#### Synopsis

```
yotta build [--generate-only / -g] [--release-build / -r] [--cmake-generator / -G <cmake-generator-name>]
```

#### Description
Build the current module and its dependencies. Missing dependencies will be automatically installed first.

yotta uses [CMake](http://www.cmake.org) to control the build, the basic process is:

 1) yotta installs the target description for the build target
 2) yotta installs all module dependencies (which may depend on which target is being built for)
 3) yotta generates CMakeLists.txt describing the libraries and executables to build
 4) yotta instructs CMake to generate the make files / ninja files / IDE project file (depending on `--cmake-generator`)
 5) yotta instructs CMake to execute the build. The compiler used depends on the CMake Toolchain file provided by the active `yotta target`.

Options:

 * `--generate-only`, `-g`: only generate the CMakeLists, don't build
 * `--release-build`, `-r`: build a release (optimised) build. The exact effects depend on the toolchain.
 * `--cmake-generator`, `-G`: specify the CMake Generator. CMake can generate project files for various editors and IDEs, though some IDEs may not be able to use non-standard compilers defined by yotta targets without additional plugins. The available generators depend on whether yotta is running on OS X, Linux, or Windows.

#### Examples

```
yotta build -r
yotta build -r -G "Sublime Text 2 - Ninja"
```

<a name="yotta-debug"></a>
### yotta debug
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

<a name="yotta-target"></a>
### yotta target
#### Synopsis

```
yotta target
yotta target <targetname>[,url-or-version-spec]
```

#### Description
Display or set the current target. Yotta will look for and install a target description from the yotta registry when building or installing dependencies.

Targets define the options and commands that yotta uses to compile modules and executables. Currently only `x86-osx-native` and `x86-linux-native` targets are available.

A target must define a CMake Toolchain file describing all of the rules that yotta uses to build software, it may also define commands to launch a debugger (used by `yotta debug`).

<a name="yotta-install"></a>
### yotta install
synonyms: `yotta in`, `yotta i`
#### Synopsis

```
(in a module directory)
yotta install
yotta install <module>[@<version>] [--save | --save-target]
(anywhere)
yotta install <module>[@<version>] --global
```

#### Description
Install a module, including modules that it depends on.

Typical usage is:

```
yotta install <module> --save
```

Which installs `<module>` and its dependencies, and saves it in the current module's description.

A `<module>` is one of:
 * a name, in which case the module is installed from the public registry (<yottabuild.org>)
 * a github spec (username/reponame), in which case the module is installed directly from github. This can include private github URLs.

##### yotta install (no arguments, in a module folder)
In a module directory, `yotta install` will check for and install any missing dependencies of the current module. Options:

 * `--install-linked`: also traverse into any linked modules, and install their dependencies. By default linked modules are not modified. Note that without this option all the required dependencies to build may not be installed.

##### `yotta install <module>` (in a module folder)
In a module directory, `yotta install <module>` will install the specified module, and any missing dependencies for it. Accepts the following options:

 * `--save`: saves the installed version of the module to the module.json file. This uses the `^` semantic-version specifier to specify that only minor version updates are allowed to be installed, **unless** the module has a 0.x.x version number, in which case the `~` semantic-version specifier is used restrict updates to patch versions only.
 * `--save-target`: saves the installed version of the module (as `--save`), but only when building for the current target. See the `targetDependencies` section of the [module.json reference](/../reference/module.html).

##### `yotta install <module>` (anywhere)
Download the specified dependency, and install it in a subdirectory of the current directory. Options:

 * `--global`: install the specified module into the global modules directory instead.

##### Examples

```
yotta install simpleog
yotta install ARM-RD/simplelog@0.0.0 --save
```

<a name="yotta-update"></a>
### yotta update
synonyms: `yotta up`
#### Synopsis

```
yotta update
yotta update <module>
```

#### Description
Update all of the current modules dependencies to the latest matching versions. Or, if a module is specified, update only that module and its dependencies.

Options:
 * `--update-linked`: update the dependencies of linked modules too.

<a name="yotta-version"></a>
### yotta version
synonyms: `yotta v`
#### Synopsis

```
yotta version [patch | minor | major | <version>]
```

#### Description
Bump the current module's version, set a new version, or display the current version. `patch`, `minor` and `major` declare which part of the major.minor.patch version number to bump.

If the current module is version-controlled by mercurial or git, then the new version is tagged. If the module is version controlled but the working directory is not clean, then an error message is printed.

### yotta login
#### Synopsis

```
yotta login
```

#### Description
Authenticate with the yotta registry. yotta will open a browser to an OAuth login page on the yotta registry, where you can then log in with either GitHub or mbed. This process generates a secret access token that is saved in your yotta configuration file, and which yotta can use to pull from private repositories that you have access to on GitHub or mbed.

You must log in before you can publish modules. Access control for publishing is based on email addresses verified by GitHub/mbed, you can see the email address of the owners with permission to publish a given module using the `yotta owners` command.

No information other than your email address, and a public key generated by your yotta client, is stored by the yotta registry. Even someone with access to the yotta registry's database would not be able to publish modules in your name without stealing information that never leaves your computer!


<a name="yotta-logout"></a>
### yotta logout
#### Synopsis

```
yotta logout
```

#### Description
Remove all saved authentication information from the current computer. Does not revoke access tokens, as GitHub returns the same access token for each computer that you log into yotta on. If you wish to revoke access tokens you can do so on your GitHub account page.


<a name="yotta-publish"></a>
### yotta publish
#### Synopsis

```
yotta publish
```

#### Description
Publish the current module or target to the public yotta registry, where other people will be able to search for and install it.


<a name="yotta-link"></a>
### yotta link
synonyms: `yotta ln`
#### Synopsis

```
yotta link (in a module directory)
yotta link <modulename>
```

#### Description
Module linking allows you to use local versions of modules when building other modules – it's useful when fixing a bug in a dependency that is most easily reproduced when that dependency is used by another module.

To link a module you need to perform two steps. First, in the directory of the dependency:

```
yotta link
```

This will ensure it has all of its own dependencies installed, and then create a symlink from the global modules directory to the current module.

Then, in the module that you would like to use the linked version of the dependency, run:

```
yotta link <depended-on-module-name>
```

When you run `yotta build` it will then pick up the linked module.

This works for direct and indirect dependencies: you can link to a module that your module does not use directly, but a dependency of your module does.


<a name="yotta-link-target"></a>
### yotta link-target
#### Synopsis

```
yotta link-target (in a target directory)
yotta link-target <targetename>
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

<a name="yotta-list"></a>
### yotta list
synonyms: `yotta ls`
#### Synopsis

```
yotta list [--all]
```

#### Description
List the installed dependencies of the current module, including information on the installed versions. Unless `--all` is specified, dependencies are only listed under the modules that first use them, with `--all` dependencies that are used my multiple modules are listed multiple times (but all modules will use the same installed instance of the dependency).

<a name="yotta-uninstall"></a>
### yotta uninstall
synonyms: `yotta unlink`, `yotta rm`
#### Synopsis

```
yotta uninstall <module>
```

#### Description
Remove the specified dependency of the current module (or destroy the symlink if it was linked).

<a name="yotta-owners"></a>
### yotta owners
synonyms: `yotta owner`
#### Synopsis

```
yotta owners list [<modulename>]
yotta owner add <email> [<modulename>]
yotta owner remove <email> [<modulename>]
```

#### Description
List, add, or remove owners from the specified module or target. Owners are people with permission to publish new versions of a module, and to add/remove other owners.

If the current directory is a module or target, then the module name is optional, and defaults to the current module.
