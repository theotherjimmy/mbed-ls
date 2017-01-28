import unittest
import re
import logging
import sys
import os
import shutil
from sets import Set
from copy import copy
from string import Template

from mbed_lstools.mbed_platform_database import MbedPlatformDatabase
from mbed_lstools.providers.mbed_provider import MbedProvider
from mbed_lstools.mbed_lister import MbedLister

mounted_consistent_target_0 = '12340000000000000000'
mounted_consistent_target_1 = '12340000000000000001'
mounted_inconsistent_target_usb = '77770000000000000002'
mounted_inconsistent_target_htm = '12340000000000000002'
unmounted_target = '55550000000000000001'

mbed_htm_template = Template("""<!doctype html>
<!-- mbed Platform Website and Authentication Shortcut -->
<html>
<head>
<meta charset="utf-8">
<title>mbed Website Shortcut</title>
</head>
<body>
<script>
window.location.replace("https://mbed.org/device/?code=${target_id}?version=0243?target_id=00000000000000000000000000000000");
</script>
</body>
</html>
""")

class MbedProviderDummy(MbedProvider):
    def __init__(self, mbeds):
        self.mbeds = mbeds        
    
    def list_mbeds(self):            
        return self.mbeds

class MbedListerTestCase(unittest.TestCase):
    """ Tests the MbedLister Class
    """
    
    TEST_PARENT_DIR = '.test_mount_points'
    
    @classmethod
    def setUpClass(self):
        def form_target(target_id_usb_id, target_id_mbed_htm=None):
            html_target_id = target_id_mbed_htm if not None else target_id_usb_id
            return {
                "target_id": target_id_usb_id,
                "target_id_usb_id": target_id_usb_id,
                "_mbed_htm_contents": mbed_htm_template.substitute(target_id=html_target_id)
            }
        
        self.test_mbeds = {}
        
        self.test_mbeds[mounted_consistent_target_0] = form_target(mounted_consistent_target_0)
        self.test_mbeds[mounted_consistent_target_1] = form_target(mounted_consistent_target_1)
        self.test_mbeds[mounted_inconsistent_target_usb] = form_target(mounted_inconsistent_target_usb, target_id_mbed_htm=mounted_inconsistent_target_htm)
        self.test_mbeds[unmounted_target] = {
            "target_id": unmounted_target,
            "target_id_usb_id": unmounted_target
        }
                
        if os.path.exists(self.TEST_PARENT_DIR):
            shutil.rmtree(self.TEST_PARENT_DIR)
        os.mkdir(self.TEST_PARENT_DIR)
        
        for target_id in self.test_mbeds:
            target = self.test_mbeds[target_id]
            if '_mbed_htm_contents' in target and target['_mbed_htm_contents']:
                test_mount_point = os.path.join(self.TEST_PARENT_DIR, 'mount_point_%s' % (target_id))
                os.mkdir(test_mount_point)
                with open(os.path.join(test_mount_point, 'mbed.htm'), 'w') as f:
                    f.write(target['_mbed_htm_contents'])
                target['mount_point'] = test_mount_point
    
    @classmethod
    def tearDownClass(self):
        if os.path.exists(self.TEST_PARENT_DIR):
            shutil.rmtree(self.TEST_PARENT_DIR)

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.stream_handler)
        self.database = MbedPlatformDatabase()
        self.provider = MbedProviderDummy(self.test_mbeds)
        self.lister = MbedLister(self.database, self.provider)

    def tearDown(self):
        self.database = None
        self.provider = None
        self.lister = None
        self.logger.removeHandler(self.stream_handler)
    
    def test_tid_filters(self):
        target_id_filters = [
            [],
            [mounted_consistent_target_0],
            ['88880000000000000001'],
            [mounted_consistent_target_0, '88880000000000000001'],
            [mounted_consistent_target_0, mounted_consistent_target_1],
            [mounted_consistent_target_0[:4] + '*'],
            ['8888*']
        ]
        
        outcomes =  [
            [mounted_consistent_target_0, mounted_consistent_target_1, mounted_inconsistent_target_htm],
            [mounted_consistent_target_0],
            [],
            [mounted_consistent_target_0],
            [mounted_consistent_target_0, mounted_consistent_target_1],
            [mounted_consistent_target_0, mounted_consistent_target_1, mounted_inconsistent_target_htm],
            []
        ]
        
        for index, target_id_filter in enumerate(target_id_filters):
            result = self.lister.list_mbeds_ext(target_id_filters=target_id_filter)
            expected_target_ids = Set(outcomes[index])
            actual_target_ids = Set(result.keys())
            self.assertEqual(expected_target_ids, actual_target_ids)

    def test_list_fs_pre(self):
        result = self.lister.list_mbeds_ext(file_system_behavior=MbedProvider.FS_PRE_TARGET_ID_CHECK)
        expected_target_ids = Set([mounted_consistent_target_0, mounted_consistent_target_1, mounted_inconsistent_target_htm])
        actual_target_ids = Set(result.keys())
        self.assertEqual(expected_target_ids, actual_target_ids)
    
    def test_list_fs_post(self):
        target_id_filter = [mounted_consistent_target_0[:4] + '*']
        result = self.lister.list_mbeds_ext(file_system_behavior=MbedProvider.FS_POST_TARGET_ID_CHECK, target_id_filters=target_id_filter)
        expected_target_ids = Set([mounted_consistent_target_0, mounted_consistent_target_1])
        actual_target_ids = Set(result.keys())
        self.assertEqual(expected_target_ids, actual_target_ids)
    
    def test_list_fs_disabled(self):
        result = self.lister.list_mbeds_ext(file_system_behavior=MbedProvider.FS_DISABLED)
        expected_target_ids = Set([mounted_consistent_target_0, mounted_consistent_target_1, mounted_inconsistent_target_usb, unmounted_target])
        actual_target_ids = Set(result.keys())
        self.assertEqual(expected_target_ids, actual_target_ids)

if __name__ == '__main__':
    unittest.main()
