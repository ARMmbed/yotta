---
layout: default
title: Tutorial
section: tutorial/building
---

# Building Existing Modules
This tutorial will guide you through the process of building software that uses
yotta. You might also want to check out the tutorial to writing your [own
software](../tutorial/tutorial.html) with yotta, or the [build system reference](/reference/buildsystem.html).


## Check your installation
First check that yotta is correctly installed. You should be able to open a
terminal window and run

```
yotta --version
```

without any errors. If this doesn't
work, check the [installation guide](../).


## Download the Module
First download the module that you want to build. For example, to download the
helloyotta example program, either clone or download the source tarball from
its [github page](https://github.com/armmbed/helloyotta).

All software that builds with yotta has a `module.json` file that describes it:

```sh
> cd path/to/downloaded/helloyotta
> ls -l
-rw-r--r--   1 jamcro01  staff   8.9K  9 Dec 11:59 LICENSE
drwxr-xr-x   2 jamcro01  staff    68B 18 Sep 17:07 helloyotta
-rw-r--r--   1 jamcro01  staff   621B  9 Dec 12:02 module.json
-rw-r--r--   1 jamcro01  staff   220B  9 Dec 11:53 readme.md
drwxr-xr-x   3 jamcro01  staff   102B 18 Sep 18:37 source
```

## Build!

To build the module, all we need to do is run `yotta build`. yotta will read
the module.json file, which describes what this module depends on, download its
dependencies into a directory called `yotta_modules`, then generate build files
and build.

yotta has a registry of publicly available modules. In the future it will be
possible to search this registry to find open-source components to re-use, or,
to build non-open-source software you can also depend on modules from private
Github repositories, or from authenticated hg and git repositories, for more
information about specifying the source of dependencies see the [module.json
reference](../reference/module.html#dependencies).


```sh
> cd path/to/downloaded/helloyotta
> yotta build
info: get versions for x86-osx-native
info: get versions for simplelog
info: download simplelog
info: generate for target: x86-osx-native 0.0.3 at /Volumes/Work/synced/Dev/IoT/helloyotta/yotta_targets/x86-osx-native
...
[100%] Built target helloyotta
```

The built executable will be created at
`./build/<targetname>/source/helloyotta`, where <targetname> is the yotta
compilation target that was set. For example, the default on OS X is to build
natively using the x86-osx-native target:

```
> ./build/x86-osx-native/source/helloyotta 
[info] Hello yotta!
```

