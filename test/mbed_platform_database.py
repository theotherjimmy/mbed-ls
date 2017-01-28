import unittest

from mbed_lstools.mbed_platform_database import MbedPlatformDatabase, manufacture_ids
from mbed_lstools.mbed_ls_utils import InvalidTargetIDPrefixException


class MbedPlatformDatabaseTestCase(unittest.TestCase):
    """ Tests the MbedPlatformDatabase Class
    """

    def setUp(self):
        self.database = MbedPlatformDatabase()

    def tearDown(self):
        self.database = None
    
    def test_add_get_remove(self):
        target_id_prefix = '0000'
        platform_name = 'TEST_PLATFORM0000'
        
        # Ensure the test platform isn't already present in the database
        self.assertEqual(self.database.get_platform_name(target_id_prefix), None)
        self.assertEqual(self.database.get_target_id_prefix(platform_name), None)
        
        # Add the test platform to the database
        self.database.add(target_id_prefix, platform_name)
        
        # Ensure the test platform was correctly added to the database
        self.assertEqual(self.database.get_platform_name(target_id_prefix), platform_name)
        self.assertEqual(self.database.get_target_id_prefix(platform_name), target_id_prefix)
        
        # Remove the test platform from the database
        self.database.remove(target_id_prefix)
        
        # Ensure the test platform was removed from the database
        self.assertEqual(self.database.get_platform_name(target_id_prefix), None)
        self.assertEqual(self.database.get_target_id_prefix(platform_name), None)
    
    def test_default_ids_present(self):
        self.assertTrue(len(manufacture_ids) > 0)
        for target_id_prefix in manufacture_ids:
            self.assertEqual(self.database.get_platform_name(target_id_prefix), manufacture_ids[target_id_prefix])
    
    def invalid_target_id_helper(self, target_id_prefix, platform_name):
        result = None
        try:
            self.database.add(target_id_prefix, platform_name)
        except InvalidTargetIDPrefixException as e:
            result = e
        return result
    
    def test_add_invalid_target_id_bad_character(self):
        bad_add_result = self.invalid_target_id_helper('ZA02', 'TEST_PLATFORM')
        self.assertNotEqual(bad_add_result, None, 'The character "Z" is invalid and should have raised an exception')
    
    def test_add_invalid_target_id_short_length(self):
        bad_add_result = self.invalid_target_id_helper('AB7', 'TEST_PLATFORM')
        self.assertNotEqual(bad_add_result, None, 'The target ID prefix is too short and should have raised an exception')
    
    def test_add_invalid_target_id_long_length(self):
        bad_add_result = self.invalid_target_id_helper('45B35', 'TEST_PLATFORM')
        self.assertNotEqual(bad_add_result, None, 'The target ID prefix is too long and should have raised an exception')


if __name__ == '__main__':
    unittest.main()
