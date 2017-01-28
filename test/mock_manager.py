import unittest
import json
import os
from mbed_lstools.mock_manager import MockManager

class MockManagerTestCase(unittest.TestCase):
    """ Tests the MockManager Class
    """
    
    test_mock_file = '.test_mock_file'

    def setUp(self):
        pass
        
    def tearDown(self):
        self.manager = None
        
        if os.path.exists(self.test_mock_file):
            os.remove(self.test_mock_file)
        
        lock_file = '%s.lockfile' % self.test_mock_file
        if os.path.exists(lock_file):
            os.remove(lock_file)
    
    def createManager(self):
        self.manager = MockManager(self.test_mock_file)
    
    def verify_valid_platforms(self, expected_platforms):
        """Helper function to verify the mocked platforms are consistent in the
        mock file as well as the MockManager's data structure
        """
        updated_platforms = self.manager.get_platforms()
        self.assertEqual(updated_platforms, expected_platforms)
        
        mock_file_contents = None
        with open(self.test_mock_file, 'r') as mock_file:
            mock_file_contents = json.load(mock_file)
        
        self.assertEqual(mock_file_contents, expected_platforms)
    
    def test_existing_mock_file(self):
        mock_file_contents = {
            '0000': 'MY_TEST_TARGET'
        }
        
        with open(self.test_mock_file, 'w') as mock_file:
            mock_file.write(json.dumps(mock_file_contents, indent=4))
        
        self.createManager()
        
        platforms = self.manager.get_platforms()
        
        self.assertEqual(platforms.keys(), mock_file_contents.keys())
        
        for target_id_prefix in platforms:
            self.assertTrue(target_id_prefix in mock_file_contents)
            self.assertEqual(platforms[target_id_prefix], mock_file_contents[target_id_prefix])
    
    def test_add_remove_platform(self):
        self.createManager()
        self.assertEqual(self.manager.get_platforms(), {})
        
        self.manager.add_platform('0000', 'MY_TEST_TARGET')
        self.verify_valid_platforms({
            '0000': 'MY_TEST_TARGET'
        })
        
        self.manager.add_platform('EEEE', 'MY_TEST_TARGET_2')
        self.verify_valid_platforms({
            '0000': 'MY_TEST_TARGET',
            'EEEE': 'MY_TEST_TARGET_2'
        })
        
        self.manager.remove_platform('0000')
        self.verify_valid_platforms({
            'EEEE': 'MY_TEST_TARGET_2'
        })
        
        self.manager.remove_platform('EEEE')
        self.verify_valid_platforms({})


if __name__ == '__main__':
    unittest.main()
