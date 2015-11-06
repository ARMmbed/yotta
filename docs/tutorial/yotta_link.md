---
layout: default
title: Using yotta link to fix bugs in dependencies
section: tutorial/yotta_link
---

## Using `yotta link` to Fix a Bug in a Dependency

It's possible, even in well-tested software, for issues to arise only when
modules are used in particular ways that were not anticipated by the authors.
Sometimes these can be hard to isolate, and its necessary to fix the bug while
working with a test application.

The `yotta link` command is designed to make it possible to investigate and fix
issues in the dependencies of your module or application. It allows you to
"link" a development version of the dependency where a problem is suspected
(obtained, for example from GitHub) into your test application.

#### <a name="update" href="#update">#</a> **Step 0:** Update To Latest Versions
Before embarking on debugging a problem, it's a good idea to update to the
latest version of your dependencies, in case the problem has already been fixed
by someone else.

You can use the [`yotta outdated`](!!!) command to see which of your
dependencies have newer versions available, and the [`yotta update`](!!!)
command to download updated versions.

Note that your module (or your dependencies) might have [version
specifications](!!!!) on dependencies that prevent updates from being
automatically downloaded. In this case you might have to first relax the
version specifications by editing your module.json file (or ask the author of
one of your dependencies to do the same): possibly requiring changes to your
module to accommodate breaking changes in the latest version of your
dependencies.

#### <a name="identify" href="#identify">#</a> **Step 1:** Identify The Module With a Problem
(identifying the module from a compilation error: use a fictitous? error in simplelog as an example / or a more complex mbed OS example?)

#### <a name="download" href="#download">#</a> **Step 2:** Download The Development Version 
(how to find the git repo of a module: registry URL on website page / look at
publisher email with `yotta owners ls`)

#### <a name="link-globally" href="#link-globally">#</a> **Step 3:** Link The Development Version Globally

#### <a name="link-in" href="#link-in">#</a> **Step 4:** Link Into Test Module(s)
(link into one or more test applications where the problem can be reproduced,
can be linked into applications or other modules)

#### <a name="debug" href="#debug">#</a> **Step 5:** Edit and Debug
(mention normal debug methods, yotta debug, editing code to add logging, etc.)

#### <a name="submit-fix" href="#submit-fix">#</a> **Step 6:** Submit Pull Request
(once a fix has been identified)

### <a name="link-target" href="#link-target">#</a> Using `yotta link-target` to link Target Descriptions


### <a name="dependency-handling" href="#dependency-handling">#</a> Dependency Handling With `yotta link`

(explain how dependencies may be loaded through the link, but that `yotta link`
will never act through the link, or modify a linked module)

