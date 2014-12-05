---
layout: default
title: Code Reuse with Yotta
section: tutorial/reuse
---

# Writing Re-usable Software
Writing re-usable software is means much more than just bundling your software as a yotta module. It's a culture (or cult, if you prefer ;) with a set of rules that make software more re-usable. In C/C++ software development these rules are rarely followed – and our favourite languages even ship with standard libraries that break them – but to yotta they are essential.

 1. All publicly exposed names must be prefixed or name-spaced.
 2. Avoid global state where possible.
 4. Public header files must not change their behaviour based on #-defines

We don't care about the way you indent code or the way you name your private variables, yotta is not that sort of religion, but we do care about the things that matter when someone else wants to use your code.
