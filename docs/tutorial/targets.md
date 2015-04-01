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
 * What other targets this target should be considered "similar to". This
   information is used to resolve dependencies.

And optionally provides information on:

 * how to run the debugger (`yotta debug` support)

Each yotta target contains a [target.json](../reference/target.html) file, which
describes where to find this other information.

### Selecting the Target

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


## Writing Targets

<a name="toolchainfile"></a>
### The Toolchain File
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

<a name="similarto"></a>
### The similarTo List and Target Specific Dependencies
The most important part of the target description is the list of targets that
the target should be considered "similar to". This is defined by target.json:

```json
  "similarTo": <list of strings>,
```

This list is used to choose which dependencies to pick when a module has
target-specific dependencies (defined by the `targetDependencies` property in
[module.json](../reference/module.html)). Target-specific dependencies can be
used to depend on different implementations of the functionality that a module
needs on different target platforms, which is especially useful when compiling
for embedded hardware.

When you create a new target that's based on an existing target, you should
copy its similarTo list. 

You might do this, for example, if you've created a new product based on an
existing microcontroller development board. Most of the peripherals and
functionality is the same, so you'll want to depend on the same implementations
that work best for the board your device is based on.

When compiling, CMake variables and preprocessor definitions are defined by
`yotta` for each thing in the similarTo list (and the name of the target
itself):

```
TARGET_LIKE_FOO
```

Where `FOO` is the name in the similarTo list, converted to uppercase, and with
any non-alphanumeric characters converted to underscores.


### `yotta debug` Support
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

### `yotta test` Support
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


### Testing targets
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

Now when you build, your new target description will be used. Note that
currently you need to remove the build directory after editing the target's
toolchain file, as CMake does not add dependency rules on the toolchain:

```
rm -Rf build/my-target
yotta build
```


### Publishing Targets
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

