---
layout: default
title: target.json
section: reference/ignore
---

# .yotta_ignore Reference

A `.yotta_ignore` file can be added to any module or target to make yotta
completely ignore any listed files. Listed files are ignored when
auto-generating build files, and when publishing to the registry (but note that
custom CMakeLists files may still refer to ignored files).


## Syntax

Glob-style syntax is supported, with one pattern per line in the ignore file.
Lines in the ignore file starting with `#` are comments and will not be parsed
by yotta.

Any file or directory that matches any pattern in the ignore file will be ignored.

Any files within an ignored directory will also be ignored.

 * `*` matches zero or more of any character, but does not match a directory separator
 * `?` matches any character exactly once, but does not match a directory separator
 * `[]` matches any character within `[]` exactly once

If a pattern starts with a `/` then it is an **absolute** pattern, and the whole
path relative to the root of the module must match.

If a pattern does not start with a `/` then it is a **relative** pattern, and
will match files and directories with any parent hierarchy.

Note that with the relative pattern `b/c`, and a directory hierarchy `a/b/c/d/e`,
the whole of the directory `c` (including any subdirectory `d`) will be ignored. 

### Examples

 * Ignore all files in `test/bar/`: `/test/bar/*`
 * Ignore all `.tar.gz` and `.tar.bz` files in the root directory: `/*.tar.[bg]z`
 * Ignore all `.swp` files everywhere: `*.swp`
 * Ignore all dotfiles files everywhere: `.*`


## Always-Ignored Files

Files matching some patterns will always be ignored by yotta, whether or not a
.yotta_ignore file is present. This list currently includes:

`/upload.tar.gz`
`/upload.tar.bz`
`/.git`
`/.hg`
`/.svn`
`/yotta_modules`
`/yotta_targets`
`/build`
`.DS_Store`
`.sw[ponml]`
`*~`
`._.*`
`.yotta.json`
