#!/usr/bin/env python

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


if __name__ == '__main__':
    unittest.main()



