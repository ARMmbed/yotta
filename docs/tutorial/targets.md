---
layout: default
title: Using Targets to Compile for Different Platforms
section: tutorial/targets
---

## Using Targets to Compile for Different Platforms

Target descriptions allow `yotta` to compile the same code for different target
platforms (different desktop operating systems, or different embedded devices).

The description contains information on:

 * a [Toolchain File](#toolchainfile), which describes how to run the compiler
 * Any supporting files required to compile (such as link scripts)
 * Configuration information associated with this target, for example
   describing what hardware functionality is available.
 * What other targets this target should be considered "similar to". This
   information is used to resolve dependencies.

And optionally provides information on:

 * how to run the debugger (`yotta debug` support)
 * how to run tests, where they cannot be run natively (`yotta test` support)

Each yotta target contains a [target.json](../reference/target.html) file, which
describes where to find this other information.

### <a href="#selecting-targets" name="selecting-targets">#</a> Selecting the Target

To view or change the current target, use the `yotta target` subcommand:

```sh
# display the current target:
yotta target

# set the target to x86-osx-native
yotta target x86-osx-native
```

By default the target is set in the *current directory only*. To set it
globally, append ` -g` to the second command. You can switch targets back and
forth to test building the same module for different targets without removing
the build directory or recompiling unnecessarily, as builds are carried out a
separate directory for each target: `./build/<targetname>/`.


## <a href="#writing-targets" name="writing-targets">#</a> Writing Targets

### <a href="#inheriting" name="inheriting">#</a> Inheriting from an Existing Target

Target descriptions usually inherit from an existing description. This allows
you to extend the description that already exists instead of writing everything
from scratch. With inheritance you override or add only the things that need
changing.

For example, this is a simple target hierarchy from mbed OS:

 * base: [mbed-gcc](https://github.com/armmbed/target-mbed-gcc): this target
   description describes how to run the arm-none-eabi-gcc cross-compiler, but
   doesn't say anything about which chip or board is being compiled for.
 * derived: [frdm-k64f-gcc](https://github.com/armmbed/target-frdm-k64f-gcc):
   this inherits from mbed-gcc, and adds compilation flags specific to
   compiling for the FRDM-K64F development board. This target description could
   actually be further split so that the description of the compilation flags
   for the main MCU on the board is separate from the description related to the
   board's peripherals.

If you were building a product derived from the FRDM-K64F development board
schematic you would choose to inherit from the existing frdm-k64f target.

To make your target description inherit from an existing one define the
[`inherits` property](/reference/target.html#inherits) in your target.json file:

```json
  ...
  "inherits": {
      "some-base-target": "^1.2.3"
  }
  ...
```

Note the version specification next to the name of the description you inherit
from. Target descriptions use [semantic versioning](http://semver.org) just
like modules do: it's normally a good idea to use the `^` version specification
which allows any compatible version to be used. Just like module version
specifications this can also be a github, git or mercurial reference if your
target inherits from another target that hasn't been published yet.

### <a href="#toolchainfile" name="toolchainfile">#</a> The Toolchain File
`yotta` uses the [CMake](http://www.cmake.org) build system, and targets
describe how the compiler should be run by providing a CMake [Toolchain
File](http://www.cmake.org/cmake/help/v3.0/manual/cmake-toolchains.7.html).

To use the system's native compiler, the toolchain doesn't need to do anything,
but cross-compiling toolchain descriptions can get a lot more complicated, and
must define every command necessary to compile programs.

By convention, the toolchain file is placed in a CMake subdirectory of the
target:

```sh
.
├── CMake
│   └── toolchain.cmake
├── readme.md
└── target.json
```

Though the path is actually specified in the `toolchain` property in target.json:

```json
  "toolchain": "CMake/toolchain.cmake"
```

### <a href="#config" name="config">#</a> yotta Config Information
In addition to the `similarTo` data, your target can also define arbitrary JSON
configuration data that can be used as the basis for including dependencies and
providing configuration to the modules being built. See the [config system
reference](/reference/config.html) for details.

### <a href="#similarto" name="similarto">#</a> The similarTo List and Target Specific Dependencies
The similarTo list in a target description is the list of targets that the
target should be considered "similar to". This is defined by target.json:

```json
  "similarTo": <list of strings>,
```

This list is used (in addition to the config information) to choose which
dependencies to pick when a module has target-specific dependencies (defined by
the `targetDependencies` property in [module.json](../reference/module.html)).
Target-specific dependencies can be used to depend on different implementations
of the functionality that a module needs on different target platforms, which
is especially useful when compiling for embedded hardware.

Note that now that [config info](/reference/config.html) can be defined by
target descriptions, and target descriptions inherit from other ones, the use
of `similarTo` should generally be avoided.

When compiling, CMake variables and preprocessor definitions are defined by
`yotta` for each thing in the similarTo list (and the name of the target
itself):

```
TARGET_LIKE_FOO
```

Where `FOO` is the name in the similarTo list, converted to uppercase, and with
any non-alphanumeric characters converted to underscores.


### <a href="#yotta-debug" name="yotta-debug">#</a> `yotta debug` Support
Targets can optionally provide a command that yotta will use to start a
debugger when the user runs `yotta debug`. They do this by providing a
`debug` script in target.json. This should be an array of commmand arguments,
and use $program for the name of the program that's being debugged, for example:

```json
  "scripts": {
      "debug": [
        "lldb", "$program"
      ]
  }
```

Debuggers that attach to embedded devices often need to run a debug server
program in the background before running the debugger itself. ARM mbed
compilation targets use the [`valinor`](http://github.com/ARMmbed/valinor)
program to achieve this (valinor also detects which debugger is installed on the
local system, and chooses the preferred one).

### <a href="#yotta-test" name="yotta-test">#</a> `yotta test` Support
To support the `yotta test` command, targets must provide a way of running
tests, to do this, implement `scripts.test` in target.json. For native
compilation targets, this can simply run the program in question, for a
cross-compilation target it should be a wrapper script that loads the program
onto the target device, runs it, prints the program's output to stdout, and
exits with the processes return code.

For example:

```json
  "scripts": {
      "test": [
        "mbed-test-wrapper", "-t", "K64F", "-i", 10, "$program"
      ]
  }
```


### <a href="#testing-targets" name="testing-targets">#</a> Testing targets
To test a target locally, without publishing it, you can use
`yotta link-target` to link it into an existing module, and use it for
compilation.

First run `yotta link-target` in the directory in which you're editing your
target:

```sh
cd path/to/my-target
yotta link-target
```

Then in the module that you want to compile, run
`yotta link-target <targetname>`:

```sh
cd ../path/to/my/module
yotta link-target my-target
```

You should also select your new target from the module directory before
attempting to build for it for the first time.

```sh
yotta target my-target
```

Now when you build, your new target description will be used. Note that
currently you need to remove the build directory after editing the target's
toolchain file, as CMake does not add dependency rules on the toolchain:

```
rm -Rf build/my-target
yotta build
```


### <a href="#publishing-targets" name="publishing-targets">#</a> Publishing Targets
Once you've written your target you can publish it:

```
# change into the target's direcory:
cd path/to/my/target

# tag a new version:
yotta version minor

# publish!
yotta publish
```

After publishing, whenever someone sets the target to your target with the
`yotta target <targetname>` command, your target description will be
automatically downloaded and used.

