---
layout: default
title: SPDX License Expressions
section: reference/licenses
---

# SPDX License Expressions

yotta module and target description files use [SPDX](http://spdx.org) License
Expression syntax to describe the licenses that apply to a module or target.

The full SPDX specification (currently version 2.0) is [available
here](http://spdx.org/sites/spdx/files/SPDX-2.0.pdf), but for ease of reference
the portion of the document referring to license expressions is included below.
It is a SPDX license-expression that should be used in the `license` fields
module.json and target.json files.


## Simple License Expressions

A simple **`<license-expression>`** is composed one of the following:

 * An **SPDX License List Short Form Identifier**. For example: GPL-2.0
 * An **SPDX License List Short Form Identifier** with a unary "+" operator
   suffix to represent the current
version of the license or any later version. For example: GPL-2.0+
 * A SPDX user defined license reference:
   `["DocumentRef-"1*(idstring)":"]"LicenseRef- "1*(idstring)` Some examples:

        LicenseRef-23
        LicenseRef-MIT-Style-1
        DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2


## Composite License Expressions
More expressive composite license expressions can be constructed using **"OR"**,
**"AND"**, and **"WITH"** operators similar to constructing mathematical expressions
using arithmetic operators. For the tag/value format, any license expression
that consists of more than one license identifier and/or LicenseRef, should be
encapsulated by parentheses: **"( )"**. This has been specified to facilitate
expression parsing. Nested parentheses can also be used to specify an order of
precedence which is discussed in more detail in subsection (4).


1.  **Disjunctive "OR" Operator**

    If presented with a choice between two or more licenses, use the
    disjunctive binary **"OR"** operator to construct a new lincense
    expression, where both the left and right operands are valid license
    expression values.

    For example, when given a choice between the LGPL-2.1 or MIT licenses, a
    valid expression would be:

          (LGPL-2.1 OR MIT)

    An example representing a choice between three different licenses would be:

          (LGPL-2.1 OR MIT OR BSD-3-Clause)

2.  **Conjunctive "AND" Operator**

    If required to simultaneously comply with two or more licenses, use the
    conjunctive binary **"AND"** operator to construct a new license expression ,
    where both the left and right operands are a valid license expression
    values.

    For example, when one is required to comply with both the LGPL-2.1 or MIT
    licenses, a valid expression would be:

          (LGPL-2.1 AND MIT)

    An example where all three different licenses apply would be:

          (LGPL-2.1 AND MIT AND BSD-2-Clause)


3. **Exception "WITH" Operator**

    Sometimes a set of license terms apply except under special circumstances.
    In this case, use the binary "WITH" operator to construct a new license
    expression to represent the special exception situation. A valid
    **`<license-expression>`** is where the left operand is a
    **`<simple-expression>`** value and the right operand is a
    **`<license-exception-id>`** that represents the special exception terms.
    
    For example, when the Bison exception is to be applied to GPL-2.0+, the
    expression would be:

          (GPL-2.0+ WITH Bison-exception-2.2)

    The current set of valid exceptions can be found in Appendix I, section 2.
    For the most up to date set of exceptions please see spdx.org/licenses. If
    the applicable exception is not found on the SPDX License Exception List,
    then use a single **`<license-ref>`** to represent the entire license terms
    (including the exception).

4. **Order of Precedence and Parentheses**

    The order of application of the operators in an expression matters (similar
    to mathematical operators). The default operator order of precedence of a
    **`<license-expression>`** is:
     1. **+**
     2. **WITH**
     3. **AND**
     4. **OR**

    where a lower order operator is applied before a higher order operator.

    For example, the following expression: `LGPL-2.1 OR BSD-3-Clause AND MIT`
    represents a license choice between either `LGPL-2.1` and the expression
    `BSD-3-Clause AND MIT` because the `AND` operator takes precedence over (is
    applied before) the `OR` operator.

    When required to express an order of precedence that is different from the
    default order a **`<license-expression>`** can be encapsulated in pairs of
    parentheses: **( )**, to indicate that the operators found inside the
    parentheses takes precedence over operators outside. This is also similar
    to the use of parentheses in an algebraic expression e.g., (5+7)/2.

    For instance, the following expression: `(MIT AND (LGPL-2.1+ OR BSD-3-Clause))`
    states the OR operator should be applied before the AND operator. That is,
    one should first select between the LGPL-2.1+ or the BSD-3-Clause license
    before applying the MIT license.


## Examples

A yotta module which is licensed entirely and only under Apache-2.0 would use
this in its module.json file:

```json
{
  "license": "Apache-2.0"
}
```

Or a module which contains both some code licensed under BSD, and other code
licensed under Apache-2.0 would use:

```json
{
  "license": "(Apache-2.0 AND BSD)"
}
```

And a module which may be used at the user's choice under either a custom
license in the file LICENSE.txt, or under Apache-2.0, would use:

```json
{
  "license": "(LicenseRef-LICENSE.txt OR Apache-2.0)"
}
```

If you have any questions about how to correctly describe the licenses that
apply to your module, please open an issue [on
Github](https://github.com/armmbed/yotta/issues).


**Note: some content on this page Copyright © 2010-2015 Linux Foundation and its Contributors.  Licensed under the Creative Commons Attribution License 3.0 Unported. All other rights are expressly reserved. [Original source](http://spdx.org/sites/spdx/files/SPDX-2.0.pdf)**
