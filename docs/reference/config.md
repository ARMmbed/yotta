---
layout: default
title: yotta Configuration System Reference
section: reference/config
---

# Configuration System Reference

**NOTE: The configuration system is currently experimental. Some of the
behaviour described below may change in backwards-icompatible ways with minor
updates to yotta.**

yotta provides a flexible configuration system that can be used to control how
modules are built based on information provided by [target
descriptions](/tutorial/targets.html), optionally extended by a `config.json`
file in the application.

This configuration information can be used to control a module's dependencies,
and is also made available to code.

<a name="defining"></a>
## Defining Configuration Data
Configuration data is defined in two places: [target descriptions](/tutorial/targets.html), and
[executable applications](/tutorial/tutorial.html#Creating%20an%20Executable).


### Target Config Data
The config data defined by targets can be used to make software modules compile
across a wide range of different target hardware. For example, it might
describe things like the frequency of a
[UART](https://en.wikipedia.org/wiki/Universal_asynchronous_receiver/transmitter)
serial bus that the target hardware might have for communication.

Software that uses this hardware can then run on different targets, choosing
the correct frequency to use for the UART communication by reading it from the
configuration data.

#### Config Data in target.json
To define config data in a target's target.json file, use the `"config":`
property, for example:

```json
{
    "name":"mytarget",
    "version":"1.2.3",
    "license":"Apache-2",
    "config":{
        "devices":{
            "foobar":"value",
            "volume":11
        }
    }
}
```

#### Overriding Config Data in Derived Targets
If a target [inherits](/tutorial/targets.html#inheriting) from a more generic
target, then the config data in the more-derived target overrides data
inherited from the base target.

For example, given a base target with config data:

```json
{
    "a":{
        "foo": true,
        "bar": 123
    }
}
```

And a derived target with config data:

```json
{
    "a":{
        "bar": 456
    },
    "b":{
        "baz": "<whatever>"
    }
}
```

The merged config data (which you can display with the [`yotta
config`](/reference/commands.html#yotta-config) subcommand), would be:

```json
{
    "a":{
        "foo": true,
        "bar": 456
    },
    "b":{
        "baz": "<whatever>"
    }
}
```

### Application Config Data
An executable application may define additional config data to that provided by
the selected target. To do this, the application should include a file called
`config.json` alongside its `module.json` file.

The application's configuration data takes highest precedence, so can be used
to override any values defined by the target data. This is useful for defining
application-specific configuration, and when developing an application for
one-off target hardware which is derived from a supported platform (it can
eliminate the need to define your own target description just for one
application).

If you find yourself copying & pasting `config.json` data between many
applications, consider if deriving and publishing [your own
target](/tutorial/targets.html) would be preferable.


### Config Data Syntax
The yotta config system accepts almost any JSON data, apart from Array objects.
Array objects are not supported due to the ambiguity of merging inherited array
objects.


<a name="using"></a>
## Using Configuration Data
Modules can use the configuration data that has been defined to change their
behaviour. In general it is best to minimise the amount of configuration that
your module requires to the absolute minimum possible. This makes it easier
for people to re-use your module in different applications, and to use it on
different target hardware, without having to define a lot of configuration.

By convention, modules should only read configuration data from their own
namespace in the config data, for example a module called `simplelog` might
read a logging level set in the `simplelog` section of the config data:

```json
{
    "mbed":{
       ...
    },
    "simplelog":{
        "level":1
    },
    ...
}
```

It would be possible for any other module (say a `betterlog` logging module),
to read this data and use it to configure itself, but doing so could cause
things to break if `simplelog` directs its users to do something different with
the config data than what `betterlog` expects.

**NOTE: support for modules to define schemas on parts of the config data is
currently being considered. This would formalise the constraints modules have
on what configuration may be defined.**

### Controlling Dependencies

Config data can be used in the [targetDependencies
section](/reference/module.html#targetDependencies) of `module.json` files.

If a path in the config data matches the values defined on the left-hand side
of the targetDependencies hash, then the dependencies declared in the object on
the right-hand side will be used.

For example, given the config data:

```json
  {
     "a": {
        "enable": true
     },
     "b": {
        "foobar": 123
     },
     "c": {
        "baz": {
            
        }
     },
     "d": {
        "etc": "astring"
     },
     "e": {
        "supported": null,
        "also-falsey": false
     }
  }
```

And the targetDependencies:

```json
  "targetDependencies": {
     "a.enable": {
       "module-1": "^1.2.3"
     },
     "b.foobar": {
       "module-2": "^1.2.3"
     },
     "c.baz": {
       "module-3": "^1.2.3"
     },
     "d.etc": {
       "module-4": "^1.2.3"
     },
     "e.supported": {
       "module-5": "^1.2.3"
     }
  }
```

Then modules 1, 2, 3 and 4 will be included as dependencies, but `module-5` will not.

### Using Configuration In Code

The config data is made available as preprocessor definitions, so that it can
be tested at compile-time.

For the config data in the above dependencies example, the following
definitions will be produced:

```C
#define YOTTA_CFG
#define YOTTA_CFG_A
#define YOTTA_CFG_A_ENABLE 1
#define YOTTA_CFG_B
#define YOTTA_CFG_B_FOOBAR 123
#define YOTTA_CFG_C
#define YOTTA_CFG_C_BAZ
#define YOTTA_CFG_D
#define YOTTA_CFG_D_ETC astring
#define YOTTA_CFG_E
#define YOTTA_CFG_E_SUPPORTED NULL
#define YOTTA_CFG_E_ALSO_FALSEY 0
```

Note that string values are not quoted. If you want a quoted string,
either embed escaped quotes (`\"`) in the string value, or use the preprocessor
[stringification
trick](https://gcc.gnu.org/onlinedocs/cpp/Stringification.html).

JSON boolean values are converted to 1 or 0, and `null` values are converted to `NULL`.

These definitions are defined through a pre-include file called
`yotta_config.h` which is generated in the root of the build directory.

### Using Configuration in CMakeLists

The config data is also made accessible to any custom CMakeLists.txt that have
been written to control the build of a module. The CMake definitions are nearly
the same as the C preprocessor definitions, except that empty definitions, and
`null` definitions are converted to `set(YOTTA_CFG_<property> "")`, and no
conversion is performed for boolean values.


