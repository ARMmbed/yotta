---
layout: default
title: Getting Started
section: yotta/gettingstarted
---

# Getting Started

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

For more information on creating modules, and building executables, follow the [tutorial](/../tutorial/module.html).
