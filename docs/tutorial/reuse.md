---
layout: default
title: Code Reuse with Yotta
section: tutorial/reuse
---

# Writing Re-usable Software
Writing re-usable software is means much more than just bundling your software as a `yotta` module. It's a culture (or cult, if you prefer ;) with a set of rules that make software more re-usable. In C/C++ software development these rules are rarely followed – and our favourite languages even ship with standard libraries that break them – but to `yotta` they are essential.

 1. **All publicly exposed names must be prefixed or name-spaced.**

    This is designed to reduce the likelihood name collisions when symbols with
    the same name are defined by different modules.

 2. **Avoid global state where possible.**

    It should be possible for modules to be re-used multiple times within the
    same program, if a module has no global state then this will be possible.
    If it does (which is sometimes unavoidable), then you need to design
    specifically for multiple users.

 3. **Public header files should not change their visible behaviour based on #-defines.**

    Header files should always define the same things, wherever they are
    included from (and thus whatever within reason is #defined when they are
    included). As much as possible they should also define the same things
    when used on different targets. This prevents problems caused by the order
    of #include statements, which can change due to changes in dependencies.

We don't care about the way you indent code or the way you name your private variables, `yotta` is not that sort of religion, but we do care about the things that matter when someone else wants to use your code.

