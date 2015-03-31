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

### `description`
**type: String**

Brief description of what this target is for. This helps other people to find
your target.
Include a `readme.md` file with a longer description, and preferably a photo of
the target platform.

### `keywords`
**type: Array of String**

Keywords describe what this target is for, and help other people to find it.
For example, a target to build for a specific mbed board should be tagged with
`mbed-target:{mbedtargetname}` (where `{mbedtargetname}` should be replaced
with the mbed target name of the development board.

### `toolchain` *required*
**type: String (path relative to target root directory)**

Path to the target's CMake toolchain file.

### `scripts`
**type: hash of script-name to command**

Each command is an array of the separate command arguments.

The supported scripts are:

 * **debug**: this is the command that's run by `yotta debug`, it should
   probably open a debugger. `$program` will be expanded to the full path of
   the binary to be debugged.
 * **test**: this command is used by `yotta test` to run each test. `$program`
   will be expanded to the full path of the binary to be debugged. For
   cross-compiling targets, this command should load the binary on to the
   target device, and then print the program's output on standard out.

For example, the scripts for a native compilation target might look like:

```json
   "scripts": {
      "debug": ["lldb", "$program"],
      "test": ["$program"]
   }
```

### `debugServer` **deprecated: use scripts.debug instead**
**type: Array of String (command parts)**

Optional command to run a debug server.

### `debug` **deprecated: use scripts.debug instead**
**type: Array of String (command parts)**

Optional command to run when the `yotta debug` is invoked.

Use `$program` for the name of the program that's being debugged, for example:

```json
  "debug": [
    "gdb", "$program", "--eval", "target remote localhost:2331"
  ]
```

