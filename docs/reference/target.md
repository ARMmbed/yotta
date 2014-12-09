---
layout: default
title: target.json
section: yotta/target
---

# target.json Reference
The `target.json` file is used to describe yotta targets. It defines where to
find the CMake toolchain used to control compilation, what this target should
be considered as similar to when working out dependencies.

### Example File
```json
{
  "name": "frdm-k64f-gcc",
  "version": "0.0.7",
  "similarTo": [
    "frdm-k64f",
    "k64f",
    "ksdk-mcu",
    "mk64fn1m0vmd12",
    "mk64fn1m0",
    "mk64fn",
    "freescale",
    "cortex-m4",
    "armv7-m",
    "arm",
    "gcc",
    "*"
  ],
  "toolchain": "CMake/toolchain.cmake",
  "debugServer": [
    "JLinkGDBServer", "-if", "SWD", "-device", "MK64FN1M0xxx12"
  ],
  "debug": [
    "arm-none-eabi-gdb", "$program", "--eval", "target remote localhost:2331"
  ]
}
```

## Properties

### `name` *required*
**type: String**

The unique name of the target. Globally unique. As the target also defines
which compiler is used to build, target names should normally explicitly state
which compiler they use (e.g. `some-target-gcc`, `some-target-armcc`).

Names can use only lowercase letters, numbers, and hyphens, but must start with
a letter. (This reduces problems with case insensitive filesystems, and
confusingly similar names.)

### `version` *required*
**type: String (conforming to the [semver](http://semver.org) specification)**

`yotta` uses Semantic Versions for targets and modules. See the [module.json
reference](../reference/module.html#version) for details.


### `similarTo` *required*
**type: Array of String**

An array of target identifiers that this target is similar to. This list is
used when resolving [target-specific dependencies](../reference/module.html#targetDependencies).

When calculating the dependencies to install, `yotta` uses the first section
from `targetDependencies` that matches one of the identifiers in this list.

The identifiers are arbitrary strings, and do not need to be the names of other
targets.


### `toolchain` *required*
**type: String (path relative to target root directory)**

Path to the target's CMake toolchain file.


### `debugServer`
**type: Array of String (command parts)**

Optional command to run a debug server.

### `debug`
**type: Array of String (command parts)**

Optional command to run when the `yotta debug` is invoked.

Use `$program` for the name of the program that's being debugged, for example:

```json
  "debug": [
    "gdb", "$program", "--eval", "target remote localhost:2331"
  ]
```

