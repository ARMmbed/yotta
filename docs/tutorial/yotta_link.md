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
"link" in a development version of the dependency where a problem is suspected
(obtained, for example from GitHub).

#### Step 1: Identify The Module With a Problem
(identifying the module from a compilation error: use a fictitous? error in simplelog as an example / or a more complex mbed OS example?)

#### Step 2: Download The Development Version 
(how to find the git repo of a module: registry URL on website page / look at
publisher email with `yotta owners ls`)

#### Step 3: Link The Development Version Globally

#### Step 4: Link Into Test Module(s)
(link into one or more test applications where the problem can be reproduced,
can be linked into applications or other modules)

#### Step 5: Edit and Debug
(mention normal debug methods, yotta debug, editing code to add logging, etc.)

#### Step 6: Submit Pull Request
(once a fix has been identified)

### Using `yotta link-target` to link Target Descriptions


### Dependency Handling With `yotta link`

(explain how dependencies may be loaded through the link, but that `yotta link`
will never act through the link, or modify a linked module)

