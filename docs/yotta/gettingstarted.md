---
layout: default
title: Getting Started
section: yotta/gettingstarted
---

# Introduction to yotta
Yotta is a tool that we're building at [mbed](https://mbed.org) to help ourselves and others build better software for C-family languages (that's C, C++ and Objective-C). It's a command line tool `yotta`, but also a culture of building software components that do one thing well, declare a clear interface, and can be re-used.

##Installation
Follow the installation instructions in the [readme](https://github.com/ARMmbed/yotta).

## Getting Started

To create and publish a minimal module, initialise with `yotta init`, edit your
source files in `source/`, then build with `yotta build` and publish using
`yotta publish`:

```sh
yotta init

echo 'void myModuleFoo(){
    printf("hello yotta!\n”);
}' > source/foo.c

yotta build

yotta publish
```

For more information on creating modules, and building executables, follow the [tutorial](/../tutorial/tutorial.html).
