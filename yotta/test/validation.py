#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest

# validate, , validate various things, internal
from yotta.lib import validate

class TestValidation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_validateSourceDirNames(self):
        self.assertTrue(validate.sourceDirValidationError('Source', 'testcomponent'))
        self.assertTrue(validate.sourceDirValidationError('src', 'testcomponent'))
        self.assertTrue(validate.sourceDirValidationError('Src', 'testcomponent'))
        self.assertTrue(validate.sourceDirValidationError('Test', 'testcomponent'))
        self.assertTrue(validate.sourceDirValidationError('with space', 'testcomponent'))
        self.assertTrue(validate.sourceDirValidationError('with nonvalid!', 'testcomponent'))

    def test_validateSourceDirSuggestions(self):
        self.assertTrue('abcde' in validate.sourceDirValidationError('a b c!%^& d e', 'testcomponent'))
        self.assertTrue('source' in validate.sourceDirValidationError('Source', 'testcomponent'))
        self.assertTrue('source' in validate.sourceDirValidationError('src', 'testcomponent'))
        self.assertTrue('test' in validate.sourceDirValidationError('Test', 'testcomponent'))

    def test_componentNameCoerced(self):
        self.assertTrue('some-name' == validate.componentNameCoerced('Some Name'))
        self.assertTrue('some-name' == validate.componentNameCoerced('Some  Name'))
        self.assertTrue('moo-moo-moo' == validate.componentNameCoerced('MOO!!!!MOO-----Moo'))

    def test_looksLikeAnEmail(self):
        self.assertTrue(validate.looksLikeAnEmail('test@example.com'))
        self.assertTrue(validate.looksLikeAnEmail('test.testytest@test.com'))
        self.assertFalse(validate.looksLikeAnEmail('@.com'))
        self.assertFalse(validate.looksLikeAnEmail('moo.moo'))
        self.assertFalse(validate.looksLikeAnEmail('thingy'))
        self.assertFalse(validate.looksLikeAnEmail('thingy@thingy'))
        self.assertFalse(validate.looksLikeAnEmail(''))


if __name__ == '__main__':
    unittest.main()



